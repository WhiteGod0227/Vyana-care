from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AwaazNurseReviewRequest, AwaazReactionRequest
from app.services.awaaz_service import (
    build_feed_item,
    build_nurse_item,
    get_submission_or_error,
    increment_play_count,
    list_feed,
    list_pending_for_nurse,
    react_to_audio,
    review_submission,
    run_ai_moderation_task,
    save_awaaz_upload,
    serialize_status,
)
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/awaaz", tags=["awaaz"])


@router.post("/upload")
async def upload_awaaz(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    speaker_age: int | None = Form(None),
    speaker_district: str | None = Form(None),
    pregnancy_week_at_time: int | None = Form(None),
    language: str | None = Form(None),
    audio_duration_seconds: int = Form(...),
    topics: str | None = Form(None),
    db: Session = Depends(get_db),
):
    try:
        submission = await save_awaaz_upload(
            db=db,
            audio_file=audio_file,
            speaker_age=speaker_age,
            speaker_district=speaker_district,
            speaker_pregnancy_week_at_time=pregnancy_week_at_time,
            language=language,
            audio_duration_seconds=audio_duration_seconds,
            topics=topics,
        )
        background_tasks.add_task(run_ai_moderation_task, submission.id)
        return success_response(
            {
                "submission_id": submission.id,
                "status": "processing",
                "message": "Aapki awaaz review ho rahi hai",
            }
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response(f"Upload failed: {exc}", 400)


@router.post("/run_ai_moderation/{submission_id}")
def run_ai_moderation(submission_id: int):
    try:
        run_ai_moderation_task(submission_id)
        return success_response({"submission_id": submission_id, "status": "completed"})
    except Exception as exc:
        return error_response(f"Moderation failed: {exc}", 400)


@router.get("/status/{submission_id}")
def get_status(submission_id: int, db: Session = Depends(get_db)):
    try:
        submission = get_submission_or_error(db, submission_id)
        return success_response(serialize_status(submission))
    except ValueError as exc:
        return error_response(str(exc), 404)


@router.get("/nurse/pending")
def nurse_pending(db: Session = Depends(get_db)):
    try:
        return success_response({"submissions": list_pending_for_nurse(db)})
    except Exception as exc:
        return error_response(f"Failed to fetch pending submissions: {exc}", 400)


@router.post("/nurse/review/{submission_id}")
def nurse_review(submission_id: int, payload: AwaazNurseReviewRequest, db: Session = Depends(get_db)):
    try:
        submission = review_submission(
            db=db,
            submission_id=submission_id,
            nurse_id=payload.nurse_id,
            decision=payload.decision,
            rejection_reason=payload.rejection_reason,
        )
        return success_response(
            {
                "submission_id": submission.id,
                "status": submission.submission_status,
                "published_at": submission.published_at,
            }
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response(f"Review failed: {exc}", 400)


@router.get("/feed")
def feed(
    language: str | None = None,
    topic: str | None = None,
    sort: str = "newest",
    page: int = 1,
    db: Session = Depends(get_db),
):
    try:
        return success_response(list_feed(db, language, topic, sort, page))
    except Exception as exc:
        return error_response(f"Failed to fetch feed: {exc}", 400)


@router.post("/react/{audio_id}")
def react(audio_id: int, payload: AwaazReactionRequest, db: Session = Depends(get_db)):
    try:
        return success_response(react_to_audio(db, audio_id, payload.reaction_type))
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception as exc:
        db.rollback()
        return error_response(f"Reaction failed: {exc}", 400)


@router.post("/play/{audio_id}")
def play(audio_id: int, db: Session = Depends(get_db)):
    try:
        return success_response(increment_play_count(db, audio_id))
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception as exc:
        db.rollback()
        return error_response(f"Play tracking failed: {exc}", 400)
