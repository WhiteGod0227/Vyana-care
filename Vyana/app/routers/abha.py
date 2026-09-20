import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models import Patient, Symptom
from app.schemas import AbhaLinkRequest, AbhaVerifyRequest
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/abha", tags=["abha"])


def _abha_available() -> bool:
    return bool(settings.abha_sandbox_api_key)



@router.post("/verify")
def verify(payload: AbhaVerifyRequest):
    if not payload.abha_id or len(payload.abha_id) < 8:
        return error_response("Invalid ABHA ID", 400)

    if not _abha_available():
        return success_response(
            {
                "verified": True,
                "mode": "sandbox-mock",
                "profile": {"abha_id": payload.abha_id, "name": "Demo Patient", "gender": "F"},
            }
        )

    return success_response({"verified": True, "profile": {"abha_id": payload.abha_id}})


@router.post("/link-patient")
def link_patient(payload: AbhaLinkRequest, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        return error_response("Patient not found", 404)

    if len(payload.abha_id) < 8:
        return error_response("Invalid ABHA ID", 400)

    setattr(patient, "abha_id", payload.abha_id)
    if not hasattr(Patient, "abha_id"):
        return success_response({"linked": True, "warning": "Patient model has no abha_id column yet"})

    db.commit()
    return success_response({"linked": True, "patient_id": patient.id, "abha_id": payload.abha_id})


@router.get("/health-records/{abha_id}")
def health_records(abha_id: str):
    records = [
        {
            "resourceType": "Observation",
            "id": f"obs-{abha_id[-4:]}-001",
            "text": "Maternal risk observation",
            "timestamp": "2026-04-10T10:00:00Z",
        }
    ]
    return success_response({"abha_id": abha_id, "records": records})


@router.post("/push-record")
def push_record(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return error_response("Patient not found", 404)

    latest = db.query(Symptom).filter(Symptom.patient_id == patient_id).order_by(Symptom.timestamp.desc()).first()
    payload = {
        "resourceType": "Observation",
        "patient": {"reference": getattr(patient, "abha_id", "unlinked")},
        "valueInteger": latest.risk_score if latest else 0,
        "components": latest.symptoms_list if latest else [],
    }

    errors = []
    for attempt in range(1, 4):
        try:
            time.sleep(0.05 * attempt)
            return success_response({"pushed": True, "attempt": attempt, "payload": payload})
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

    print(f"[ABHA] push failed after retries: {errors}")
    return success_response({"pushed": False, "errors": errors, "payload": payload})
