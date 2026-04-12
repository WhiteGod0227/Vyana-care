from datetime import datetime, timedelta, timezone
import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, AshaWorker, Checkup, Patient, Symptom
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/district", tags=["district"])


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


VILLAGE_COORDS = {
    "Ramgarh": (25.123, 71.456),
    "Balotra": (25.832, 72.241),
    "Siwana": (25.651, 72.422),
    "Sam": (26.912, 70.923),
    "Pokaran": (26.917, 71.917),
    "Fatehgarh": (26.560, 71.300),
    "Osian": (26.742, 72.914),
    "Bilara": (26.180, 73.700),
    "Phalodi": (27.131, 72.368),
}


SUPPORTED_DISTRICTS = ["Barmer", "Jaisalmer", "Jodhpur"]


def _latest_symptom_for_patient(db: Session, patient_id: int):
    return (
        db.query(Symptom)
        .filter(Symptom.patient_id == patient_id)
        .order_by(Symptom.timestamp.desc())
        .first()
    )


def _district_snapshot_data(district_name: str, db: Session) -> dict:
    patients = (
        db.query(Patient)
        .filter(func.lower(Patient.district) == district_name.lower())
        .all()
    )

    latest_levels = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    high_risk_patients = []

    for patient in patients:
        latest_symptom = _latest_symptom_for_patient(db, patient.id)

        if latest_symptom:
            level = latest_symptom.risk_level
            latest_levels[level] = latest_levels.get(level, 0) + 1
        else:
            level = "LOW"
            latest_levels["LOW"] += 1

        coords = VILLAGE_COORDS.get(patient.village)
        if level in {"HIGH", "MEDIUM"} and latest_symptom and coords:
            high_risk_patients.append(
                {
                    "id": patient.id,
                    "name": patient.name,
                    "village": patient.village,
                    "district": patient.district,
                    "risk_level": latest_symptom.risk_level,
                    "risk_score": latest_symptom.risk_score,
                    "primary_reason": latest_symptom.primary_reason,
                    "latitude": coords[0],
                    "longitude": coords[1],
                }
            )

    start_of_day = _utc_now_naive().replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    alerts_today = (
        db.query(Alert)
        .join(Patient, Alert.patient_id == Patient.id)
        .filter(
            func.lower(Patient.district) == district_name.lower(),
            Alert.created_at >= start_of_day,
            Alert.created_at < end_of_day,
        )
        .count()
    )

    unack_count = (
        db.query(Alert)
        .join(Patient, Alert.patient_id == Patient.id)
        .filter(
            func.lower(Patient.district) == district_name.lower(),
            Alert.acknowledged.is_(False),
        )
        .count()
    )

    high_risk_patients.sort(key=lambda p: (-p["risk_score"], p["name"]))

    return {
        "stats": {
            "total_patients": len(patients),
            "high_risk": latest_levels.get("HIGH", 0),
            "medium_risk": latest_levels.get("MEDIUM", 0),
            "low_risk": latest_levels.get("LOW", 0),
            "alerts_fired_today": alerts_today,
            "unacknowledged_alerts": unack_count,
        },
        "high_risk_patients": high_risk_patients,
    }


@router.get("/stats")
def all_district_stats(db: Session = Depends(get_db)):
    try:
        rows = []
        for district in SUPPORTED_DISTRICTS:
            snap = _district_snapshot_data(district, db)
            rows.append(
                {
                    "district": district,
                    "total_patients": snap["stats"]["total_patients"],
                    "high_risk": snap["stats"]["high_risk"],
                    "medium_risk": snap["stats"]["medium_risk"],
                    "low_risk": snap["stats"]["low_risk"],
                }
            )
        return success_response({"district_stats": rows})
    except Exception as exc:
        return error_response(f"Failed to get district stats: {exc}", 400)


@router.get("/{district_name}/snapshot")
def district_snapshot(district_name: str, db: Session = Depends(get_db)):
    try:
        return success_response(_district_snapshot_data(district_name, db))
    except Exception as exc:
        return error_response(f"Failed to get district snapshot: {exc}", 400)


@router.get("/{district_name}/stats")
def district_stats(district_name: str, db: Session = Depends(get_db)):
    try:
        snap = _district_snapshot_data(district_name, db)

        return success_response(
            {
                "total_patients": snap["stats"]["total_patients"],
                "high_count": snap["stats"]["high_risk"],
                "medium_count": snap["stats"]["medium_risk"],
                "low_count": snap["stats"]["low_risk"],
                "alerts_fired_today": snap["stats"]["alerts_fired_today"],
                "unacknowledged_alerts": snap["stats"]["unacknowledged_alerts"],
            }
        )
    except Exception as exc:
        return error_response(f"Failed to get district stats: {exc}", 400)


@router.get("/{district_name}/heatmap")
def district_heatmap(district_name: str, db: Session = Depends(get_db)):
    try:
        patients = (
            db.query(Patient)
            .filter(func.lower(Patient.district) == district_name.lower())
            .all()
        )

        grouped: dict[str, dict] = {}
        for patient in patients:
            if patient.village not in VILLAGE_COORDS:
                continue

            latest_symptom = (
                db.query(Symptom)
                .filter(Symptom.patient_id == patient.id)
                .order_by(Symptom.timestamp.desc())
                .first()
            )

            if patient.village not in grouped:
                lat, lng = VILLAGE_COORDS[patient.village]
                grouped[patient.village] = {
                    "village": patient.village,
                    "latitude": lat,
                    "longitude": lng,
                    "high_risk_count": 0,
                    "total_patients": 0,
                }

            grouped[patient.village]["total_patients"] += 1
            if latest_symptom and latest_symptom.risk_level == "HIGH":
                grouped[patient.village]["high_risk_count"] += 1

        return success_response({"heatmap": list(grouped.values())})
    except Exception as exc:
        return error_response(f"Failed to get district heatmap: {exc}", 400)


def _csv_response(filename: str, rows: list[list[str]]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    data = io.BytesIO(buffer.getvalue().encode("utf-8"))
    return StreamingResponse(
        data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{district_name}/export/csv")
def export_district_csv(district_name: str, db: Session = Depends(get_db)):
    snap = _district_snapshot_data(district_name, db)
    rows = [["Village", "Total Patients", "High Risk"]]
    heatmap = district_heatmap(district_name, db)
    payload = heatmap.body.decode("utf-8") if hasattr(heatmap, "body") else ""
    if payload:
        import json

        parsed = json.loads(payload)
        for item in parsed.get("data", {}).get("heatmap", []):
            rows.append([str(item.get("village", "")), str(item.get("total_patients", 0)), str(item.get("high_risk_count", 0))])
    rows.append([])
    rows.append(["District", district_name])
    rows.append(["Total", str(snap["stats"]["total_patients"])])
    rows.append(["High", str(snap["stats"]["high_risk"])])
    rows.append(["Medium", str(snap["stats"]["medium_risk"])])
    rows.append(["Low", str(snap["stats"]["low_risk"])])
    filename = f"District_{district_name}_{datetime.now().strftime('%Y%m%d')}.csv"
    return _csv_response(filename, rows)


@router.get("/{district_name}/export/nrhm")
def export_nrhm(district_name: str, db: Session = Depends(get_db)):
    now = datetime.now()
    month_label = now.strftime("%B")
    year_label = now.strftime("%Y")

    patients = db.query(Patient).filter(func.lower(Patient.district) == district_name.lower()).all()
    total_registered = len(patients)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (month_start + timedelta(days=32)).replace(day=1)

    high_cases = 0
    for p in patients:
        latest = (
            db.query(Symptom)
            .filter(Symptom.patient_id == p.id)
            .order_by(Symptom.timestamp.desc())
            .first()
        )
        if latest and latest.risk_level == "HIGH":
            high_cases += 1

    district_asha_ids = [
        p.asha_id
        for p in patients
        if p.asha_id is not None
    ]
    ashas = db.query(AshaWorker).filter(AshaWorker.id.in_(district_asha_ids) if district_asha_ids else False).all()

    alerts_this_month = (
        db.query(Alert)
        .join(Patient, Alert.patient_id == Patient.id)
        .filter(
            func.lower(Patient.district) == district_name.lower(),
            Alert.created_at >= month_start,
            Alert.created_at < next_month,
        )
        .all()
    )

    response_minutes = []
    for a in alerts_this_month:
        if a.acknowledged and a.acknowledged_at:
            mins = (a.acknowledged_at - a.created_at).total_seconds() / 60
            response_minutes.append(mins)
    avg_response = round(sum(response_minutes) / len(response_minutes), 2) if response_minutes else 0

    village_map: dict[str, dict[str, int]] = {}
    for p in patients:
        if p.village not in village_map:
            village_map[p.village] = {"total": 0, "high": 0}
        village_map[p.village]["total"] += 1
        latest = (
            db.query(Symptom)
            .filter(Symptom.patient_id == p.id)
            .order_by(Symptom.timestamp.desc())
            .first()
        )
        if latest and latest.risk_level == "HIGH":
            village_map[p.village]["high"] += 1

    rows: list[list[str]] = []
    rows.append(["NRHM Monthly Report"])
    rows.append([f"District: {district_name}"])
    rows.append([f"Period: {month_label} {year_label}"])
    rows.append([])

    rows.append(["Total Patients registered", str(total_registered)])
    rows.append(["High Risk Cases", str(high_cases)])
    rows.append(["Alerts Fired This Month", str(len(alerts_this_month))])
    rows.append(["Avg Response Time (minutes)", str(avg_response)])
    rows.append([])

    rows.append(["ASHA Name", "Patients", "Checkups Done", "Alerts Responded"])
    for asha in ashas:
        asha_patients = db.query(Patient).filter(Patient.asha_id == asha.id, func.lower(Patient.district) == district_name.lower()).all()
        asha_patient_ids = [p.id for p in asha_patients]
        checkups_done = db.query(Checkup).filter(Checkup.asha_id == asha.id).count()
        asha_alerts = db.query(Alert).filter(Alert.asha_id == asha.id, Alert.patient_id.in_(asha_patient_ids) if asha_patient_ids else False).all()
        responded = len([a for a in asha_alerts if a.acknowledged])
        rows.append([asha.name, str(len(asha_patients)), str(checkups_done), str(responded)])
    rows.append([])

    rows.append(["Village", "Total", "High Risk"])
    for village, stats in sorted(village_map.items()):
        rows.append([village, str(stats["total"]), str(stats["high"])])

    filename = f"NRHM_{district_name}_{month_label}_{year_label}.csv"
    return _csv_response(filename, rows)


@router.get("/{district_name}/export/highrisk")
def export_highrisk(district_name: str, db: Session = Depends(get_db)):
    patients = db.query(Patient).filter(func.lower(Patient.district) == district_name.lower()).all()
    rows = [["Name", "Age", "Village", "Pregnancy Week", "Risk Score", "Risk Reason", "Last Alert Date", "ASHA Worker", "Days Since Checkup"]]

    now = _utc_now_naive()
    compiled = []
    for p in patients:
        latest = (
            db.query(Symptom)
            .filter(Symptom.patient_id == p.id)
            .order_by(Symptom.timestamp.desc())
            .first()
        )
        if not latest or latest.risk_level != "HIGH":
            continue
        latest_alert = (
            db.query(Alert)
            .filter(Alert.patient_id == p.id)
            .order_by(Alert.created_at.desc())
            .first()
        )
        latest_checkup = (
            db.query(Checkup)
            .filter(Checkup.patient_id == p.id)
            .order_by(Checkup.created_at.desc())
            .first()
        )
        days_since = (now - latest_checkup.created_at).days if latest_checkup else 999
        asha = db.query(AshaWorker).filter(AshaWorker.id == p.asha_id).first()
        compiled.append(
            {
                "name": p.name,
                "age": p.age,
                "village": p.village,
                "week": p.pregnancy_week,
                "score": latest.risk_score,
                "reason": latest.primary_reason,
                "alert_date": latest_alert.created_at.strftime("%d-%m-%Y %H:%M") if latest_alert else "N/A",
                "asha": asha.name if asha else "N/A",
                "days": days_since,
            }
        )

    compiled.sort(key=lambda item: item["score"], reverse=True)
    for item in compiled:
        rows.append(
            [
                item["name"],
                str(item["age"]),
                item["village"],
                str(item["week"]),
                str(item["score"]),
                item["reason"],
                item["alert_date"],
                item["asha"],
                str(item["days"]),
            ]
        )

    filename = f"HighRisk_{district_name}_{datetime.now().strftime('%Y%m%d')}.csv"
    return _csv_response(filename, rows)
