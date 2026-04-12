import base64
import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Checkup, DeviceSyncState, OfflineActionLog, Patient, Symptom
from app.schemas import BluetoothImportRequest, OfflineSyncBatchRequest
from app.services.alert_service import acknowledge_alert, trigger_alert
from app.services.risk_model import calculate_risk
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/sync", tags=["sync"])


def _parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)


def _upsert_sync_state(db: Session, device_id: str, ts: datetime) -> None:
    state = db.query(DeviceSyncState).filter(DeviceSyncState.device_id == device_id).first()
    if not state:
        state = DeviceSyncState(device_id=device_id, last_sync_at=ts)
        db.add(state)
    else:
        state.last_sync_at = ts
    db.commit()


@router.post("/batch")
def sync_batch(payload: OfflineSyncBatchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        actions = sorted(payload.queued_actions, key=lambda a: a.local_timestamp)
        processed = 0
        failed = 0
        id_mapping: dict[str, str] = {}
        errors: list[dict] = []

        for action in actions:
            try:
                existing = (
                    db.query(OfflineActionLog)
                    .filter(OfflineActionLog.device_id == payload.device_id, OfflineActionLog.local_id == action.local_id)
                    .first()
                )
                if existing:
                    continue

                local_ts = action.local_timestamp.replace(tzinfo=None)
                if action.action_type == "symptom_report":
                    patient_id = int(action.payload.get("patient_id"))
                    patient = db.query(Patient).filter(Patient.id == patient_id).first()
                    if not patient:
                        raise ValueError("Patient not found")

                    symptoms = action.payload.get("symptoms", [])
                    risk = calculate_risk(
                        symptoms=symptoms,
                        bp_systolic=int(action.payload.get("bp_systolic", 0)),
                        bp_diastolic=int(action.payload.get("bp_diastolic", 0)),
                        age=int(action.payload.get("age", patient.age)),
                        pregnancy_week=int(action.payload.get("pregnancy_week", patient.pregnancy_week)),
                        days_since_last_checkup=int(action.payload.get("days_since_last_checkup", 0)),
                        previous_complications=bool(action.payload.get("previous_complications", False)),
                    )

                    conflict = (
                        db.query(Symptom)
                        .filter(
                            Symptom.patient_id == patient_id,
                            Symptom.timestamp >= local_ts.replace(second=0, microsecond=0),
                        )
                        .order_by(Symptom.timestamp.desc())
                        .first()
                    )
                    if conflict and abs((conflict.timestamp - local_ts).total_seconds()) <= 300:
                        if risk["score"] > conflict.risk_score:
                            conflict.symptoms_list = symptoms
                            conflict.risk_score = risk["score"]
                            conflict.risk_level = risk["level"]
                            conflict.primary_reason = risk["primary_reason"]
                            conflict.timestamp = local_ts
                            db.commit()
                            server_id = conflict.id
                        else:
                            server_id = conflict.id
                    else:
                        row = Symptom(
                            patient_id=patient_id,
                            symptoms_list=symptoms,
                            input_type="offline_sync",
                            transcription=action.payload.get("transcription"),
                            risk_score=risk["score"],
                            risk_level=risk["level"],
                            primary_reason=risk["primary_reason"],
                            timestamp=local_ts,
                        )
                        db.add(row)
                        db.commit()
                        db.refresh(row)
                        server_id = row.id

                    if risk["level"] == "HIGH":
                        trigger_alert(
                            db=db,
                            background_tasks=background_tasks,
                            patient_id=patient.id,
                            asha_id=patient.asha_id,
                            patient_name=patient.name,
                            risk_score=risk["score"],
                            reason=risk["primary_reason"],
                            village=patient.village,
                            district=patient.district,
                        )

                elif action.action_type == "checkup_record":
                    row = Checkup(
                        patient_id=int(action.payload["patient_id"]),
                        asha_id=int(action.payload["asha_id"]),
                        bp_systolic=int(action.payload.get("bp_systolic", 0)),
                        bp_diastolic=int(action.payload.get("bp_diastolic", 0)),
                        weight_kg=int(action.payload.get("weight_kg", 0)),
                        notes=action.payload.get("notes"),
                        created_at=local_ts,
                    )
                    db.add(row)
                    db.commit()
                    db.refresh(row)
                    server_id = row.id

                elif action.action_type == "alert_acknowledge":
                    alert_id = int(action.payload["alert_id"])
                    alert = db.query(Alert).filter(Alert.id == alert_id).first()
                    if not alert:
                        raise ValueError("Alert not found")
                    alert.acknowledged = True
                    alert.acknowledged_at = local_ts
                    db.commit()
                    acknowledge_alert(db, alert_id)
                    server_id = alert.id
                else:
                    raise ValueError("Unsupported action_type")

                log_row = OfflineActionLog(
                    device_id=payload.device_id,
                    local_id=action.local_id,
                    action_type=action.action_type,
                    server_id=str(server_id),
                    local_timestamp=local_ts,
                )
                db.add(log_row)
                db.commit()

                id_mapping[action.local_id] = str(server_id)
                processed += 1
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                failed += 1
                errors.append({"local_id": action.local_id, "error": str(exc)})

        if actions:
            _upsert_sync_state(db, payload.device_id, actions[-1].local_timestamp.replace(tzinfo=None))

        return success_response(
            {
                "processed": processed,
                "failed": failed,
                "id_mapping": id_mapping,
                "errors": errors,
            }
        )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return error_response(f"Batch sync failed: {exc}", 400)


@router.get("/status/{device_id}")
def sync_status(device_id: str, db: Session = Depends(get_db)):
    row = db.query(DeviceSyncState).filter(DeviceSyncState.device_id == device_id).first()
    return success_response({"device_id": device_id, "last_sync_timestamp": row.last_sync_at.isoformat() if row else None})


@router.post("/bluetooth-export/{asha_id}")
def bluetooth_export(asha_id: int, db: Session = Depends(get_db)):
    try:
        patients = db.query(Patient).filter(Patient.asha_id == asha_id).all()
        patient_ids = [p.id for p in patients]
        alerts = db.query(Alert).filter(Alert.asha_id == asha_id, Alert.acknowledged.is_(False)).all()
        if patient_ids:
            symptoms = (
                db.query(Symptom)
                .filter(Symptom.patient_id.in_(patient_ids))
                .order_by(Symptom.timestamp.desc())
                .limit(100)
                .all()
            )
        else:
            symptoms = []

        payload = {
            "asha_id": asha_id,
            "patients": [
                {
                    "id": p.id,
                    "name": p.name,
                    "age": p.age,
                    "village": p.village,
                    "district": p.district,
                    "pregnancy_week": p.pregnancy_week,
                }
                for p in patients
            ],
            "pending_alerts": [{"id": a.id, "patient_id": a.patient_id, "risk_score": a.risk_score, "created_at": a.created_at.isoformat()} for a in alerts],
            "recent_symptoms": [{"id": s.id, "patient_id": s.patient_id, "risk_score": s.risk_score, "risk_level": s.risk_level, "timestamp": s.timestamp.isoformat()} for s in symptoms],
            "checkup_templates": [
                {
                    "patient_id": p.id,
                    "bp_systolic": 0,
                    "bp_diastolic": 0,
                    "weight_kg": 0,
                    "notes": "",
                }
                for p in patients
            ],
        }
        encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
        return success_response({"base64_data": encoded})
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Bluetooth export failed: {exc}", 400)


@router.post("/bluetooth-import")
def bluetooth_import(payload: BluetoothImportRequest, db: Session = Depends(get_db)):
    try:
        raw = base64.b64decode(payload.base64_data.encode("utf-8")).decode("utf-8")
        data = json.loads(raw)
        merged_count = 0
        conflict_count = 0

        for item in data.get("patients", []):
            existing = db.query(Patient).filter(Patient.id == int(item["id"])).first()
            if not existing:
                continue
            merged_count += 1

        for item in data.get("recent_symptoms", []):
            existing = db.query(Symptom).filter(Symptom.id == int(item["id"])).first()
            if existing:
                conflict_count += 1
                continue
            row = Symptom(
                id=int(item["id"]),
                patient_id=int(item["patient_id"]),
                symptoms_list=[],
                input_type="bluetooth_import",
                transcription=None,
                risk_score=int(item.get("risk_score", 0)),
                risk_level=item.get("risk_level", "LOW"),
                primary_reason="Imported via bluetooth",
                timestamp=_parse_ts(item["timestamp"]),
            )
            db.add(row)
            merged_count += 1

        db.commit()
        return success_response({"merged_count": merged_count, "conflict_count": conflict_count})
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return error_response(f"Bluetooth import failed: {exc}", 400)
