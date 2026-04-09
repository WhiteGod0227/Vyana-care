# Vyana Care Backend

FastAPI + PostgreSQL backend for maternal health monitoring.

## 1) Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Fill `.env` with:

- `POSTGRES_URL`
- `GROQ_API_KEY` (Groq Whisper transcription)
- `GEMINI_API_KEY` (Gemini symptom extraction)
- `FIREBASE_CREDENTIALS_JSON` (path to service account JSON or raw JSON string)

## 2) Run API

```powershell
uvicorn app.main:app --reload
```

Base URL: `http://127.0.0.1:8000`
Swagger: `http://127.0.0.1:8000/docs`

## 3) Seed demo data

```powershell
python seed.py
```

This creates:

- 3 ASHA workers
- 20 patients
- 50 symptom records
- Includes Savitri Devi with a mandatory high-risk entry

## 4) Endpoints

- `POST /patient/register`
- `GET /patient/{patient_id}`
- `POST /symptom/report/text`
- `POST /symptom/report/voice`
- `GET /asha/{asha_id}/patients`
- `POST /asha/checkup/record`
- `GET /asha/{asha_id}/alerts`
- `POST /alert/acknowledge/{alert_id}`
- `GET /district/{district_name}/stats`
- `GET /district/{district_name}/heatmap`
- `GET /health`
