from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_patient_register_validation():
    payload = {
        "name": "Sita",
        "age": 28,
        "village": "Ramgarh",
        "district": "Barmer",
        "pregnancy_week": 24,
        "phone_number": "9876500011",
        "asha_id": 1,
    }
    res = client.post("/patient/register", json=payload)
    assert res.status_code in (200, 400)


def test_sync_status_endpoint():
    res = client.get("/sync/status/demo-device")
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_federated_simulate_training():
    res = client.post("/federated/simulate-training")
    assert res.status_code == 200
    assert res.json()["success"] is True
