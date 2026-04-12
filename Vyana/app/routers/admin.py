from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog
from app.utils.response import success_response

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit-logs")
def audit_logs(limit: int = 200, db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return success_response(
        {
            "logs": [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "user_role": r.user_role,
                    "action": r.action,
                    "resource_type": r.resource_type,
                    "resource_id": r.resource_id,
                    "ip_address": r.ip_address,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in rows
            ]
        }
    )
