# Vyana Care — Environment & Credential Management Guide

This document outlines how credentials and environment variables are structured in **Vyana Care**, and provides step-by-step instructions for switching from **Local / Sandbox** to **Production** deployments.

---

## 1. Architecture & Variable Overview

Vyana Care follows a strict 12-factor configuration model. All sensitive keys and configuration parameters are loaded at runtime from `.env` files and exposed via centralized configuration objects:

* **Backend Config Module**: [`app/core/config.py`](file:///c:/Desktop/Vyana%20care/Vyana/app/core/config.py) (`from app.core.config import settings`)
* **Frontend Config**: Vite environment injection via `import.meta.env.VITE_*` ([`frontend/src/api/axios.js`](file:///c:/Desktop/Vyana%20care/Vyana/frontend/src/api/axios.js))

---

## 2. Complete Environment Variable Reference

### Backend Variables (`.env`)

| Variable | Type | Default / Sandbox | Description & Production Source |
| :--- | :--- | :--- | :--- |
| `POSTGRES_URL` | String | `postgresql+psycopg://postgres:postgres@localhost:5432/vyana_care` | Primary PostgreSQL database URL. (AWS RDS, Neon, Supabase) |
| `SQLITE_FALLBACK_URL`| String | `sqlite:///./vyana.db` | Local SQLite fallback when PostgreSQL server is offline. |
| `GROQ_API_KEY` | Secret | Sandbox Key | Groq Whisper STT API Key. Get from [Groq Console](https://console.groq.com/keys). |
| `GEMINI_API_KEY` | Secret | Sandbox Key | Google Gemini AI Key. Get from [Google AI Studio](https://aistudio.google.com/app/apikey). |
| `GEMINI_MODEL_NAME` | String | `models/gemini-2.5-flash` | Gemini model name for clinical entity extraction. |
| `TWILIO_ACCOUNT_SID` | Secret | `AC...` | Twilio Account SID. Get from [Twilio Console](https://console.twilio.com/). |
| `TWILIO_AUTH_TOKEN` | Secret | `...` | Twilio Auth Token. |
| `TWILIO_FROM_NUMBER` | String | `+1...` | Twilio registered phone number in E.164 format. |
| `TWILIO_TO_NUMBER` | String | `+91...` | Override destination number used during demo/testing. |
| `TWILIO_WEBHOOK_URL` | URL | `""` | Public webhook URL for inbound IVR callbacks. |
| `FIREBASE_CREDENTIALS_JSON` | Path / JSON | `./vyana-care-firebase-adminsdk-*.json` | Path to Firebase service account JSON key or raw JSON string. |
| `ABHA_SANDBOX_API_KEY` | Secret | Sandbox Key | ABDM Ayushman Bharat Digital Mission API Key. |
| `JWT_SECRET_KEY` | Secret | `vyana-care-jwt-local-secret` | Cryptographic secret for signing auth tokens & HMACs. |
| `DEMO_ESCALATION_SECONDS` | Integer | `15` | Escalation delay in seconds (15s for demo, 60–300s in prod). |
| `ALLOWED_ORIGINS` | CSV | `http://localhost:5173,...` | Comma-separated list of allowed frontend origins for CORS. |
| `FRONTEND_URL` | URL | `http://localhost:5173` | Production frontend domain. |
| `EMERGENCY_AMBULANCE_NUMBER` | String | `108` | National / Regional 108 ambulance hotline. |
| `EMERGENCY_ASHA_PHONE` | String | `9876543210` | Default ASHA emergency contact. |
| `EMERGENCY_PHC_PHONE` | String | `9000010001` | Default Primary Health Centre emergency contact. |

---

### Frontend Variables (`frontend/.env`)

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | URL | `http://127.0.0.1:8001` | FastAPI backend server URL (e.g. `https://api.vyanacare.org`). |
| `VITE_HOTLINE_AMBULANCE`| String | `108` | Hotline number displayed on emergency SOS cards. |
| `VITE_HOTLINE_ASHA` | String | `9876543210` | Frontline ASHA contact link. |
| `VITE_HOTLINE_PHC` | String | `9000010001` | PHC Nurse contact link. |
| `VITE_FIREBASE_CONFIG` | JSON | `{}` | Optional web Firebase configuration for browser push notifications. |

---

## 3. Switching from Test to Production (Step-by-Step)

### Step 1: Prepare Production Database
1. Provision a managed PostgreSQL instance (e.g. AWS RDS, Neon, Supabase, Google Cloud SQL).
2. Update `.env` on your backend server:
   ```env
   POSTGRES_URL=postgresql+psycopg://db_user:secure_password@prod-db.example.com:5432/vyana_production
   ```

### Step 2: Switch AI Credentials to Paid / High-Quota Keys
1. In Google AI Studio, generate a production key and set:
   ```env
   GEMINI_API_KEY=AIzaSy...
   GEMINI_MODEL_NAME=models/gemini-2.5-flash
   ```
2. In Groq Console, generate your production API key:
   ```env
   GROQ_API_KEY=gsk_...
   ```

### Step 3: Configure Twilio Production Telephony
1. Upgrade your Twilio trial account to a paid tier.
2. Purchase a local toll-free or Indian national number (or international alphanumeric sender ID).
3. Clear or update the demo destination override:
   ```env
   TWILIO_ACCOUNT_SID=AC_PROD_ACCOUNT_SID
   TWILIO_AUTH_TOKEN=PROD_AUTH_TOKEN
   TWILIO_FROM_NUMBER=+918000000000
   TWILIO_TO_NUMBER=
   TWILIO_WEBHOOK_URL=https://api.vyanacare.org/ivr/incoming
   ```

### Step 4: Add Production Firebase Service Account
1. Go to Firebase Console $\rightarrow$ **Project Settings** $\rightarrow$ **Service Accounts** $\rightarrow$ **Generate New Private Key**.
2. Download the JSON file to your deployment server (e.g. `/etc/secrets/firebase-key.json`).
3. Set in `.env`:
   ```env
   FIREBASE_CREDENTIALS_JSON=/etc/secrets/firebase-key.json
   ```

### Step 5: Rotate JWT Secret & Escalation Delays
1. Generate a 64-character random cryptographic secret:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Update `.env`:
   ```env
   JWT_SECRET_KEY=e83a7f...
   VYANA_AUTH_SECRET=e83a7f...
   DEMO_ESCALATION_SECONDS=180
   ```

### Step 6: Configure CORS & Deploy Frontend
1. In `frontend/.env.production`:
   ```env
   VITE_API_BASE_URL=https://api.vyanacare.org
   ```
2. In backend `.env`:
   ```env
   FRONTEND_URL=https://app.vyanacare.org
   ALLOWED_ORIGINS=https://app.vyanacare.org,https://admin.vyanacare.org
   ```

---

## 4. Verification & Health Check

Verify configuration without starting the dev server:

```bash
# Verify Settings loading
python -c "from app.core.config import settings; print('Loaded DB:', settings.database_url); print('Twilio configured:', settings.twilio_is_configured()); print('Gemini configured:', settings.gemini_is_configured())"

# Run backend test suite
python test_endpoints.py
```
