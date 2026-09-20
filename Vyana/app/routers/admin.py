from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog
from app.utils.response import success_response

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed")
def trigger_seed(db: Session = Depends(get_db)):
    from seed import run_seed
    try:
        run_seed()
        return success_response({"message": "Database seeded successfully with test patients and ASHA workers"})
    except Exception as exc:
        return {"success": False, "error": f"Seed failed: {exc}"}

