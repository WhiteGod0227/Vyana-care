from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models import Alert, AmbulanceDispatch, Patient
from app.services.alert_service import trigger_alert
from app.services.twilio_service import place_test_call, twilio_is_configured
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/sos", tags=["sos"])


class SOSTriggerRequest(BaseModel):
    patient_name: str = "Savitri Devi"
    patient_id: Optional[int] = 1
    village: str = "Ramgarh"
    district: str = "Barmer"
    phone: str = "9000010001"
    emergency_type: str = "MATERNAL_EMERGENCY_108"
    symptoms_summary: Optional[str] = "Severe distress / emergency SOS triggered"
    gps_lat: Optional[float] = 25.123
    gps_lng: Optional[float] = 71.456

def _mask(phone: str) -> str:
    return f"{phone[:4]}XXXXXX" if len(phone) >= 4 else "XXXXXX"

@router.post("/trigger")
def trigger_maternal_sos(
    payload: SOSTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        # 1. Dispatch 108 Ambulance Record
        dispatch_row = AmbulanceDispatch(
            patient_name=payload.patient_name,
            village=payload.village,
            district=payload.district,
            phone_masked=_mask(payload.phone),
            emergency_type=payload.emergency_type,
            gps_lat=payload.gps_lat or 25.123,
            gps_lng=payload.gps_lng or 71.456,
            eta_minutes=18,
            status="dispatched",
            created_at=datetime.utcnow(),
        )
        db.add(dispatch_row)
        db.commit()
        db.refresh(dispatch_row)

        # 2. Trigger High-Priority ASHA Alert
        alert_id = None
        patient = None
        if payload.patient_id:
            patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
        
        asha_id = patient.asha_id if patient else 1
        patient_name = payload.patient_name
        risk_reason = f"🚨 EMERGENCY SOS: {payload.symptoms_summary} at {payload.village}"

        try:
            alert = Alert(
                patient_id=payload.patient_id or 1,
                asha_id=asha_id,
                risk_score=99,
                risk_level="HIGH",
                risk_reason=risk_reason,
                escalation_level=1,
                created_at=datetime.utcnow(),
                acknowledged=False,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            alert_id = alert.id
        except Exception as alert_err:
            print(f"[SOS] Alert insert warning: {alert_err}")

        # 3. Twilio Outreach (if configured, or simulated)
        twilio_status = "simulated"
        twilio_details = None
        if twilio_is_configured():
            try:
                twilio_msg = f"EMERGENCY: Maternal SOS for {patient_name}, {payload.village}, Barmer. 108 Ambulance dispatched."
                twilio_res = place_test_call(
                    to_number=payload.phone,
                    message=twilio_msg
                )
                twilio_status = "call_placed"
                twilio_details = twilio_res
            except Exception as twilio_err:
                twilio_status = f"failed: {twilio_err}"

        return success_response({
            "status": "EMERGENCY_DISPATCHED",
            "dispatch_id": dispatch_row.id,
            "ambulance_id": "RJ-108-047",
            "driver_name": "Ramu Lal",
            "driver_phone": settings.default_driver_phone,
            "eta_minutes": 18,
            "patient_name": payload.patient_name,
            "village": payload.village,
            "district": payload.district,
            "alert_id": alert_id,
            "twilio_outreach": twilio_status,
            "emergency_numbers": {
                "ambulance": settings.emergency_ambulance_number,
                "asha_didi": settings.emergency_asha_phone,
                "phc_nurse": settings.emergency_phc_phone,
            },
            "instructions_hi": "कृपया शांत रहें और बाईं करवट लेटें। 108 एम्बुलेंस और आशा दीदी को आपकी लाइव लोकेशन भेज दी गई है।",
            "instructions_en": "Please stay calm and lie on your left side. 108 Ambulance and your ASHA worker are notified.",
        })
    except Exception as exc:
        db.rollback()
        return error_response(f"SOS trigger failed: {exc}", 500)
