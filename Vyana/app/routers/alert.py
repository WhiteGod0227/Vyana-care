from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.alert_service import acknowledge_alert
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/alert", tags=["alert"])


def _acknowledge_impl(alert_id: int, db: Session):
    try:
        minutes = acknowledge_alert(db, alert_id)
        return success_response({"response_time_minutes": minutes})
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception as exc:
        db.rollback()
        return error_response(f"Failed to acknowledge alert: {exc}", 400)


@router.post("/acknowledge/{alert_id}")
def acknowledge_legacy(alert_id: int, db: Session = Depends(get_db)):
    return _acknowledge_impl(alert_id, db)


@router.post("/{alert_id}/acknowledge")
def acknowledge_modern(alert_id: int, db: Session = Depends(get_db)):
    return _acknowledge_impl(alert_id, db)
