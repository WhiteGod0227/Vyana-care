from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Patient, Symptom
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
