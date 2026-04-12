import csv
import io
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Checkup, Patient, Symptom
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/hmis", tags=["hmis"])


def _weekly_report(district: str, db: Session) -> dict:
    since = datetime.utcnow() - timedelta(days=7)
    patients = db.query(Patient).filter(Patient.district.ilike(district)).all()
    patient_ids = [p.id for p in patients]

    if patient_ids:
        high = (
            db.query(Symptom)
            .filter(Symptom.patient_id.in_(patient_ids), Symptom.risk_level == "HIGH", Symptom.timestamp >= since)
            .count()
        )
        checkups = db.query(Checkup).filter(Checkup.patient_id.in_(patient_ids), Checkup.created_at >= since).count()
        alerts = db.query(Alert).filter(Alert.patient_id.in_(patient_ids), Alert.created_at >= since).all()
    else:
        high = 0
        checkups = 0
        alerts = []
    ack = [a for a in alerts if a.acknowledged and a.acknowledged_at]
    avg_response = 0
    if ack:
        avg_response = round(sum((a.acknowledged_at - a.created_at).total_seconds() for a in ack) / len(ack) / 60, 2)

    return {
        "district": district,
        "reporting_period": "weekly",
        "total_anc_registrations": len(patients),
        "high_risk_cases_identified": high,
        "asha_worker_performance_metrics": {
            "checkups_completed": checkups,
            "alerts_handled": len(ack),
        },
        "alert_response_time_minutes": avg_response,
        "checkup_completion_rate": round((checkups / len(patients) * 100), 2) if patients else 0,
    }


@router.get("/export/weekly/{district}")
def export_weekly(district: str, db: Session = Depends(get_db)):
    try:
        report = _weekly_report(district, db)
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["district", "anc", "high_risk", "checkups", "response_time_minutes"])
        writer.writerow(
            [
                report["district"],
                report["total_anc_registrations"],
                report["high_risk_cases_identified"],
                report["asha_worker_performance_metrics"]["checkups_completed"],
                report["alert_response_time_minutes"],
            ]
        )
        return success_response({"report": report, "csv": stream.getvalue()})
    except Exception as exc:  # noqa: BLE001
        return error_response(f"HMIS weekly export failed: {exc}", 400)


@router.post("/sync")
def sync(report_payload: dict):
    print(f"[HMIS] Sync initiated: {report_payload}")
    return success_response({"synced": True, "synced_at": datetime.utcnow().isoformat()})
