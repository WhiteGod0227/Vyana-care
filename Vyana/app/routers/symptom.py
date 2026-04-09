from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Checkup, Patient, Symptom
from app.schemas import SymptomTextRequest
from app.services.alert_service import trigger_alert
from app.services.risk_model import calculate_risk
from app.services.voice_service import process_voice
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/symptom", tags=["symptom"])


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _days_since_last_checkup(db: Session, patient_id: int) -> int:
    checkup = (
        db.query(Checkup)
        .filter(Checkup.patient_id == patient_id)
        .order_by(Checkup.created_at.desc())
        .first()
    )
    if not checkup:
        return 0
    return (_utc_now_naive() - checkup.created_at).days


@router.post("/report/text")
def report_text_symptom(
    payload: SymptomTextRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
        if not patient:
            return error_response("Patient not found", 404)

        risk_result = calculate_risk(
            symptoms=payload.symptoms,
            bp_systolic=payload.bp_systolic,
            bp_diastolic=payload.bp_diastolic,
            age=payload.age,
            pregnancy_week=payload.pregnancy_week,
            days_since_last_checkup=payload.days_since_last_checkup,
            previous_complications=payload.previous_complications,
        )

        symptom = Symptom(
            patient_id=payload.patient_id,
            symptoms_list=payload.symptoms,
            input_type="text",
            transcription=None,
            risk_score=risk_result["score"],
            risk_level=risk_result["level"],
            primary_reason=risk_result["primary_reason"],
        )
        db.add(symptom)
        db.commit()
        db.refresh(symptom)

        if risk_result["level"] == "HIGH":
            trigger_alert(
                db=db,
                background_tasks=background_tasks,
                patient_id=patient.id,
                asha_id=patient.asha_id,
                patient_name=patient.name,
                risk_score=risk_result["score"],
                reason=risk_result["primary_reason"],
                village=patient.village,
                district=patient.district,
            )

        return success_response({"risk_result": risk_result})
    except Exception as exc:
        db.rollback()
        return error_response(f"Failed to submit text symptom report: {exc}", 400)


@router.post("/report/voice")
def report_voice_symptom(
    background_tasks: BackgroundTasks,
    patient_id: int = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return error_response("Patient not found", 404)

        try:
            voice_data = process_voice(audio_file)
        except Exception as exc:
            return error_response(f"Voice processing failed: {exc}", 500)

        days_since_last_checkup = _days_since_last_checkup(db, patient_id)

        risk_result = calculate_risk(
            symptoms=voice_data.get("symptoms", []),
            bp_systolic=0,
            bp_diastolic=0,
            age=patient.age,
            pregnancy_week=patient.pregnancy_week,
            days_since_last_checkup=days_since_last_checkup,
            previous_complications=False,
        )

        symptom = Symptom(
            patient_id=patient_id,
            symptoms_list=voice_data.get("symptoms", []),
            input_type="voice",
            transcription=voice_data.get("transcription"),
            risk_score=risk_result["score"],
            risk_level=risk_result["level"],
            primary_reason=risk_result["primary_reason"],
        )
        db.add(symptom)
        db.commit()
        db.refresh(symptom)

        if risk_result["level"] == "HIGH":
            trigger_alert(
                db=db,
                background_tasks=background_tasks,
                patient_id=patient.id,
                asha_id=patient.asha_id,
                patient_name=patient.name,
                risk_score=risk_result["score"],
                reason=risk_result["primary_reason"],
                village=patient.village,
                district=patient.district,
            )

        return success_response(
            {
                "transcription": voice_data.get("transcription", ""),
                "symptoms": voice_data.get("symptoms", []),
                "risk_result": risk_result,
                "confidence": voice_data.get("confidence", "low"),
                "original_complaints": voice_data.get("original_complaints", ""),
                "gemini_json_error": voice_data.get("gemini_json_error", False),
            }
        )
    except Exception as exc:
        db.rollback()
        return error_response(f"Failed to submit voice symptom report: {exc}", 400)
