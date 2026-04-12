from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient, PatientConsent, PatientDeleteRequest, Symptom
from app.schemas import PatientConsentRequest, PatientDeleteRequestPayload, PatientRegisterRequest
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/patient", tags=["patient"])


def _mask_phone(phone: str) -> str:
    if len(phone) < 4:
        return "XXXX"
    return f"{phone[:2]}XXXXXX{phone[-2:]}"


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
                "phone_number": _mask_phone(patient.phone_number),
                "asha_id": patient.asha_id,
                "created_at": patient.created_at.isoformat(),
                "data_retention_until": (patient.created_at + timedelta(days=365 * 5)).isoformat(),
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


@router.post("/consent")
def set_consent(payload: PatientConsentRequest, db: Session = Depends(get_db)):
    try:
        patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
        if not patient:
            return error_response("Patient not found", 404)

        row = PatientConsent(patient_id=payload.patient_id, consent_type=payload.consent_type, granted=payload.granted)
        db.add(row)
        db.commit()
        return success_response({"saved": True, "consent_id": row.id})
    except Exception as exc:
        db.rollback()
        return error_response(f"Failed to save consent: {exc}", 400)


@router.get("/consent/{patient_id}")
def get_consent(patient_id: int, db: Session = Depends(get_db)):
    rows = db.query(PatientConsent).filter(PatientConsent.patient_id == patient_id).order_by(PatientConsent.created_at.desc()).all()
    return success_response(
        {
            "records": [
                {
                    "consent_type": r.consent_type,
                    "granted": r.granted,
                    "timestamp": r.created_at.isoformat(),
                }
                for r in rows
            ]
        }
    )


@router.post("/delete-request")
def delete_request(payload: PatientDeleteRequestPayload, db: Session = Depends(get_db)):
    try:
        patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
        if not patient:
            return error_response("Patient not found", 404)

        row = PatientDeleteRequest(patient_id=payload.patient_id, reason=payload.reason, status="queued")
        db.add(row)
        db.commit()
        return success_response({"queued": True, "request_id": row.id, "anonymize_within_days": 30})
    except Exception as exc:
        db.rollback()
        return error_response(f"Failed to queue delete request: {exc}", 400)


@router.get("/data-export/{patient_id}")
def data_export(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return error_response("Patient not found", 404)

    symptoms = db.query(Symptom).filter(Symptom.patient_id == patient_id).order_by(Symptom.timestamp.desc()).all()
    consents = db.query(PatientConsent).filter(PatientConsent.patient_id == patient_id).all()
    deletes = db.query(PatientDeleteRequest).filter(PatientDeleteRequest.patient_id == patient_id).all()

    return success_response(
        {
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "village": patient.village,
                "district": patient.district,
                "pregnancy_week": patient.pregnancy_week,
                "phone_number": _mask_phone(patient.phone_number),
                "created_at": patient.created_at.isoformat(),
            },
            "symptoms": [
                {
                    "id": s.id,
                    "symptoms_list": s.symptoms_list,
                    "input_type": s.input_type,
                    "risk_score": s.risk_score,
                    "risk_level": s.risk_level,
                    "timestamp": s.timestamp.isoformat(),
                }
                for s in symptoms
            ],
            "consents": [{"type": c.consent_type, "granted": c.granted, "timestamp": c.created_at.isoformat()} for c in consents],
            "delete_requests": [{"id": d.id, "reason": d.reason, "status": d.status, "timestamp": d.created_at.isoformat()} for d in deletes],
        }
    )
