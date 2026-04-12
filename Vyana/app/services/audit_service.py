from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit_log(
    db: Session,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    user_id: str | None = None,
    user_role: str | None = None,
    ip_address: str | None = None,
) -> None:
    row = AuditLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        timestamp=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
