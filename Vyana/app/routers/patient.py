from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient, Symptom
from app.schemas import PatientRegisterRequest
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/patient", tags=["patient"])


@router.post("/register")
def register_patient(payload: PatientRegisterRequest, db: Session = Depends(get_db)):
    try:
        patient = Patient(
            name=payload.name,
            age=payload.age,
            village=payload.village,
            district=payload.district,
            pregnancy_week=payload.pregnancy_week,
            phone_number=payload.phone_number,
            asha_id=payload.asha_id,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return success_response({"patient_id": patient.id})
    except Exception as exc:
        db.rollback()
        return error_response(f"Failed to register patient: {exc}", 400)


@router.get("/{patient_id}")
def get_patient_profile(patient_id: int, db: Session = Depends(get_db)):
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return error_response("Patient not found", 404)

        latest_symptom = (
            db.query(Symptom)
            .filter(Symptom.patient_id == patient_id)
            .order_by(Symptom.timestamp.desc())
            .first()
        )

        symptom_reports = (
            db.query(Symptom)
            .filter(Symptom.patient_id == patient_id)
            .order_by(Symptom.timestamp.desc())
            .limit(5)
            .all()
        )

        report_data = [
            {
                "id": s.id,
                "symptoms_list": s.symptoms_list,
                "input_type": s.input_type,
                "transcription": s.transcription,
                "risk_score": s.risk_score,
                "risk_level": s.risk_level,
                "primary_reason": s.primary_reason,
                "timestamp": s.timestamp.isoformat(),
            }
            for s in symptom_reports
        ]

        data = {
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "village": patient.village,
                "district": patient.district,
                "pregnancy_week": patient.pregnancy_week,
                "phone_number": patient.phone_number,
                "asha_id": patient.asha_id,
                "created_at": patient.created_at.isoformat(),
            },
            "latest_risk": {
                "risk_score": latest_symptom.risk_score if latest_symptom else None,
                "risk_level": latest_symptom.risk_level if latest_symptom else None,
            },
            "last_5_symptom_reports": report_data,
        }
        return success_response(data)
    except Exception as exc:
        return error_response(f"Failed to fetch patient profile: {exc}", 400)
