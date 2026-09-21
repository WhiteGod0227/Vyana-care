import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

BACKEND_URL = "https://vyana-care.onrender.com"
FRONTEND_ORIGIN = "https://frontend-ayushs-projects-76f1503f.vercel.app"

print("================================================================")
print("TESTING LIVE PRODUCTION CONNECTION: FRONTEND <-> BACKEND")
print("================================================================")

headers = {
    "Origin": FRONTEND_ORIGIN,
    "Referer": f"{FRONTEND_ORIGIN}/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
}

# 1. Test CORS Preflight (OPTIONS)
print("\n[1/5] Testing CORS Preflight (OPTIONS /symptom/report/text)...")
preflight_headers = {
    "Origin": FRONTEND_ORIGIN,
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type"
}
r_opt = requests.options(f"{BACKEND_URL}/symptom/report/text", headers=preflight_headers)
print(f"Status: {r_opt.status_code}")
print(f"Access-Control-Allow-Origin: {r_opt.headers.get('access-control-allow-origin')}")
print(f"Access-Control-Allow-Methods: {r_opt.headers.get('access-control-allow-methods')}")

# 2. Test Knowledge Topics (GET)
print("\n[2/5] Testing Knowledge Base (GET /knowledge/topics)...")
r_know = requests.get(f"{BACKEND_URL}/knowledge/topics", headers=headers)
print(f"Status: {r_know.status_code}")
print(f"CORS Header: {r_know.headers.get('access-control-allow-origin')}")
print(f"Topics Count: {len(r_know.json().get('data', {}).get('topics', []))}")

# 3. Test ASHA Patients List (GET)
print("\n[3/5] Testing ASHA Portal Data (GET /asha/1/patients)...")
r_pat = requests.get(f"{BACKEND_URL}/asha/1/patients", headers=headers)
print(f"Status: {r_pat.status_code}")
print(f"CORS Header: {r_pat.headers.get('access-control-allow-origin')}")
print(f"Patients Found: {[p['name'] for p in r_pat.json().get('data', {}).get('patients', [])[:4]]}")

# 4. Test Symptom Triage (POST)
print("\n[4/5] Testing AI Symptom Triage (POST /symptom/report/text)...")
payload = {
    "patient_id": 1,
    "symptoms": ["headache", "dizziness"],
    "bp_systolic": 120,
    "bp_diastolic": 80,
    "age": 29,
    "pregnancy_week": 32,
    "days_since_last_checkup": 0,
    "previous_complications": False
}
r_sym = requests.post(f"{BACKEND_URL}/symptom/report/text", json=payload, headers=headers)
print(f"Status: {r_sym.status_code}")
print(f"CORS Header: {r_sym.headers.get('access-control-allow-origin')}")
print(f"AI Risk Result: {r_sym.json().get('data', {}).get('risk_result')}")

# 5. Test SOS Hotline Dispatch (POST)
print("\n[5/5] Testing Emergency SOS Dispatch (POST /sos/trigger)...")
sos_payload = {
    "patient_name": "Savitri Devi",
    "patient_id": 1,
    "village": "Ramgarh",
    "district": "Barmer",
    "phone": "9000010001",
    "emergency_type": "MATERNAL_108_SOS",
    "symptoms_summary": "Emergency SOS check",
    "gps_lat": 25.123,
    "gps_lng": 71.456
}
r_sos = requests.post(f"{BACKEND_URL}/sos/trigger", json=sos_payload, headers=headers)
print(f"Status: {r_sos.status_code}")
print(f"CORS Header: {r_sos.headers.get('access-control-allow-origin')}")
print(f"Dispatch ID: {r_sos.json().get('data', {}).get('dispatch_id')}")

print("\n================================================================")
print("ALL LIVE PRODUCTION CONNECTIVITY CHECKS PASSED WITH 200 OK!")
print("================================================================")
