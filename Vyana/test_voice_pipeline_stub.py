import io
import os
from unittest.mock import patch

from fastapi import UploadFile

from app.services.risk_model import calculate_risk
from app.services.voice_service import process_voice


class FakeTranscriptionResponse:
    text = "Mujhe sir dard ho raha hai aur pair mein sujan hai"


class FakeGroqWhisperAPI:
    class Transcriptions:
        @staticmethod
        def create(model, file, *args, **kwargs):
            return FakeTranscriptionResponse()

    transcriptions = Transcriptions()


class FakeGroqClient:
    def __init__(self, api_key):
        self.audio = FakeGroqWhisperAPI()


def fake_extract_symptoms_from_text(transcription_text: str, gemini_api_key: str) -> dict:
    return {
        "symptoms": ["headache", "swelling"],
        "confidence": "high",
        "original_complaints": "Patient reports headache and swelling",
        "gemini_json_error": False,
    }


def main():
    os.environ["GROQ_API_KEY"] = "dummy-groq-key"
    os.environ["GEMINI_API_KEY"] = "dummy-gemini-key"

    wav = io.BytesIO(
        b"RIFF\x24\x00\x00\x00WAVEfmt "
        b"\x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80>\x00\x00"
        b"\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    upload = UploadFile(filename="mock.wav", file=wav)

    with patch("app.services.voice_service.Groq", FakeGroqClient), patch(
        "app.services.voice_service.extract_symptoms_from_text", fake_extract_symptoms_from_text
    ):
        voice_data = process_voice(upload)

    risk_result = calculate_risk(
        symptoms=voice_data["symptoms"],
        bp_systolic=142,
        bp_diastolic=92,
        age=29,
        pregnancy_week=32,
        days_since_last_checkup=5,
        previous_complications=False,
    )

    print("VOICE_DATA:", voice_data)
    print("RISK_RESULT:", risk_result)


if __name__ == "__main__":
    main()
