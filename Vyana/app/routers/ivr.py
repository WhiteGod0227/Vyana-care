from datetime import datetime
from xml.sax.saxutils import escape

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import IvrCallLog, Patient, Symptom
from app.services.alert_service import trigger_alert
from app.services.risk_model import calculate_risk
from app.services.twilio_service import place_test_call
from app.schemas import TwilioTestCallRequest
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/ivr", tags=["ivr"])


SYMPTOM_MAP = {
    "1": "headache",
    "2": "swelling",
    "3": "blurred_vision",
    "4": "bleeding",
    "5": "fever",
    "6": "fatigue",
    "7": "dizziness",
}


def _xml(body: str) -> Response:
    return Response(content=body, media_type="application/xml")


def _mask(phone: str) -> str:
    if len(phone) < 5:
        return "XXXXX"
    return f"{phone[:5]}XXXXX"


def _find_patient(db: Session, phone: str):
    return db.query(Patient).filter(Patient.phone_number == phone).first()


@router.post("/incoming")
def incoming(From: str = Form(default="anonymous"), db: Session = Depends(get_db)):  # noqa: N803
    patient = _find_patient(db, From)
    row = IvrCallLog(caller_number=From, patient_id=patient.id if patient else None, symptoms_collected=[])
    db.add(row)
    db.commit()
    db.refresh(row)

    body = f"""<Response>
  <Gather numDigits=\"1\" action=\"/ivr/symptom1\" method=\"POST\">
    <Say language=\"hi-IN\" voice=\"Polly.Aditi\">
      Vyana Care mein aapka swagat hai.
      Sir dard ke liye 1 dabayein.
      Pair mein sujan ke liye 2 dabayein.
      Aankhon ke aage andhera ke liye 3 dabayein.
      Khoon aane ke liye 4 dabayein.
      Bukhar ke liye 5 dabayein.
      Thakaan ya kamzori ke liye 6 dabayein.
      Chakkar aane ke liye 7 dabayein.
    </Say>
  </Gather>
  <Say language=\"hi-IN\">Input na milne par call samapt ki ja rahi hai.</Say>
</Response>"""
    return _xml(body)


@router.post("/twilio-test-call")
def twilio_test_call(payload: TwilioTestCallRequest):
    try:
        result = place_test_call(
            to_number=payload.to_number,
            message=payload.message,
            use_local_webhook=payload.use_local_webhook,
        )
        return success_response(result)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Twilio call failed: {exc}", 502)


@router.post("/symptom1")
def symptom1(
    background_tasks: BackgroundTasks,
    Digits: str = Form(default=""),  # noqa: N803
    From: str = Form(default="anonymous"),  # noqa: N803
    db: Session = Depends(get_db),
):
    symptom = SYMPTOM_MAP.get(Digits)
    if not symptom:
        return _xml("<Response><Say language=\"hi-IN\">Galat input. Kripya dubara call karein.</Say></Response>")

    patient = _find_patient(db, From)
    log = db.query(IvrCallLog).filter(IvrCallLog.caller_number == From).order_by(IvrCallLog.created_at.desc()).first()
    if log:
        log.symptoms_collected = list(set((log.symptoms_collected or []) + [symptom]))
        db.commit()

    if symptom == "bleeding":
        if patient:
            risk = calculate_risk(["bleeding"], 0, 0, patient.age, patient.pregnancy_week, 0, False)
            s = Symptom(
                patient_id=patient.id,
                symptoms_list=["bleeding"],
                input_type="ivr",
                transcription="IVR bleeding fast-path",
                risk_score=risk["score"],
                risk_level="HIGH",
                primary_reason=risk["primary_reason"],
                timestamp=datetime.utcnow(),
            )
            db.add(s)
            db.commit()
            trigger_alert(
                db=db,
                background_tasks=background_tasks,
                patient_id=patient.id,
                asha_id=patient.asha_id,
                patient_name=patient.name,
                risk_score=risk["score"],
                reason=risk["primary_reason"],
                village=patient.village,
                district=patient.district,
            )
        if log:
            log.risk_result = "HIGH"
            db.commit()

        return _xml(
            """<Response>
  <Say language=\"hi-IN\">Yeh emergency hai. ASHA didi ko abhi bheja ja raha hai. Agar bahut zyada takleef ho toh ek sau aath dial karein.</Say>
</Response>"""
        )

    return _xml(
        f"""<Response>
  <Gather numDigits=\"1\" action=\"/ivr/symptom2\" method=\"POST\">
    <Say language=\"hi-IN\">Kya aapko seene mein dard bhi hai? Haan ke liye 1, Nahi ke liye 2.</Say>
  </Gather>
  <Redirect method=\"POST\">/ivr/calculate?primary={escape(symptom)}</Redirect>
</Response>"""
    )


@router.post("/symptom2")
def symptom2(Digits: str = Form(default="2")):  # noqa: N803
    chest = "chest_pain" if Digits == "1" else ""
    return _xml(
        f"""<Response>
  <Gather numDigits=\"3\" action=\"/ivr/calculate\" method=\"POST\">
    <Say language=\"hi-IN\">Kya aapke paas BP machine hai? Agar hai toh systolic number dabayein, warna 0 dabayein.</Say>
  </Gather>
  <Redirect method=\"POST\">/ivr/calculate?secondary={escape(chest)}</Redirect>
</Response>"""
    )


@router.post("/calculate")
def calculate(
    request: Request,
    background_tasks: BackgroundTasks,
    Digits: str = Form(default="0"),  # noqa: N803
    From: str = Form(default="anonymous"),  # noqa: N803
    db: Session = Depends(get_db),
):
    primary = request.query_params.get("primary", "headache")
    secondary = request.query_params.get("secondary", "")
    symptoms = [s for s in [primary, secondary] if s]
    systolic = int(Digits) if Digits.isdigit() else 0

    patient = _find_patient(db, From)
    if not patient:
        return _xml("<Response><Say language=\"hi-IN\">Aapka number register nahi hai. Kripya ASHA didi se sampark karein.</Say></Response>")

    risk = calculate_risk(symptoms, systolic, 0, patient.age, patient.pregnancy_week, 0, False)
    row = Symptom(
        patient_id=patient.id,
        symptoms_list=symptoms,
        input_type="ivr",
        transcription=f"IVR call by {From}",
        risk_score=risk["score"],
        risk_level=risk["level"],
        primary_reason=risk["primary_reason"],
        timestamp=datetime.utcnow(),
    )
    db.add(row)

    log = db.query(IvrCallLog).filter(IvrCallLog.caller_number == From).order_by(IvrCallLog.created_at.desc()).first()
    if log:
        log.risk_result = risk["level"]

    db.commit()

    if risk["level"] == "HIGH":
        trigger_alert(
            db=db,
            background_tasks=background_tasks,
            patient_id=patient.id,
            asha_id=patient.asha_id,
            patient_name=patient.name,
            risk_score=risk["score"],
            reason=risk["primary_reason"],
            village=patient.village,
            district=patient.district,
        )
        return _xml(
            """<Response>
  <Say language=\"hi-IN\">Aapka risk score zyada hai. Aapki ASHA didi ko abhi alert bheja ja raha hai. Ghabrayein nahi, madad aa rahi hai. Agar aur takleef ho toh ek sau aath dial karein.</Say>
</Response>"""
        )
    if risk["level"] == "MEDIUM":
        return _xml("<Response><Say language=\"hi-IN\">Thodi takleef lag rahi hai. ASHA didi jald aapke paas aayengi. Aaram karein aur paani piyein.</Say></Response>")
    return _xml("<Response><Say language=\"hi-IN\">Sab theek lag raha hai. Apna khayal rakhein. Routine checkup zaroor karwayein.</Say></Response>")


@router.post("/callback-request")
def callback_request(From: str = Form(default="anonymous"), db: Session = Depends(get_db)):  # noqa: N803
    log = db.query(IvrCallLog).filter(IvrCallLog.caller_number == From).order_by(IvrCallLog.created_at.desc()).first()
    if log:
        log.callback_requested = True
        db.commit()
    return _xml("<Response><Say language=\"hi-IN\">ASHA didi jald call karengi.</Say></Response>")


@router.get("/logs")
def logs(db: Session = Depends(get_db)):
    try:
        rows = db.query(IvrCallLog).order_by(IvrCallLog.created_at.desc()).limit(200).all()
        data = [
            {
                "caller_number": _mask(r.caller_number),
                "duration": r.duration_seconds,
                "symptoms_collected": r.symptoms_collected,
                "risk_result": r.risk_result,
                "timestamp": r.created_at.isoformat(),
            }
            for r in rows
        ]
        return success_response({"logs": data})
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Failed to fetch IVR logs: {exc}", 400)
