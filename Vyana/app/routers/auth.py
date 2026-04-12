from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JwtBlacklist, OtpSession, RefreshToken
from app.schemas import AuthLoginRequest, RefreshTokenPayload, RequestOtpPayload, VerifyOtpPayload
from app.services.auth_service import (
    build_user_payload,
    create_refresh_token,
    create_session,
    decode_token,
    generate_otp,
    verify_access_code,
)
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/auth", tags=["auth"])
LOGIN_ATTEMPTS: dict[str, list[datetime]] = {}
LOCKOUTS: dict[str, datetime] = {}


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header is required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is required")

    blacklisted = db.query(JwtBlacklist).filter(JwtBlacklist.token == token).first()
    if blacklisted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalidated")

    payload = decode_token(token)
    return build_user_payload(payload)


def _rate_limited(phone: str) -> bool:
    now = datetime.utcnow()
    key = phone.strip()
    if key in LOCKOUTS and LOCKOUTS[key] > now:
        return True

    attempts = [x for x in LOGIN_ATTEMPTS.get(key, []) if (now - x).total_seconds() <= 3600]
    LOGIN_ATTEMPTS[key] = attempts
    if len(attempts) >= 5:
        LOCKOUTS[key] = now + timedelta(minutes=15)
        return True
    return False


def _record_failure(phone: str) -> None:
    LOGIN_ATTEMPTS.setdefault(phone.strip(), []).append(datetime.utcnow())


@router.post("/login")
def login(payload: AuthLoginRequest):
    display_name = payload.display_name or verify_access_code(payload.role, payload.access_code)
    if payload.display_name:
        verify_access_code(payload.role, payload.access_code)

    session = create_session(payload.role, display_name)
    return success_response(
        {
            "token": session.token,
            "user": {
                "role": session.role,
                "display_name": session.display_name,
                "issued_at": session.issued_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
            },
        }
    )


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return success_response({"user": current_user})


@router.post("/logout")
def logout(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            db.add(JwtBlacklist(token=token, expires_at=datetime.utcnow() + timedelta(hours=8)))
            db.query(RefreshToken).filter(RefreshToken.token == token).update({"revoked": True})
            db.commit()
    return success_response({"message": "Logged out successfully"})


@router.post("/request-otp")
def request_otp(payload: RequestOtpPayload, db: Session = Depends(get_db)):
    if _rate_limited(payload.phone):
        return error_response("Invalid phone or OTP", 429)

    code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    row = OtpSession(phone=payload.phone, role=payload.role, otp_code=code, expires_at=expires_at, attempts=0, verified=False)
    db.add(row)
    db.commit()

    print(f"[AUTH] OTP sent to {payload.phone}: {code}")
    return success_response({"otp_sent": True})


@router.post("/verify-otp")
def verify_otp(payload: VerifyOtpPayload, db: Session = Depends(get_db)):
    if _rate_limited(payload.phone):
        return error_response("Invalid phone or OTP", 429)

    row = (
        db.query(OtpSession)
        .filter(OtpSession.phone == payload.phone, OtpSession.role == payload.role, OtpSession.verified.is_(False))
        .order_by(OtpSession.created_at.desc())
        .first()
    )
    if not row or row.expires_at < datetime.utcnow() or row.otp_code != payload.otp:
        _record_failure(payload.phone)
        return error_response("Invalid phone or OTP", 401)

    row.verified = True
    access = create_session(payload.role, f"{payload.role.title()} User")
    refresh_token, refresh_expiry = create_refresh_token(payload.phone, payload.role, days=30)
    db.add(RefreshToken(token=refresh_token, phone=payload.phone, role=payload.role, expires_at=refresh_expiry, revoked=False))
    db.commit()

    return success_response(
        {
            "access_token": access.token,
            "refresh_token": refresh_token,
            "role": payload.role,
            "user_id": payload.phone,
            "expires_at": access.expires_at.isoformat(),
        }
    )


@router.post("/refresh")
def refresh(payload: RefreshTokenPayload, db: Session = Depends(get_db)):
    row = db.query(RefreshToken).filter(RefreshToken.token == payload.refresh_token, RefreshToken.revoked.is_(False)).first()
    if not row or row.expires_at < datetime.utcnow():
        return error_response("Invalid refresh token", 401)

    access = create_session(row.role, f"{row.role.title()} User")
    return success_response({"access_token": access.token, "expires_at": access.expires_at.isoformat()})