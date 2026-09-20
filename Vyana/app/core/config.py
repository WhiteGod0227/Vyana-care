from functools import lru_cache
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env at project root
project_root = Path(__file__).resolve().parents[2]
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings:
    def __init__(self) -> None:
        # 1. Database Configuration
        self.database_url: str = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "sqlite:///./vyana.db"
        self.postgres_url: str = os.getenv("POSTGRES_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/vyana_care")
        self.sqlite_fallback_url: str = os.getenv("SQLITE_FALLBACK_URL", "sqlite:///./vyana.db")

        # 2. AI & Speech-to-Text Services
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model_name: str = os.getenv("GEMINI_MODEL_NAME", "models/gemini-2.5-flash").strip()

        # 3. Telephony & IVR (Twilio)
        self.twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        self.twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        self.twilio_from_number: str = os.getenv("TWILIO_FROM_NUMBER", "").strip()
        self.twilio_to_number: str = os.getenv("TWILIO_TO_NUMBER", "").strip()
        self.twilio_webhook_url: str = os.getenv("TWILIO_WEBHOOK_URL", "").strip()

        # 4. Emergency Hotlines & Dispatch Contacts
        self.emergency_ambulance_number: str = os.getenv("EMERGENCY_AMBULANCE_NUMBER", "108").strip()
        self.emergency_asha_phone: str = os.getenv("EMERGENCY_ASHA_PHONE", "9876543210").strip()
        self.emergency_phc_phone: str = os.getenv("EMERGENCY_PHC_PHONE", "9000010001").strip()
        self.default_driver_phone: str = os.getenv("DEFAULT_DRIVER_PHONE", "9876543210").strip()

        # 5. Push Notifications (Firebase Admin SDK)
        self.firebase_credentials_json: str = os.getenv("FIREBASE_CREDENTIALS_JSON", "./vyana-care-firebase-adminsdk-fbsvc-c55b228241.json").strip()

        # 6. Government Integration (ABHA Sandbox)
        self.abha_sandbox_api_key: str = os.getenv("ABHA_SANDBOX_API_KEY", "").strip()
        self.abha_base_url: str = os.getenv("ABHA_BASE_URL", "https://dev.abdm.gov.in/gateway/v0.5").strip()

        # 7. Security, Auth & Escalation Timings
        self.auth_secret: str = os.getenv("VYANA_AUTH_SECRET") or os.getenv("JWT_SECRET_KEY") or "vyana-care-local-secret"
        self.jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "vyana-care-jwt-local-secret")
        self.jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.token_ttl_hours: int = int(os.getenv("VYANA_TOKEN_TTL_HOURS", "72"))
        self.demo_escalation_seconds: int = int(os.getenv("DEMO_ESCALATION_SECONDS", "15"))

        # Access Codes for Demo/Role Authentication
        self.patient_access_code: str = os.getenv("VYANA_PATIENT_ACCESS_CODE", "patient-1234")
        self.asha_access_code: str = os.getenv("VYANA_ASHA_ACCESS_CODE", "asha-1234")
        self.district_access_code: str = os.getenv("VYANA_DISTRICT_ACCESS_CODE", "district-1234")
        self.admin_access_code: str = os.getenv("VYANA_ADMIN_ACCESS_CODE", "admin-1234")

        # 8. CORS & Origin Settings
        allowed_origins_env = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
        frontend_url_env = [os.getenv("FRONTEND_URL").strip()] if os.getenv("FRONTEND_URL") else []
        default_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
        self.all_allowed_origins = list(set(default_origins + allowed_origins_env + frontend_url_env))

    def twilio_is_configured(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number)

    def gemini_is_configured(self) -> bool:
        return bool(self.gemini_api_key)

    def groq_is_configured(self) -> bool:
        return bool(self.groq_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()