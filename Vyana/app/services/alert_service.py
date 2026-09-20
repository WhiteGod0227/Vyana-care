import json
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

import firebase_admin
from firebase_admin import credentials, messaging
from twilio.rest import Client

from app.core.config import settings
from app.database import SessionLocal
from app.models import Alert, AshaWorker, Patient


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def init_firebase() -> bool:
    try:
        if firebase_admin._apps:
            print("[FIREBASE] [OK] Working")
            return True

        cred_value = settings.firebase_credentials_json.strip()
        if not cred_value:
            print("[FIREBASE] [FAIL] Failed: FIREBASE_CREDENTIALS_JSON missing")
            return False

        if cred_value.startswith("{"):
            cred_dict = json.loads(cred_value)
            cred = credentials.Certificate(cred_dict)
        else:
            raw_path = Path(cred_value).expanduser()
            if raw_path.is_absolute():
                cred_path = raw_path
            else:
                project_root = Path(__file__).resolve().parents[2]
                cred_path = (project_root / raw_path).resolve()
            cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
        print("[FIREBASE] [OK] Working")
        return True
    except Exception as exc:
        print(f"[FIREBASE] [FAIL] Failed: {exc}")
        return False


def send_push_notification(device_token: str, title: str, body: str, data: dict | None = None) -> bool:
    try:
        if not init_firebase():
            return False

        if not device_token:
            print("[FIREBASE] [FAIL] Failed: missing device token")
            return False

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=device_token,
            data={k: str(v) for k, v in (data or {}).items()},
        )

        response = messaging.send(message)
        print(f"[FIREBASE] [OK] Working ({response})")
        return True
    except Exception as exc:
        print(f"[FIREBASE] [FAIL] Failed: {exc}")
        return False


def _send_sms(to_number: str, message: str) -> bool:
    if not to_number:
        print("[TWILIO] Missing destination number - skipped")
        return False

    sid = settings.twilio_account_sid
    token = settings.twilio_auth_token
    from_number = settings.twilio_from_number
    if not sid or not token or not from_number:
        print("[TWILIO] Missing credentials - skipped")
        return False

    try:
        client = Client(sid, token)
        client.messages.create(body=message, from_=from_number, to=to_number)
        print(f"[TWILIO] SMS sent to {to_number}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[TWILIO] SMS failed: {exc}")
        return False


def _resolve_demo_phone(phone: str) -> str:
    demo_phone = settings.twilio_to_number
    return demo_phone or phone


def escalation_chain(
    alert_id: int,
    patient_name: str,
    village: str,
    district: str,
    patient_family_phone: str,
    phc_nurse_phone: str,
):
    wait_time = settings.demo_escalation_seconds

    time.sleep(wait_time)
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert or alert.acknowledged:
            print(f"[ESCALATION] Alert {alert_id} acknowledged - stopping")
            return

        alert.escalation_level = 2
        db.commit()

        family_msg = (
            f"Vyana Care: {patient_name} ko turant madad chahiye. "
            f"ASHA didi aa rahi hain. Emergency mein 108 dial karein."
        )
        sms_ok = _send_sms(_resolve_demo_phone(patient_family_phone), family_msg)
        if sms_ok:
            print("[TWILIO L2] [OK] SMS sent")
        else:
            print("[TWILIO L2] [FAIL] SMS failed")
    finally:
        db.close()

    time.sleep(wait_time)
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert or alert.acknowledged:
            print(f"[ESCALATION] Alert {alert_id} acknowledged at L2 - stopping")
            return

        alert.escalation_level = 3
        db.commit()

        nurse_msg = (
            f"Vyana Care EMERGENCY: {patient_name}, {village} -- PHC nurse turant action karein."
        )
        sms_ok = _send_sms(_resolve_demo_phone(phc_nurse_phone), nurse_msg)
        if sms_ok:
            print("[TWILIO L3] [OK] PHC SMS sent")
        else:
            print("[TWILIO L3] [FAIL] PHC SMS failed")
        print(f"[108] Ambulance logged for {patient_name} at {village}")
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
    sent_push = False
    if asha:
        sent_push = send_push_notification(
            device_token=asha.device_token or "",
            title="⚠ High Risk Alert",
            body=f"{patient_name} — {reason}",
            data={
                "patient_id": str(patient_id),
                "alert_id": str(alert.id),
                "risk_score": str(risk_score),
            },
        )

    if not sent_push:
        fallback_msg = (
            f"⚠ Vyana Care Alert: {patient_name}\n"
            f"Risk: HIGH - {reason}\n"
            "Turant action karein."
        )
        _send_sms(_resolve_demo_phone(asha.phone if asha else ""), fallback_msg)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    patient_family_phone = _resolve_demo_phone(patient.phone_number if patient else "")
    phc_nurse_phone = _resolve_demo_phone(asha.phone if asha else "")

    background_tasks.add_task(
        escalation_chain,
        alert.id,
        patient_name,
        village,
        district,
        patient_family_phone,
        phc_nurse_phone,
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
