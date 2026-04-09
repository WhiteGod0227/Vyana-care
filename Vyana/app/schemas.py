from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class AuthLoginRequest(BaseModel):
    role: Literal["patient", "asha", "district", "admin"]
    access_code: str
    display_name: str | None = None


class AuthUser(BaseModel):
    role: str
    display_name: str
    issued_at: str
    expires_at: str


class AuthTokenResponse(BaseModel):
    token: str
    user: AuthUser


class PatientRegisterRequest(BaseModel):
    name: str
    age: int = Field(ge=12, le=60)
    village: str
    district: str
    pregnancy_week: int = Field(ge=1, le=45)
    phone_number: str
    asha_id: int


class SymptomTextRequest(BaseModel):
    patient_id: int
    symptoms: list[str]
    bp_systolic: int = 0
    bp_diastolic: int = 0
    age: int
    pregnancy_week: int
    days_since_last_checkup: int = 0
    previous_complications: bool = False


class CheckupRecordRequest(BaseModel):
    patient_id: int
    asha_id: int
    bp_systolic: int
    bp_diastolic: int
    weight_kg: int
    notes: str | None = None
    next_visit_date: date | None = None


class SymptomView(BaseModel):
    id: int
    symptoms_list: list[str]
    input_type: str
    transcription: str | None
    risk_score: int
    risk_level: str
    primary_reason: str
    timestamp: datetime

    class Config:
        from_attributes = True


class AwaazUploadResponse(BaseModel):
    submission_id: int
    status: str
    message: str


class AwaazStatusResponse(BaseModel):
    status: str
    message: str
    reason: str | None = None
    distress_detected: bool = False


class AwaazNurseReviewRequest(BaseModel):
    nurse_id: int
    decision: str = Field(pattern="^(approved|rejected)$")
    rejection_reason: str | None = None


class AwaazReactionRequest(BaseModel):
    reaction_type: str = Field(pattern="^(helpful|not_helpful|saved)$")


class AwaazFeedItem(BaseModel):
    id: int
    speaker_age: int | None = None
    speaker_district: str | None = None
    speaker_pregnancy_week_at_time: int | None = None
    audio_duration_seconds: int
    transcription: str | None = None
    language_detected: str | None = None
    submission_status: str
    ai_analysis_summary: str | None = None
    helpful_topics: list[str] = Field(default_factory=list)
    audio_file_url: str
    play_count: int
    helpful_count: int
    published_at: datetime | None = None

    class Config:
        from_attributes = True


class AwaazNurseItem(BaseModel):
    id: int
    speaker_age: int | None = None
    speaker_district: str | None = None
    speaker_pregnancy_week_at_time: int | None = None
    audio_duration_seconds: int
    transcription: str | None = None
    language_detected: str | None = None
    ai_check_pregnancy_related: bool | None = None
    ai_check_safe_advice: bool | None = None
    ai_check_distress_detected: bool | None = None
    ai_check_respectful: bool | None = None
    ai_overall_score: int | None = None
    ai_analysis_summary: str | None = None
    helpful_topics: list[str] = Field(default_factory=list)
    audio_file_url: str
    created_at: datetime

    class Config:
        from_attributes = True
