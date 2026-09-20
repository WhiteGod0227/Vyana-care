import io
import struct
import wave
from pprint import pprint

import httpx

BASE = "http://127.0.0.1:8001"


def build_valid_wav(duration_seconds: int = 1, sample_rate: int = 16000) -> io.BytesIO:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        total_frames = duration_seconds * sample_rate
        silence = b"".join(struct.pack("<h", 0) for _ in range(total_frames))
        wf.writeframes(silence)
    buffer.seek(0)
    return buffer


def show(name, method, url, request_body, response):
    print("\n" + "=" * 80)
    print(f"ENDPOINT: {name}")
    print(f"METHOD: {method}")
    print(f"URL: {url}")
    print("REQUEST BODY:")
    pprint(request_body)
    print("STATUS:", response.status_code)
    try:
        print("RESPONSE:")
        pprint(response.json())
    except Exception:
        print(response.text)


with httpx.Client(timeout=60) as client:
    r = client.get(f"{BASE}/health")
    show("GET /health", "GET", f"{BASE}/health", None, r)

    register_payload = {
        "name": "Demo Patient",
        "age": 27,
        "village": "Ramgarh",
        "district": "Barmer",
        "pregnancy_week": 30,
        "phone_number": "9999999999",
        "asha_id": 1,
    }
    r = client.post(f"{BASE}/patient/register", json=register_payload)
    show("POST /patient/register", "POST", f"{BASE}/patient/register", register_payload, r)

    patient_id = r.json().get("data", {}).get("patient_id", 1)

    r = client.get(f"{BASE}/patient/{patient_id}")
    show(
        "GET /patient/{patient_id}",
        "GET",
        f"{BASE}/patient/{patient_id}",
        None,
        r,
    )

    text_payload = {
        "patient_id": patient_id,
        "symptoms": ["bleeding", "dizziness"],
        "bp_systolic": 150,
        "bp_diastolic": 98,
        "age": 27,
        "pregnancy_week": 30,
        "days_since_last_checkup": 20,
        "previous_complications": True,
    }
    r = client.post(f"{BASE}/symptom/report/text", json=text_payload)
    show(
        "POST /symptom/report/text",
        "POST",
        f"{BASE}/symptom/report/text",
        text_payload,
        r,
    )

    wav_bytes = build_valid_wav(duration_seconds=1)
    files = {"audio_file": ("sample.wav", wav_bytes, "audio/wav")}
    data = {"patient_id": str(patient_id)}
    r = client.post(f"{BASE}/symptom/report/voice", data=data, files=files)
    show(
        "POST /symptom/report/voice",
        "POST",
        f"{BASE}/symptom/report/voice",
        {"form": data, "file": "sample.wav"},
        r,
    )

    r = client.get(f"{BASE}/asha/1/patients")
    show("GET /asha/{asha_id}/patients", "GET", f"{BASE}/asha/1/patients", None, r)

    checkup_payload = {
        "patient_id": patient_id,
        "asha_id": 1,
        "bp_systolic": 130,
        "bp_diastolic": 84,
        "weight_kg": 58,
        "notes": "Routine home visit",
        "next_visit_date": "2026-04-20",
    }
    r = client.post(f"{BASE}/asha/checkup/record", json=checkup_payload)
    show(
        "POST /asha/checkup/record",
        "POST",
        f"{BASE}/asha/checkup/record",
        checkup_payload,
        r,
    )

    r = client.get(f"{BASE}/asha/1/alerts")
    show("GET /asha/{asha_id}/alerts", "GET", f"{BASE}/asha/1/alerts", None, r)

    alert_id = None
    try:
        alerts = r.json().get("data", {}).get("alerts", [])
        if alerts:
            alert_id = alerts[0].get("alert_id")
    except Exception:
        pass

    if alert_id:
        r_ack = client.post(f"{BASE}/alert/acknowledge/{alert_id}")
        show(
            "POST /alert/acknowledge/{alert_id}",
            "POST",
            f"{BASE}/alert/acknowledge/{alert_id}",
            None,
            r_ack,
        )
    else:
        print("\nNo alert available to acknowledge.")

    r = client.get(f"{BASE}/district/Barmer/stats")
    show(
        "GET /district/{district_name}/stats",
        "GET",
        f"{BASE}/district/Barmer/stats",
        None,
        r,
    )

    r = client.get(f"{BASE}/district/Barmer/heatmap")
    show(
        "GET /district/{district_name}/heatmap",
        "GET",
        f"{BASE}/district/Barmer/heatmap",
        None,
        r,
    )
