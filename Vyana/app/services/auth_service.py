from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings


ROLE_ACCESS_CODES = {
    "patient": settings.patient_access_code,
    "asha": settings.asha_access_code,
    "district": settings.district_access_code,
    "admin": settings.admin_access_code,
}


@dataclass(frozen=True)
class AuthSession:
    role: str
    display_name: str
    issued_at: datetime
    expires_at: datetime
    token: str


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def _sign(payload_part: str) -> str:
    signature = hmac.new(settings.auth_secret.encode("utf-8"), payload_part.encode("utf-8"), hashlib.sha256).digest()
    return _b64encode(signature)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_session(role: str, display_name: str) -> AuthSession:
    issued_at = _now()
    expires_at = issued_at + timedelta(hours=settings.token_ttl_hours)
    header = {"alg": "HS256", "typ": "VYANA"}
    payload = {
        "role": role,
        "display_name": display_name,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    header_part = _b64encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_part = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature_part = _sign(f"{header_part}.{payload_part}")
    token = f"{header_part}.{payload_part}.{signature_part}"
    return AuthSession(role=role, display_name=display_name, issued_at=issued_at, expires_at=expires_at, token=token)


def verify_access_code(role: str, access_code: str) -> str:
    expected = ROLE_ACCESS_CODES.get(role)
    if not expected or not hmac.compare_digest(expected, access_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access code")

    role_titles = {
        "patient": "Patient User",
        "asha": "ASHA Worker",
        "district": "District Officer",
        "admin": "Vyana Admin",
    }
    return role_titles[role]


def decode_token(token: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    expected_signature = _sign(f"{header_part}.{payload_part}")
    if not hmac.compare_digest(expected_signature, signature_part):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")

    try:
        payload = json.loads(_b64decode(payload_part))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from exc

    exp = int(payload.get("exp", 0))
    if exp and _now().timestamp() > exp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    return payload


def build_user_payload(token_payload: dict[str, Any]) -> dict[str, Any]:
    issued_at = datetime.fromtimestamp(int(token_payload["iat"]), tz=timezone.utc)
    expires_at = datetime.fromtimestamp(int(token_payload["exp"]), tz=timezone.utc)
    return {
        "role": token_payload["role"],
        "display_name": token_payload["display_name"],
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
    }


def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def create_refresh_token(phone: str, role: str, days: int = 30) -> tuple[str, datetime]:
    issued_at = _now()
    expires_at = issued_at + timedelta(days=days)
    raw = f"{phone}:{role}:{int(issued_at.timestamp())}:{secrets.token_urlsafe(24)}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    token = _b64encode(digest.encode("utf-8"))
    return token, expires_at