from functools import lru_cache
import os


class Settings:
    def __init__(self) -> None:
        self.auth_secret = os.getenv("VYANA_AUTH_SECRET", "vyana-care-local-secret")
        self.token_ttl_hours = int(os.getenv("VYANA_TOKEN_TTL_HOURS", "72"))
        self.patient_access_code = os.getenv("VYANA_PATIENT_ACCESS_CODE", "patient-1234")
        self.asha_access_code = os.getenv("VYANA_ASHA_ACCESS_CODE", "asha-1234")
        self.district_access_code = os.getenv("VYANA_DISTRICT_ACCESS_CODE", "district-1234")
        self.admin_access_code = os.getenv("VYANA_ADMIN_ACCESS_CODE", "admin-1234")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()