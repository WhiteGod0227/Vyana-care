from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AshaWorker(Base):
    __tablename__ = "asha_workers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    device_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    area_pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    patients = relationship("Patient", back_populates="asha_worker")
    alerts = relationship("Alert", back_populates="asha_worker")
    checkups = relationship("Checkup", back_populates="asha_worker")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    village: Mapped[str] = mapped_column(String(120), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    pregnancy_week: Mapped[int] = mapped_column(Integer, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    asha_id: Mapped[int] = mapped_column(ForeignKey("asha_workers.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    asha_worker = relationship("AshaWorker", back_populates="patients")
    symptoms = relationship("Symptom", back_populates="patient")
    alerts = relationship("Alert", back_populates="patient")
    checkups = relationship("Checkup", back_populates="patient")


class Symptom(Base):
    __tablename__ = "symptoms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    symptoms_list: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    input_type: Mapped[str] = mapped_column(String(20), nullable=False)
    transcription: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    primary_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="symptoms")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    asha_id: Mapped[int] = mapped_column(ForeignKey("asha_workers.id"), nullable=False, index=True)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="alerts")
    asha_worker = relationship("AshaWorker", back_populates="alerts")


class Checkup(Base):
    __tablename__ = "checkups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    asha_id: Mapped[int] = mapped_column(ForeignKey("asha_workers.id"), nullable=False)
    bp_systolic: Mapped[int] = mapped_column(Integer, nullable=False)
    bp_diastolic: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_visit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="checkups")
    asha_worker = relationship("AshaWorker", back_populates="checkups")


class AwaazSubmission(Base):
    __tablename__ = "awaaz_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    speaker_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    speaker_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    speaker_district: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    speaker_pregnancy_week_at_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    audio_file_path: Mapped[str] = mapped_column(Text, nullable=False)
    audio_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    transcription: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language_detected: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    submission_status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="PENDING_AI")
    ai_check_pregnancy_related: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    ai_check_safe_advice: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    ai_check_distress_detected: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    ai_check_respectful: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    ai_overall_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    ai_rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_analysis_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    helpful_topics: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    nurse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("asha_workers.id"), nullable=True)
    nurse_decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nurse_rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nurse_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    reactions = relationship("AwaazReaction", back_populates="submission", cascade="all, delete-orphan")


class AwaazReaction(Base):
    __tablename__ = "awaaz_reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    audio_id: Mapped[int] = mapped_column(ForeignKey("awaaz_submissions.id"), nullable=False, index=True)
    reaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    submission = relationship("AwaazSubmission", back_populates="reactions")
