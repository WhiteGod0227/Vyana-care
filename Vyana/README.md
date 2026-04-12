# Vyana Care - AI Maternal Health Platform

Vyana Care is an AI-assisted maternal health system designed for rural frontline workflows. It combines patient reporting (voice/text/IVR), ASHA triage, district analytics, community audio support (Vaani), offline sync, and production-grade integration scaffolding.

## Problem
India faces preventable maternal risks where early symptom escalation and care coordination are delayed in rural settings.

## Solution
- Voice + text symptom reporting with AI risk scoring.
- Automated alerting and escalation to ASHA teams.
- District-level operational visibility and trend analytics.
- Offline-first support for low-connectivity field operations.
- IVR workflows for non-smartphone callers.
- Government integration scaffolding (ABHA, HMIS, 108 dispatch).
- Federated learning architecture simulation for privacy-preserving model improvement.

## Tech Stack (Phase 1 + 2 + 3)
- Backend: FastAPI, SQLAlchemy, PostgreSQL, APScheduler, Redis-ready cache hooks.
- AI: Groq Whisper, Gemini extraction/moderation.
- Messaging: Firebase Admin, Twilio-ready OTP/IVR integration points.
- Frontend: React + Vite, MUI, Recharts, Framer Motion, Leaflet.
- Offline/PWA: service worker, local queue + batch sync.

## Key Features
- Patient registration + profile + symptom history.
- Risk model with high-risk hard rules and escalation.
- ASHA dashboard with alert acknowledgements.
- District dashboard + map + IVR + federated sections.
- Vaani (community voice moderation + nurse review + feed).
- Offline sync batch and Bluetooth export/import package flow.
- OTP auth flow with refresh tokens and blacklist support.
- Consent, delete-request, and data export endpoints for DPDP-aligned workflow.

## Setup
1. Clone repository.
2. Create virtual environment and install backend deps:
	```powershell
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	pip install -r requirements.txt
	```
3. Configure env vars:
	```powershell
	copy .env.example .env
	```
4. Run backend:
	```powershell
	python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
	```
5. Run frontend:
	```powershell
	cd frontend
	npm install
	npm run dev
	```
6. Optional demo seed:
	```powershell
	python seed.py
	```

## API Snapshot
- Core: /patient, /symptom, /asha, /alert, /district, /awaaz
- Phase 3: /sync, /ivr, /federated, /abha, /hmis, /ambulance, /admin/audit-logs
- Security: /auth/login, /auth/request-otp, /auth/verify-otp, /auth/refresh, /auth/logout
- Monitoring: /health, /metrics

## Testing
- API tests: `pytest tests/ -v`
- Manual frontend checklist: see TESTING.md

## Deployment
### Docker
```powershell
docker compose up --build
```

### Railway (backend)
```powershell
railway init
railway add postgresql
railway add redis
railway up
```

### Vercel (frontend)
```powershell
cd frontend
npm run build
vercel --prod
```

## Demo Flow
1. Register a patient.
2. Submit high-risk symptoms.
3. Observe ASHA alert and acknowledgement.
4. Review district analytics and federated simulation.
5. Test offline queue and sync recovery.

## Team
Solo developer build, hackathon-ready architecture.
