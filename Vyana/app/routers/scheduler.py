from fastapi import APIRouter

from app.services.scheduler_service import predictive_alerts_job


router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.post("/run-now")
async def run_scheduler_now():
    await predictive_alerts_job()
    return {"success": True, "message": "Alerts checked"}