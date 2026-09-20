from fastapi import FastAPI
from fastapi import Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from time import perf_counter
from datetime import datetime
import os

from app.database import Base, engine
from app.routers.abha import router as abha_router
from app.routers.admin import router as admin_router
from app.routers.ambulance import router as ambulance_router
from app.routers.auth import router as auth_router
from app.routers.awaaz import router as awaaz_router
from app.routers.alert import router as alert_router
from app.routers.asha import router as asha_router
from app.routers.district import router as district_router
from app.routers.federated import router as federated_router
from app.routers.hmis import router as hmis_router
from app.routers.ivr import router as ivr_router
from app.routers.knowledge import router as knowledge_router
from app.routers.patient import router as patient_router
from app.routers.scheduler import router as scheduler_router
from app.routers.sos import router as sos_router
from app.routers.sync import router as sync_router
from app.routers.symptom import router as symptom_router
from app.models import Alert, AwaazSubmission, Patient, Symptom
from app.database import SessionLocal
from app.services.scheduler_service import start_scheduler, stop_scheduler
from app.utils.response import success_response

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed database if empty
    try:
        db = SessionLocal()
        if db.query(Patient).count() == 0:
            print("[STARTUP] Empty database detected. Running auto-seed...")
            from seed import run_seed
            run_seed()
            print("[STARTUP] Auto-seed complete!")
        db.close()
    except Exception as e:
        print(f"[STARTUP] Auto-seed check warning: {e}")

    start_scheduler()
    yield
    stop_scheduler()



from app.core.config import settings

app = FastAPI(title="Vyana Care Backend", version="1.0.0", lifespan=lifespan)
APP_STARTED_AT = datetime.utcnow()
API_CALLS_TODAY = {"date": datetime.utcnow().date().isoformat(), "count": 0}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_allowed_origins if settings.all_allowed_origins else ["*"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patient_router)
app.include_router(scheduler_router)
app.include_router(symptom_router)
app.include_router(auth_router)
app.include_router(awaaz_router)
app.include_router(asha_router)
app.include_router(alert_router)
app.include_router(district_router)
app.include_router(sync_router)
app.include_router(ivr_router)
app.include_router(federated_router)
app.include_router(abha_router)
app.include_router(hmis_router)
app.include_router(ambulance_router)
app.include_router(admin_router)
app.include_router(knowledge_router)
app.include_router(sos_router)

Path("uploads").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    elapsed_ms = int((perf_counter() - start) * 1000)
    today = datetime.utcnow().date().isoformat()
    if API_CALLS_TODAY["date"] != today:
        API_CALLS_TODAY["date"] = today
        API_CALLS_TODAY["count"] = 0
    API_CALLS_TODAY["count"] += 1
    print(f"[REQUEST] {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms}ms)")
    return response


@app.get("/health")
def health_check():
    uptime = int((datetime.utcnow() - APP_STARTED_AT).total_seconds())
    twilio_configured = all(
        os.getenv(name, "").strip()
        for name in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER", "TWILIO_TO_NUMBER")
    )
    data = {
        "status": "healthy",
        "database": "connected",
        "groq_api": "available" if os.getenv("GROQ_API_KEY") else "missing_key",
        "gemini_api": "available" if os.getenv("GEMINI_API_KEY") else "missing_key",
        "firebase": "connected" if os.getenv("FIREBASE_CREDENTIALS_JSON") else "not_configured",
        "abha_api": "available" if os.getenv("ABHA_SANDBOX_API_KEY") else "sandbox-mock",
        "twilio_api": "available" if twilio_configured else "missing_key",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "message": "Vyana Care backend is running",
    }
    return success_response(data)


@app.get("/metrics")
def metrics():
    db = SessionLocal()
    try:
        total_patients = db.query(Patient).count()
        total_symptom_reports = db.query(Symptom).count()
        total_high_risk_alerts = db.query(Alert).filter(Alert.risk_level == "HIGH").count()
        total_awaaz_published = db.query(AwaazSubmission).filter(AwaazSubmission.submission_status == "PUBLISHED").count()
        acknowledged = db.query(Alert).filter(Alert.acknowledged.is_(True), Alert.acknowledged_at.is_not(None)).all()
        avg_response = 0
        if acknowledged:
            avg_response = int(sum((a.acknowledged_at - a.created_at).total_seconds() * 1000 for a in acknowledged) / len(acknowledged))

        return success_response(
            {
                "total_patients": total_patients,
                "total_symptom_reports": total_symptom_reports,
                "total_high_risk_alerts": total_high_risk_alerts,
                "total_awaaz_published": total_awaaz_published,
                "avg_response_time_ms": avg_response,
                "api_calls_today": API_CALLS_TODAY["count"],
            }
        )
    finally:
        db.close()
