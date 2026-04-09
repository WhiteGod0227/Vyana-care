from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Checkup, Patient, Symptom
from app.schemas import CheckupRecordRequest
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/asha", tags=["asha"])


RISK_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.get("/{asha_id}/patients")
def get_asha_patients(asha_id: int, db: Session = Depends(get_db)):
    try:
        patients = db.query(Patient).filter(Patient.asha_id == asha_id).all()
        rows = []
        for p in patients:
            latest_symptom = (
                db.query(Symptom)
                .filter(Symptom.patient_id == p.id)
                .order_by(Symptom.timestamp.desc())
                .first()
            )
            latest_checkup = (
                db.query(Checkup)
                .filter(Checkup.patient_id == p.id)
                .order_by(Checkup.created_at.desc())
                .first()
            )

            days_since_last_checkup = 0
            if latest_checkup:
                days_since_last_checkup = (_utc_now_naive() - latest_checkup.created_at).days

            rows.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "village": p.village,
                    "risk_level": latest_symptom.risk_level if latest_symptom else "LOW",
                    "risk_score": latest_symptom.risk_score if latest_symptom else 0,
                    "days_since_last_checkup": days_since_last_checkup,
                    "last_symptom_date": latest_symptom.timestamp.isoformat() if latest_symptom else None,
                }
            )

        rows.sort(key=lambda r: (RISK_ORDER.get(r["risk_level"], 3), -r["risk_score"]))
        return success_response({"patients": rows})
    except Exception as exc:
        return error_response(f"Failed to fetch ASHA patients: {exc}", 400)


@router.post("/checkup/record")
def record_checkup(payload: CheckupRecordRequest, db: Session = Depends(get_db)):
    try:
        checkup = Checkup(
            patient_id=payload.patient_id,
            asha_id=payload.asha_id,
            bp_systolic=payload.bp_systolic,
            bp_diastolic=payload.bp_diastolic,
            weight_kg=payload.weight_kg,
            notes=payload.notes,
            next_visit_date=payload.next_visit_date,
        )
        db.add(checkup)
        db.commit()
        db.refresh(checkup)
        return success_response({"checkup_id": checkup.id})
    except Exception as exc:
        db.rollback()
        return error_response(f"Failed to record checkup: {exc}", 400)


@router.get("/{asha_id}/alerts")
def get_unacknowledged_alerts(asha_id: int, db: Session = Depends(get_db)):
    try:
        alerts = (
            db.query(Alert, Patient)
            .join(Patient, Alert.patient_id == Patient.id)
            .filter(Alert.asha_id == asha_id, Alert.acknowledged.is_(False))
            .order_by(Alert.created_at.desc())
            .all()
        )

        rows = []
        now = _utc_now_naive()
        for alert, patient in alerts:
            minutes_ago = int((now - alert.created_at).total_seconds() // 60)
            high_symptoms = (
                db.query(Symptom)
                .filter(
                    Symptom.patient_id == patient.id,
                    Symptom.risk_level == "HIGH",
                )
                .order_by(Symptom.timestamp.desc())
                .first()
            )

            alert_symptom = None
            if high_symptoms:
                high_rows = (
                    db.query(Symptom)
                    .filter(
                        Symptom.patient_id == patient.id,
                        Symptom.risk_level == "HIGH",
                    )
                    .order_by(Symptom.timestamp.desc())
                    .limit(20)
                    .all()
                )
                alert_symptom = min(
                    high_rows,
                    key=lambda s: abs((s.timestamp - alert.created_at).total_seconds()),
                )

            if not alert_symptom:
                alert_symptom = (
                    db.query(Symptom)
                    .filter(Symptom.patient_id == patient.id)
                    .order_by(Symptom.timestamp.desc())
                    .first()
                )

            rows.append(
                {
                    "alert_id": alert.id,
                    "patient_name": patient.name,
                    "risk_reason": alert_symptom.primary_reason if alert_symptom else "High risk symptoms",
                    "escalation_level": alert.escalation_level,
                    "time_ago": f"{minutes_ago} minutes ago",
                }
            )

        return success_response({"alerts": rows})
    except Exception as exc:
        return error_response(f"Failed to fetch alerts: {exc}", 400)
