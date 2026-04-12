from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import SessionLocal
from app.models import Alert, AshaWorker, Checkup, Patient, PredictiveAlert, Symptom
from app.services.alert_service import send_push_notification


scheduler = AsyncIOScheduler()


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def predictive_alerts_job() -> None:
    print("[SCHEDULER] Running...")

    db = SessionLocal()
    try:
        now = _utc_now_naive()
        recent_cutoff = now - timedelta(days=3)
        duplicate_cutoff = now - timedelta(hours=24)
        patients = db.query(Patient).all()

        for patient in patients:
            asha = db.query(AshaWorker).filter(AshaWorker.id == patient.asha_id).first()
            if not asha or not asha.is_active:
                continue

            alerts_to_create: list[dict] = []

            checkups = (
                db.query(Checkup)
                .filter(Checkup.patient_id == patient.id)
                .order_by(Checkup.created_at.desc())
                .limit(3)
                .all()
            )

            if len(checkups) >= 3:
                bp_values = [c.bp_systolic for c in checkups]
                if bp_values[0] > bp_values[1] > bp_values[2]:
                    alerts_to_create.append(
                        {
                            "type": "predictive",
                            "reason": f"{patient.name} ka BP trend lagatar bad raha hai - urgent visit karein",
                            "level": "MEDIUM",
                        }
                    )

            latest_checkup = checkups[0] if checkups else None
            if latest_checkup:
                days_since = (now - latest_checkup.created_at).days
            else:
                days_since = 999

            if days_since > 14:
                alerts_to_create.append(
                    {
                        "type": "overdue",
                        "reason": f"{patient.name} ka checkup {days_since} din se nahi hua",
                        "level": "MEDIUM",
                    }
                )

            if 36 <= patient.pregnancy_week <= 42 and days_since > 7:
                alerts_to_create.append(
                    {
                        "type": "delivery_week",
                        "reason": f"{patient.name} - delivery week ({patient.pregnancy_week}) aur checkup nahi hua",
                        "level": "HIGH",
                    }
                )

            recent_high = (
                db.query(Symptom)
                .filter(
                    Symptom.patient_id == patient.id,
                    Symptom.risk_level == "HIGH",
                    Symptom.timestamp >= recent_cutoff,
                )
                .order_by(Symptom.timestamp.desc())
                .first()
            )
            if recent_high:
                followup_checkup = (
                    db.query(Checkup)
                    .filter(
                        Checkup.patient_id == patient.id,
                        Checkup.created_at > recent_high.timestamp,
                    )
                    .first()
                )
                no_followup_since_high = followup_checkup is None
            else:
                no_followup_since_high = False

            if recent_high and no_followup_since_high:
                alerts_to_create.append(
                    {
                        "type": "high_risk_followup",
                        "reason": f"{patient.name} HIGH risk thi - follow-up visit karein",
                        "level": "HIGH",
                    }
                )

            if latest_checkup and latest_checkup.next_visit_date:
                if latest_checkup.next_visit_date < now.date() and days_since > 0:
                    alerts_to_create.append(
                        {
                            "type": "missed_appointment",
                            "reason": f"{patient.name} ki scheduled visit miss ho gayi",
                            "level": "MEDIUM",
                        }
                    )

            for item in alerts_to_create:
                duplicate = (
                    db.query(PredictiveAlert)
                    .filter(
                        PredictiveAlert.patient_id == patient.id,
                        PredictiveAlert.alert_type == item["type"],
                        PredictiveAlert.created_at >= duplicate_cutoff,
                    )
                    .first()
                )
                if duplicate:
                    continue

                alert = Alert(
                    patient_id=patient.id,
                    asha_id=patient.asha_id,
                    risk_score=50 if item["level"] == "MEDIUM" else 75,
                    risk_level=item["level"],
                    escalation_level=1,
                    acknowledged=False,
                )
                db.add(alert)
                db.flush()

                predictive = PredictiveAlert(
                    patient_id=patient.id,
                    asha_id=patient.asha_id,
                    alert_type=item["type"],
                    risk_level=item["level"],
                    reason=item["reason"],
                    linked_alert_id=alert.id,
                )
                db.add(predictive)

                send_push_notification(
                    device_token=asha.device_token or "",
                    title="📋 Predictive Alert",
                    body=item["reason"],
                    data={"patient_id": patient.id, "alert_type": item["type"]},
                )

            if alerts_to_create:
                db.commit()

        print("[SCHEDULER] Complete")
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        predictive_alerts_job,
        trigger=IntervalTrigger(hours=24),
        id="predictive_alerts",
        name="Daily Predictive Alerts",
        replace_existing=True,
    )
    scheduler.start()
    print("[SCHEDULER] Started - runs every 24 hours")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[SCHEDULER] Stopped")