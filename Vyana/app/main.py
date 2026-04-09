from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.database import Base, engine
from app.routers.auth import router as auth_router
from app.routers.awaaz import router as awaaz_router
from app.routers.alert import router as alert_router
from app.routers.asha import router as asha_router
from app.routers.district import router as district_router
from app.routers.patient import router as patient_router
from app.routers.symptom import router as symptom_router
from app.utils.response import success_response

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vyana Care Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patient_router)
app.include_router(symptom_router)
app.include_router(auth_router)
app.include_router(awaaz_router)
app.include_router(asha_router)
app.include_router(alert_router)
app.include_router(district_router)

Path("uploads").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/health")
def health_check():
    return success_response({"message": "Vyana Care backend is running"})
