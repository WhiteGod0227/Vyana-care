import requests
import json

payload = {
    "name": "Test Mother",
    "age": 25,
    "village": "TestVillage", 
    "district": "Barmer",
    "pregnancy_week": 28,
    "phone_number": "9999999999",
    "asha_id": 1
}

try:
    response = requests.post("http://127.0.0.1:8000/patient/register", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
