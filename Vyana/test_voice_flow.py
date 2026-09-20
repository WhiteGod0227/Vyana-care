import sys
import os

# Set standard output encoding to utf-8 for Windows console
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
from app.core.config import settings
from app.services.voice_service import extract_symptoms_from_text

print("--- Testing Voice Extraction with Gemini ---")
test_queries = [
    "नमस्ते दीदी, मेरे सिर में बहुत तेज दर्द हो रहा है और चक्कर आ रहे हैं",
    "Mera pet me dard ho raha hai aur ulti jaisa lag raha hai",
    "Mujhe bukhar hai aur pait me sujan lag rahi hai",
    "Sab theek hai, bas thakaan lagti hai dopahar me",
]

for q in test_queries:
    print(f"\nQuery: {q}")
    res = extract_symptoms_from_text(q, settings.gemini_api_key)
    print("Extracted:", json.dumps(res, indent=2, ensure_ascii=False))

print("\n--- Testing API /symptom/report/text ---")
for q in test_queries:
    res = extract_symptoms_from_text(q, settings.gemini_api_key)
    payload = {
        "patient_id": 1,
        "symptoms": res["symptoms"],
        "bp_systolic": 120,
        "bp_diastolic": 80,
        "age": 24,
        "pregnancy_week": 28,
        "days_since_last_checkup": 5,
        "previous_complications": False
    }
    r = requests.post("http://127.0.0.1:8001/symptom/report/text", json=payload)
    print(f"Status: {r.status_code}")
    print("Response:", r.json())
