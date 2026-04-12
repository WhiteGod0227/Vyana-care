from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AmbulanceDispatch
from app.schemas import AmbulanceDispatchRequest
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/ambulance", tags=["ambulance"])


def _mask(phone: str) -> str:
    return f"{phone[:4]}XXXXXX" if len(phone) >= 4 else "XXXXXX"


@router.post("/dispatch")
def dispatch(payload: AmbulanceDispatchRequest, db: Session = Depends(get_db)):
    row = AmbulanceDispatch(
        patient_name=payload.patient_name,
        village=payload.village,
        district=payload.district,
        phone_masked=_mask(payload.phone),
        emergency_type=payload.emergency_type,
        gps_lat=payload.gps_lat,
        gps_lng=payload.gps_lng,
        eta_minutes=23,
        status="dispatched",
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    print(f"[108] Ambulance dispatched for {payload.patient_name} at {payload.village}, {payload.district}")
    return success_response(
        {
            "dispatch_id": row.id,
            "status": "dispatched",
            "eta_minutes": row.eta_minutes,
            "ambulance_id": "RJ-108-047",
            "driver_name": "Ramu Lal",
            "driver_phone": "9876XXXXXX",
        }
    )


@router.get("/track/{dispatch_id}")
def track(dispatch_id: int, db: Session = Depends(get_db)):
    row = db.query(AmbulanceDispatch).filter(AmbulanceDispatch.id == dispatch_id).first()
    if not row:
        return error_response("Dispatch not found", 404)

    elapsed = int((datetime.utcnow() - row.created_at).total_seconds() // 30)
    eta = max(1, row.eta_minutes - elapsed)

    start_lat = 26.23
    start_lng = 73.02
    end_lat = row.gps_lat if row.gps_lat is not None else 25.75
    end_lng = row.gps_lng if row.gps_lng is not None else 71.38

    t = min(1.0, elapsed / max(row.eta_minutes, 1))
    lat = start_lat + (end_lat - start_lat) * t
    lng = start_lng + (end_lng - start_lng) * t

    return success_response({"dispatch_id": row.id, "status": row.status, "eta_minutes": eta, "gps_lat": round(lat, 6), "gps_lng": round(lng, 6)})


@router.get("/history")
def history(district: str | None = None, db: Session = Depends(get_db)):
    query = db.query(AmbulanceDispatch).order_by(AmbulanceDispatch.created_at.desc())
    if district:
        query = query.filter(AmbulanceDispatch.district.ilike(district))
    rows = query.limit(200).all()
    return success_response(
        {
            "dispatches": [
                {
                    "dispatch_id": r.id,
                    "patient_name": "Anonymous",
                    "village": r.village,
                    "district": r.district,
                    "status": r.status,
                    "eta_minutes": r.eta_minutes,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ]
        }
    )
