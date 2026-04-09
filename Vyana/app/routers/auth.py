from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.schemas import AuthLoginRequest
from app.services.auth_service import build_user_payload, create_session, decode_token, verify_access_code
from app.utils.response import success_response

router = APIRouter(prefix="/auth", tags=["auth"])


def get_current_user(authorization: str | None = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header is required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is required")

    payload = decode_token(token)
    return build_user_payload(payload)


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
def logout():
    return success_response({"message": "Logged out successfully"})