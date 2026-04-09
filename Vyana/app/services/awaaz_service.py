from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles
from dotenv import load_dotenv
from fastapi import UploadFile
from groq import Groq
import google.generativeai as genai
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import AwaazReaction, AwaazSubmission, AshaWorker

load_dotenv()

UPLOAD_DIR = Path("uploads") / "awaaz"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".webm", ".ogg", ".m4a"}
ALLOWED_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
}
MAX_FILE_SIZE = 10 * 1024 * 1024
MIN_DURATION_SECONDS = 10
MAX_DURATION_SECONDS = 300

GEMINI_PROMPT = """You are a medical content moderator for a maternal health platform in rural India.

Analyze this audio transcription from a recovered mother sharing her pregnancy experience.

Transcription: {transcription}

Perform these 4 checks and return ONLY JSON:

CHECK 1 — pregnancy_related (boolean):
Is this content about pregnancy, childbirth, maternal health, or related experiences?
Even indirect experiences count as true.
Completely unrelated topics = false.

CHECK 2 — safe_advice (boolean):
Does this audio contain any dangerous medical advice such as:
- Taking medicines without doctor consultation
- Home remedies that could be harmful
- Advice to avoid hospitals or doctors
- Any recommendation that contradicts WHO maternal health guidelines
If dangerous advice found = false.
General experiences without advice = true.

CHECK 3 — distress_detected (boolean):
Does the speaker sound emotionally distressed, traumatized, scared, or in crisis RIGHT NOW?
Past difficult experiences described calmly = false.
Current emotional crisis = true.

CHECK 4 — respectful_content (boolean):
Is the content respectful, non-discriminatory, and appropriate for a health platform?
No offensive language, no misinformation about communities, castes, religions.

CHECK 5 — overall_score (0-100):
Overall quality and helpfulness score.
Consider: clarity, emotional value, relevance, safety, authenticity.

CHECK 6 — summary (string):
One sentence summary of what the mother shared.
Write in English.

CHECK 7 — rejection_reason (string or null):
If any check failed, explain why in Hindi.
If all passed, return null.

CHECK 8 — helpful_topics (array of strings):
What topics does this audio help with?
Choose from: symptoms, nutrition, hospital_visit, emotional_support, delivery_experience, postnatal_care, family_support, medication, warning_signs, exercise

Return ONLY this JSON, nothing else:
{
  pregnancy_related: boolean,
  safe_advice: boolean,
  distress_detected: boolean,
  respectful_content: boolean,
  overall_score: number,
  summary: string,
  rejection_reason: string or null,
  helpful_topics: array
}"""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _audio_url(file_path: str) -> str:
    return "/" + file_path.replace("\\", "/")


def _normalize_topics(topics: Any) -> list[str]:
    if not topics:
        return []
    if isinstance(topics, list):
        return [str(item).strip() for item in topics if str(item).strip()]
    if isinstance(topics, str):
        try:
            parsed = json.loads(topics)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
        return [item.strip() for item in topics.split(",") if item.strip()]
    return []


def _topic_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _extract_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found")

    candidate = match.group(0)
    candidate = re.sub(r"(\{|,\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', candidate)
    candidate = candidate.replace("'", '"')
    return json.loads(candidate)


def _fallback_moderation(transcription: str, language: str | None = None) -> dict:
    text = transcription.lower()
    pregnancy_related = any(
        token in text
        for token in [
            "pregnancy",
            "pregnant",
            "baby",
            "delivery",
            "hospital",
            "mother",
            "bachcha",
            "garbh",
            "mahila",
            "doctor",
        ]
    )
    unsafe = any(token in text for token in ["bina doctor", "home remedy", "dawai mat", "avoid hospital", "nuskha"])
    distress = any(token in text for token in ["bahut ghabra", "panic", "help me", "saans", "crisis", "dar lag", "pareshan"])
    respectful = not any(token in text for token in ["gali", "hate", "beizzati"])

    score = 65
    if pregnancy_related:
        score += 10
    if respectful:
        score += 5
    if distress:
        score -= 15
    if unsafe:
        score -= 40
    if len(transcription.split()) < 12:
        score -= 15
    score = max(0, min(100, score))

    topics = []
    topic_map = {
        "symptoms": ["symptom", "dard", "pain", "headache", "swelling", "bleeding"],
        "nutrition": ["khana", "nutrition", "diet", "food"],
        "hospital_visit": ["hospital", "doctor", "clinic"],
        "emotional_support": ["emotion", "support", "scared", "pareshan"],
        "delivery_experience": ["delivery", "pains", "labor", "labour"],
        "postnatal_care": ["after birth", "postnatal", "delivery ke baad"],
        "family_support": ["family", "husband", "sasural", "ghar"],
        "medication": ["medicine", "tablet", "dawai"],
        "warning_signs": ["bleeding", "fever", "blurred", "swelling", "warning"],
        "exercise": ["walk", "exercise", "move"],
    }
    for topic, keywords in topic_map.items():
        if any(keyword in text for keyword in keywords):
            topics.append(topic)

    summary = transcription.strip().split(".")[0].strip() if transcription.strip() else "Recovered mother shared a pregnancy experience in local mode."
    if not summary:
        summary = "Recovered mother shared a pregnancy experience in local mode."

    rejection_reason = None
    if distress:
        rejection_reason = "Aap thodi pareshan lag rahi hain. ASHA didi se baat karna madadgar ho sakta hai."
    elif not pregnancy_related:
        rejection_reason = "Ye content pregnancy se related nahi lagta."
    elif unsafe:
        rejection_reason = "Is audio mein kuch aisi baatein hain jo doosron ke liye safe nahi hain."
    elif not respectful:
        rejection_reason = "Content platform guidelines ke against hai."
    elif score < 30:
        rejection_reason = "Audio ki quality ya content helpful nahi laga."

    return {
        "pregnancy_related": pregnancy_related,
        "safe_advice": not unsafe,
        "distress_detected": distress,
        "respectful_content": respectful,
        "overall_score": score,
        "summary": summary,
        "rejection_reason": rejection_reason,
        "helpful_topics": topics,
        "language_detected": language or "Hindi",
    }


def _gemini_analyze(transcription: str) -> dict:
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_api_key:
        return _fallback_moderation(transcription)

    genai.configure(api_key=gemini_api_key)
    prompt = GEMINI_PROMPT.format(transcription=transcription)
    model_names = ["gemini-1.5-flash", "models/gemini-1.5-flash", "models/gemini-2.0-flash"]

    last_error: Exception | None = None
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            raw = (getattr(response, "text", "") or "").strip()
            if not raw and getattr(response, "candidates", None):
                chunks = []
                for candidate in response.candidates:
                    content = getattr(candidate, "content", None)
                    if not content:
                        continue
                    for part in getattr(content, "parts", []) or []:
                        text = getattr(part, "text", "")
                        if text:
                            chunks.append(text)
                raw = "\n".join(chunks).strip()
            parsed = _extract_json_object(raw)
            return {
                "pregnancy_related": bool(parsed.get("pregnancy_related", False)),
                "safe_advice": bool(parsed.get("safe_advice", False)),
                "distress_detected": bool(parsed.get("distress_detected", False)),
                "respectful_content": bool(parsed.get("respectful_content", False)),
                "overall_score": int(parsed.get("overall_score", 0) or 0),
                "summary": str(parsed.get("summary", "")).strip() or "Recovered mother shared an audio story.",
                "rejection_reason": parsed.get("rejection_reason"),
                "helpful_topics": _normalize_topics(parsed.get("helpful_topics", [])),
            }
        except Exception as exc:
            last_error = exc
            continue

    print(f"[AWAAZ] Gemini moderation failed, using fallback: {last_error}")
    return _fallback_moderation(transcription)


def _transcribe_with_whisper(audio_path: str) -> tuple[str, str]:
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_api_key:
        raise RuntimeError("GROQ_API_KEY is missing")

    whisper_client = Groq(api_key=groq_api_key)
    with open(audio_path, "rb") as handle:
        response = whisper_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(Path(audio_path).name, handle.read()),
            response_format="verbose_json",
        )

    text = (getattr(response, "text", "") or "").strip()
    language = (getattr(response, "language", "") or "").strip() or "Hindi"
    if not text:
        raise RuntimeError("Whisper transcription returned empty text")
    return text, language


def _set_rejection(submission: AwaazSubmission, reason: str, distress: bool = False) -> None:
    submission.submission_status = "AI_REJECTED"
    submission.ai_rejection_reason = reason
    submission.ai_check_distress_detected = distress


def _run_support_notification(submission: AwaazSubmission) -> None:
    nurse = submission.nurse_id
    if nurse:
        print(
            "[AWAAZ] Distress detected for submission",
            submission.id,
            "-> notify nurse",
            nurse,
        )
    else:
        print(f"[AWAAZ] Distress detected for submission {submission.id}. Nurse notification queued.")


def run_ai_moderation_task(submission_id: int) -> None:
    db = SessionLocal()
    try:
        submission = db.query(AwaazSubmission).filter(AwaazSubmission.id == submission_id).first()
        if not submission:
            return

        if submission.submission_status in {"PUBLISHED", "NURSE_REJECTED"}:
            return

        try:
            transcription, detected_language = _transcribe_with_whisper(submission.audio_file_path)
        except Exception as exc:
            print(f"[AWAAZ] Whisper failed for submission {submission_id}: {exc}")
            transcription = submission.transcription or "Recovered mother shared a community story."
            detected_language = submission.language_detected or "Hindi"

        submission.transcription = transcription
        submission.language_detected = detected_language

        try:
            analysis = _gemini_analyze(transcription)
        except Exception as exc:
            print(f"[AWAAZ] Gemini failed for submission {submission_id}: {exc}")
            analysis = _fallback_moderation(transcription, detected_language)
            submission.submission_status = "PENDING_NURSE"
            submission.ai_analysis_summary = analysis["summary"]
            submission.ai_check_pregnancy_related = analysis["pregnancy_related"]
            submission.ai_check_safe_advice = analysis["safe_advice"]
            submission.ai_check_distress_detected = analysis["distress_detected"]
            submission.ai_check_respectful = analysis["respectful_content"]
            submission.ai_overall_score = analysis["overall_score"]
            submission.helpful_topics = analysis["helpful_topics"]
            submission.ai_rejection_reason = None
            db.commit()
            return

        submission.ai_check_pregnancy_related = analysis["pregnancy_related"]
        submission.ai_check_safe_advice = analysis["safe_advice"]
        submission.ai_check_distress_detected = analysis["distress_detected"]
        submission.ai_check_respectful = analysis["respectful_content"]
        submission.ai_overall_score = analysis["overall_score"]
        submission.ai_analysis_summary = analysis["summary"]
        submission.helpful_topics = analysis["helpful_topics"]
        submission.ai_rejection_reason = analysis.get("rejection_reason")

        if analysis["distress_detected"]:
            _set_rejection(
                submission,
                analysis.get("rejection_reason") or "Hum dekh rahe hain aap thodi pareshan lag rahi hain. ASHA didi se baat karna madadgar ho sakta hai.",
                distress=True,
            )
            _run_support_notification(submission)
        elif not analysis["pregnancy_related"]:
            _set_rejection(submission, analysis.get("rejection_reason") or "Ye content pregnancy se related nahi lagta.")
        elif not analysis["safe_advice"]:
            _set_rejection(submission, analysis.get("rejection_reason") or "Is audio mein kuch aisi baatein hain jo doosron ke liye safe nahi hain.")
        elif not analysis["respectful_content"]:
            _set_rejection(submission, analysis.get("rejection_reason") or "Content platform guidelines ke against hai.")
        elif analysis["overall_score"] < 30:
            _set_rejection(submission, analysis.get("rejection_reason") or "Audio ki quality ya content helpful nahi laga.")
        else:
            submission.submission_status = "PENDING_NURSE"
            submission.ai_rejection_reason = None
            print(f"[AWAAZ] Submission {submission_id} passed AI moderation and is awaiting nurse review")

        db.commit()
    except Exception as exc:
        db.rollback()
        submission = db.query(AwaazSubmission).filter(AwaazSubmission.id == submission_id).first()
        if submission:
            submission.submission_status = "PENDING_NURSE"
            submission.ai_analysis_summary = f"AI moderation unavailable; routed to nurse review. ({exc})"
            submission.ai_rejection_reason = None
            db.commit()
    finally:
        db.close()


async def save_awaaz_upload(
    db: Session,
    audio_file: UploadFile,
    speaker_age: int | None,
    speaker_district: str | None,
    speaker_pregnancy_week_at_time: int | None,
    language: str | None,
    audio_duration_seconds: int,
    topics: Any,
) -> AwaazSubmission:
    if not audio_file.filename:
        raise ValueError("Sirf audio files accept hoti hain")

    ext = Path(audio_file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Sirf audio files accept hoti hain")

    if audio_file.content_type and audio_file.content_type not in ALLOWED_MIME_TYPES and not audio_file.content_type.startswith("audio/"):
        raise ValueError("Sirf audio files accept hoti hain")

    if audio_duration_seconds < MIN_DURATION_SECONDS:
        raise ValueError("Audio bahut chhota hai — kam se kam 10 second bolein")
    if audio_duration_seconds > MAX_DURATION_SECONDS:
        raise ValueError("Audio bahut bada hai — 5 minute se kam rakein")

    contents = await audio_file.read(MAX_FILE_SIZE + 1)
    if len(contents) > MAX_FILE_SIZE:
        raise ValueError("File bahut badi hai — 10MB se kam honi chahiye")

    filename = f"{uuid.uuid4().hex}{ext}"
    relative_path = Path("uploads") / "awaaz" / filename
    absolute_path = Path(relative_path)
    async with aiofiles.open(absolute_path, "wb") as handle:
        await handle.write(contents)

    submission = AwaazSubmission(
        speaker_id=str(uuid.uuid4()),
        speaker_age=speaker_age,
        speaker_district=speaker_district,
        speaker_pregnancy_week_at_time=speaker_pregnancy_week_at_time,
        audio_file_path=str(relative_path).replace("\\", "/"),
        audio_duration_seconds=audio_duration_seconds,
        transcription=None,
        language_detected=language,
        submission_status="PENDING_AI",
        helpful_topics=_normalize_topics(topics),
        play_count=0,
        helpful_count=0,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def serialize_status(submission: AwaazSubmission) -> dict[str, Any]:
    message_map = {
        "PENDING_AI": "Aapki awaaz review ho rahi hai",
        "PENDING_NURSE": "Aapki awaaz AI se pass ho gayi, ab nurse review karengi",
        "PUBLISHED": "Aapki awaaz publish ho gayi!",
        "NURSE_REJECTED": "Nurse review mein is audio ko approve nahi kiya gaya.",
        "AI_REJECTED": "Aapki awaaz is baar publish nahi ho saki.",
    }
    if submission.submission_status == "AI_REJECTED" and submission.ai_check_distress_detected:
        return {
            "status": submission.submission_status,
            "message": "Hum dekh rahe hain aap thodi pareshan lag rahi hain. Kya ASHA didi se baat karni hai?",
            "reason": submission.ai_rejection_reason,
            "distress_detected": True,
        }
    return {
        "status": submission.submission_status,
        "message": message_map.get(submission.submission_status, "Awaaz status update ho gaya hai."),
        "reason": submission.ai_rejection_reason or submission.nurse_rejection_reason,
        "distress_detected": bool(submission.ai_check_distress_detected),
    }


def get_submission_or_error(db: Session, submission_id: int) -> AwaazSubmission:
    submission = db.query(AwaazSubmission).filter(AwaazSubmission.id == submission_id).first()
    if not submission:
        raise ValueError("Submission not found")
    return submission


def build_feed_item(submission: AwaazSubmission) -> dict[str, Any]:
    return {
        "id": submission.id,
        "speaker_age": submission.speaker_age,
        "speaker_district": submission.speaker_district,
        "speaker_pregnancy_week_at_time": submission.speaker_pregnancy_week_at_time,
        "audio_duration_seconds": submission.audio_duration_seconds,
        "transcription": submission.transcription,
        "language_detected": submission.language_detected,
        "submission_status": submission.submission_status,
        "ai_analysis_summary": submission.ai_analysis_summary,
        "helpful_topics": submission.helpful_topics or [],
        "audio_file_url": _audio_url(submission.audio_file_path),
        "play_count": submission.play_count,
        "helpful_count": submission.helpful_count,
        "published_at": submission.published_at,
    }


def build_nurse_item(submission: AwaazSubmission) -> dict[str, Any]:
    payload = build_feed_item(submission)
    payload.update(
        {
            "ai_check_pregnancy_related": submission.ai_check_pregnancy_related,
            "ai_check_safe_advice": submission.ai_check_safe_advice,
            "ai_check_distress_detected": submission.ai_check_distress_detected,
            "ai_check_respectful": submission.ai_check_respectful,
            "ai_overall_score": submission.ai_overall_score,
            "created_at": submission.created_at,
        }
    )
    return payload


def list_feed(db: Session, language: str | None, topic: str | None, sort: str, page: int, per_page: int = 10) -> dict[str, Any]:
    query = db.query(AwaazSubmission).filter(AwaazSubmission.submission_status == "PUBLISHED")
    if language and language != "All":
        query = query.filter(AwaazSubmission.language_detected == language)

    submissions = query.all()
    if topic and topic != "All":
        topic_normalized = _topic_key(topic)
        submissions = [
            s
            for s in submissions
            if any(_topic_key(str(item)) == topic_normalized for item in (s.helpful_topics or []))
        ]

    if sort == "most_played":
        submissions.sort(key=lambda item: item.play_count, reverse=True)
    elif sort == "most_helpful":
        submissions.sort(key=lambda item: item.helpful_count, reverse=True)
    else:
        submissions.sort(key=lambda item: item.published_at or item.created_at, reverse=True)

    total = len(submissions)
    start = max(0, (page - 1) * per_page)
    end = start + per_page
    page_items = submissions[start:end]

    return {
        "items": [build_feed_item(item) for item in page_items],
        "page": page,
        "per_page": per_page,
        "has_more": end < total,
        "total": total,
    }


def list_pending_for_nurse(db: Session) -> list[dict[str, Any]]:
    submissions = (
        db.query(AwaazSubmission)
        .filter(AwaazSubmission.submission_status == "PENDING_NURSE")
        .order_by(desc(AwaazSubmission.created_at))
        .all()
    )
    return [build_nurse_item(item) for item in submissions]


def review_submission(db: Session, submission_id: int, nurse_id: int, decision: str, rejection_reason: str | None = None) -> AwaazSubmission:
    submission = get_submission_or_error(db, submission_id)

    if decision == "rejected" and not rejection_reason:
        raise ValueError("Rejection reason is required")

    submission.nurse_id = nurse_id
    submission.nurse_decision = decision
    submission.nurse_reviewed_at = _utc_now()
    if decision == "approved":
        submission.submission_status = "PUBLISHED"
        submission.published_at = _utc_now()
        submission.nurse_rejection_reason = None
    else:
        submission.submission_status = "NURSE_REJECTED"
        submission.nurse_rejection_reason = rejection_reason

    db.commit()
    db.refresh(submission)
    return submission


def react_to_audio(db: Session, audio_id: int, reaction_type: str) -> dict[str, Any]:
    submission = get_submission_or_error(db, audio_id)
    reaction = AwaazReaction(audio_id=audio_id, reaction_type=reaction_type)
    db.add(reaction)
    if reaction_type in {"helpful", "saved"}:
        submission.helpful_count += 1
    db.commit()
    db.refresh(submission)
    return {
        "audio_id": audio_id,
        "play_count": submission.play_count,
        "helpful_count": submission.helpful_count,
        "reaction_type": reaction_type,
    }


def increment_play_count(db: Session, audio_id: int) -> dict[str, Any]:
    submission = get_submission_or_error(db, audio_id)
    submission.play_count += 1
    db.commit()
    db.refresh(submission)
    return {
        "audio_id": audio_id,
        "play_count": submission.play_count,
    }
