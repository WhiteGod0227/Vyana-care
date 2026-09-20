import json
import os
import re
from tempfile import NamedTemporaryFile

from dotenv import load_dotenv
from fastapi import UploadFile
import google.generativeai as genai
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = """You are a medical symptom extractor for pregnant women 
in rural India. From the given text (Hindi or English), 
extract symptoms and map them ONLY to this list:
headache, swelling, blurred_vision, bleeding, fever, 
reduced_fetal_movement, chest_pain, difficulty_breathing,
abdominal_pain, fatigue, nausea, dizziness.

Rules:
- If symptom is not exact match, map to closest one
- pait bhaari = abdominal_pain
- neend nahi = fatigue
- chakkar = dizziness
- ulti = nausea
- aankhon ke aage andhera = blurred_vision
- If no symptoms found, return empty array

Return ONLY a JSON object, nothing else:
{symptoms: ['headache', 'swelling'], 
 confidence: 'high/medium/low',
 original_complaints: 'one line summary in English'}"""

KEYWORD_SYMPTOM_MAP = {
    "sir dard": "headache",
    "headache": "headache",
    "sujan": "swelling",
    "swelling": "swelling",
    "aankhon": "blurred_vision",
    "andhera": "blurred_vision",
    "blurred": "blurred_vision",
    "khoon": "bleeding",
    "bleeding": "bleeding",
    "bukhar": "fever",
    "fever": "fever",
    "bachcha kam hil": "reduced_fetal_movement",
    "reduced fetal": "reduced_fetal_movement",
    "seene": "chest_pain",
    "chest pain": "chest_pain",
    "saans": "difficulty_breathing",
    "breathing": "difficulty_breathing",
    "pet dard": "abdominal_pain",
    "abdominal": "abdominal_pain",
    "thakaan": "fatigue",
    "fatigue": "fatigue",
    "ulti": "nausea",
    "nausea": "nausea",
    "chakkar": "dizziness",
    "dizziness": "dizziness",
}


def _extract_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found")

    candidate = match.group(0)
    candidate = re.sub(r"(\{|,\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\\1"\\2":', candidate)
    candidate = candidate.replace("'", '"')
    return json.loads(candidate)


def _extract_symptoms_from_keywords(transcription_text: str) -> dict:
    text = transcription_text.lower()
    detected = []
    for keyword, symptom in KEYWORD_SYMPTOM_MAP.items():
        if keyword in text and symptom not in detected:
            detected.append(symptom)

    return {
        "symptoms": detected,
        "confidence": "medium" if detected else "low",
        "original_complaints": transcription_text[:140],
        "gemini_json_error": True,
    }


def extract_symptoms_from_text(transcription_text: str, gemini_api_key: str) -> dict:
    genai.configure(api_key=gemini_api_key)

    model_names = [
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-001",
        "models/gemini-flash-latest",
        "gemini-1.5-flash",
        "models/gemini-1.5-flash",
    ]

    full_prompt = f"{SYSTEM_PROMPT}\n\nInput text:\n{transcription_text}"

    gemini_error = False
    parsed: dict = {}
    for attempt in range(2):
        try:
            response = None
            last_error: Exception | None = None
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(
                        full_prompt,
                        generation_config={"response_mime_type": "application/json"},
                    )
                    break
                except Exception as inner_exc:
                    last_error = inner_exc
                    continue

            if response is None:
                raise RuntimeError(f"Gemini request failed for all model options: {last_error}")

            raw_content = (getattr(response, "text", "") or "").strip()
            if not raw_content and getattr(response, "candidates", None):
                raw_chunks = []
                for candidate in response.candidates:
                    content = getattr(candidate, "content", None)
                    if not content:
                        continue
                    for part in getattr(content, "parts", []) or []:
                        text = getattr(part, "text", "")
                        if text:
                            raw_chunks.append(text)
                raw_content = "\n".join(raw_chunks).strip()

            parsed = _extract_json_object(raw_content)
            break
        except Exception:
            if attempt == 1:
                return _extract_symptoms_from_keywords(transcription_text)

    symptoms = parsed.get("symptoms", [])
    confidence = parsed.get("confidence", "low")
    original_complaints = parsed.get("original_complaints", "")

    if not isinstance(symptoms, list):
        symptoms = []

    print(f"[GEMINI] Symptoms extracted: {symptoms}")

    return {
        "symptoms": symptoms,
        "confidence": confidence,
        "original_complaints": original_complaints,
        "gemini_json_error": gemini_error,
    }


def process_voice(audio_file: UploadFile) -> dict:
    from app.core.config import settings

    groq_api_key = settings.groq_api_key
    gemini_api_key = settings.gemini_api_key

    if not groq_api_key:
        raise RuntimeError("GROQ_API_KEY is missing in .env")
    if not gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing in .env")

    whisper_client = Groq(api_key=groq_api_key)

    with NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        temp_path = tmp.name
        tmp.write(audio_file.file.read())


    try:
        with open(temp_path, "rb") as f:
            transcription_response = whisper_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=(audio_file.filename or "audio.wav", f.read()),
                response_format="json",
            )
        transcription_text = (transcription_response.text or "").strip()
        print(f"[WHISPER] Transcription complete: {transcription_text}")
    except Exception as exc:
        raise RuntimeError(f"Whisper processing failed: {exc}") from exc
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    gemini_data = extract_symptoms_from_text(transcription_text, gemini_api_key)

    return {
        "transcription": transcription_text,
        "symptoms": gemini_data["symptoms"],
        "confidence": gemini_data["confidence"],
        "original_complaints": gemini_data["original_complaints"],
        "gemini_json_error": gemini_data["gemini_json_error"],
    }
