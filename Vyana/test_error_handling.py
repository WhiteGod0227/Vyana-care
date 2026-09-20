import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

BASE = "http://127.0.0.1:8001"

print("==================================================")
print("TEST SUITE: ERROR HANDLING & MALFORMED REQUESTS")
print("==================================================")

# Test 1: Empty payload validation (missing required fields)
r1 = requests.post(f"{BASE}/symptom/report/text", json={})
print(f"1. Empty payload to /symptom/report/text -> Status: {r1.status_code}")
print("   Response:", r1.json())
assert r1.status_code in [400, 422], f"Expected 400/422, got {r1.status_code}"

# Test 2: Non-existent patient ID with valid schema
r2 = requests.post(f"{BASE}/symptom/report/text", json={
    "patient_id": 999999,
    "symptoms": ["headache"],
    "bp_systolic": 120,
    "bp_diastolic": 80,
    "age": 25,
    "pregnancy_week": 24,
    "days_since_last_checkup": 0,
    "previous_complications": False
})
print(f"2. Non-existent patient ID -> Status: {r2.status_code}")
print("   Response:", r2.json())
assert r2.status_code == 404, f"Expected 404, got {r2.status_code}"

# Test 3: Invalid acknowledge alert ID
r3 = requests.post(f"{BASE}/alert/acknowledge/99999999")
print(f"3. Non-existent alert acknowledge -> Status: {r3.status_code}")
print("   Response:", r3.json())
assert r3.status_code in [400, 404], f"Expected 400/404, got {r3.status_code}"

# Test 4: Invalid route 404
r4 = requests.get(f"{BASE}/non_existent_route_123")
print(f"4. Non-existent route -> Status: {r4.status_code}")
print("   Response:", r4.json())
assert r4.status_code == 404, f"Expected 404, got {r4.status_code}"

# Test 5: Search knowledge base with empty query
r5 = requests.get(f"{BASE}/knowledge/search?q=")
print(f"5. Empty knowledge search query -> Status: {r5.status_code}")
print("   Response:", r5.json())
assert r5.status_code in [400, 422], f"Expected 400/422, got {r5.status_code}"

print("\n--- ALL ERROR HANDLING TESTS PASSED PROPERLY WITH NO CRASHES ---")
