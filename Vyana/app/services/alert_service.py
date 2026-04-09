import json
import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import BackgroundTasks

from sqlalchemy.orm import Session

import firebase_admin
from firebase_admin import credentials, messaging

from app.database import SessionLocal
from app.models import Alert, AshaWorker

load_dotenv()


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _init_firebase() -> bool:
    if firebase_admin._apps:
        return True

    raw = os.getenv("FIREBASE_CREDENTIALS_JSON", "").strip()
    if not raw:
        print("[ALERT] FIREBASE_CREDENTIALS_JSON missing, skipping push notifications")
        return False

    try:
        if raw.startswith("{"):
            cred_dict = json.loads(raw)
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate(raw)
        firebase_admin.initialize_app(cred)
        return True
    except Exception as exc:
        print(f"[ALERT] Firebase initialization failed: {exc}")
        return False


def _send_notification(device_token: str, patient_name: str, reason: str, patient_id: int, risk_score: int, alert_id: int, asha_name: str):
    if not _init_firebase() or not device_token:
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title="⚠️ High Risk Patient Alert",
            body=f"{patient_name} — {reason}",
        ),
        token=device_token,
        data={
            "patient_id": str(patient_id),
            "risk_score": str(risk_score),
            "alert_id": str(alert_id),
        },
    )

    try:
        messaging.send(message)
        print(f"[ALERT] Firebase notification sent to {asha_name}")
    except Exception as exc:
        print(f"[ALERT] Firebase send failed: {exc}")


def _escalate_if_unacknowledged(alert_id: int, patient_name: str, village: str, district: str):
    time.sleep(60)
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert and not alert.acknowledged:
            alert.escalation_level = 2
            db.commit()
            print(f"[ESCALATION] Level 2 triggered for {patient_name}")
            print(f"ESCALATION L2 — Family SMS would be sent for patient {patient_name}")
    finally:
        db.close()

    time.sleep(60)
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert and not alert.acknowledged:
            alert.escalation_level = 3
            db.commit()
            print(f"ESCALATION L3 — 108 Ambulance triggered for {patient_name} at {village}, {district}")
    finally:
        db.close()


def trigger_alert(
    db: Session,
    background_tasks: BackgroundTasks,
    patient_id: int,
    asha_id: int,
    patient_name: str,
    risk_score: int,
    reason: str,
    village: str,
    district: str,
) -> Alert:
    alert = Alert(
        patient_id=patient_id,
        asha_id=asha_id,
        risk_score=risk_score,
        risk_level="HIGH",
        escalation_level=1,
        acknowledged=False,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    asha = db.query(AshaWorker).filter(AshaWorker.id == asha_id).first()
    if asha:
        _send_notification(
            device_token=asha.device_token or "",
            patient_name=patient_name,
            reason=reason,
            patient_id=patient_id,
            risk_score=risk_score,
            alert_id=alert.id,
            asha_name=asha.name,
        )

    background_tasks.add_task(
        _escalate_if_unacknowledged,
        alert.id,
        patient_name,
        village,
        district,
    )

    return alert


def acknowledge_alert(db: Session, alert_id: int) -> float:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise ValueError("Alert not found")

    if alert.acknowledged:
        if alert.acknowledged_at:
            delta = alert.acknowledged_at - alert.created_at
            return round(delta.total_seconds() / 60, 2)
        return 0.0

    now = _utc_now_naive()
    alert.acknowledged = True
    alert.acknowledged_at = now
    db.commit()
    db.refresh(alert)

    delta = now - alert.created_at
    return round(delta.total_seconds() / 60, 2)
