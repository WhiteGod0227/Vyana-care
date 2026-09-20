# 🌐 Vyana Care — Production Deployment Runbook & Live Launch Guide

> **Target Deploy Architecture:**
> - **Backend:** FastAPI on **Render.com** (with Managed PostgreSQL Database) or **Railway**
> - **Frontend:** React SPA on **Vercel** or **Netlify**
> - **Security:** HTTPS/TLS 1.3, Strict CORS, DPDP Act 2023 Compliance, PII Masking

---

## 🚀 Part 1: Deploying the Backend (FastAPI + PostgreSQL on Render)

### Option A: 1-Click Render Blueprint (Recommended)
The repository contains a pre-configured [`render.yaml`](file:///c:/Desktop/Vyana%20care/Vyana/render.yaml) that automatically provisions both the FastAPI web service and a managed PostgreSQL database.

1. **Push your repository to GitHub**:
   ```bash
   git push origin main
   ```
2. **Open Render Dashboard**: Navigate to [dashboard.render.com](https://dashboard.render.com).
3. Click **New +** → Select **Blueprint**.
4. Connect your GitHub repository (`Vyana-care`).
5. Render will detect `render.yaml` and create:
   - 🐘 **Database:** `vyana-db` (PostgreSQL 16)
   - ⚡ **Web Service:** `vyana-care-backend` (Python 3.11 / Uvicorn)
6. Click **Apply**.

---

### Option B: Manual Web Service Setup on Render / Railway
If setting up manually via the dashboard:

| Setting | Value |
|---|---|
| **Environment** | Python 3 |
| **Region** | Singapore (`sin`) or Frankfurt (closest latency to India) |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/knowledge/topics` |

---

### 🔑 Backend Production Environment Variables
Set these variables in the **Environment** tab of your Render/Railway dashboard:

```ini
# --- Database ---
DATABASE_URL=postgresql://vyana_user:secret_pass@ep-xyz.render.com/vyana_db?sslmode=require

# --- AI & Speech Services ---
GROQ_API_KEY=gsk_your_production_groq_api_key_here
GEMINI_API_KEY=AIzaSy_your_production_gemini_api_key_here
GEMINI_MODEL_NAME=models/gemini-2.5-flash

# --- Telephony & SMS (Twilio) ---
TWILIO_ACCOUNT_SID=AC_your_production_twilio_account_sid
TWILIO_AUTH_TOKEN=your_production_twilio_auth_token
TWILIO_FROM_NUMBER=+1234567890

# --- Emergency Dispatch Hotlines ---
EMERGENCY_AMBULANCE_NUMBER=108
EMERGENCY_ASHA_PHONE=9876543210
EMERGENCY_PHC_PHONE=9000010001
DEFAULT_DRIVER_PHONE=9876543210

# --- Production Security & CORS ---
# Replace with your actual live Vercel domain once deployed
BACKEND_CORS_ORIGINS=["https://vyana-care.vercel.app","https://vyana-care.netlify.app"]
```

---

## ⚡ Part 2: Deploying the Frontend (React SPA on Vercel)

### Method 1: Using Vercel CLI
From your local terminal, deploy directly to Vercel:
```bash
cd "c:\Desktop\Vyana care\Vyana\frontend"
npx vercel --prod
```
*Follow the interactive prompts:*
- Set root directory: `./`
- Framework preset: `Vite`
- Build command: `npm run build`
- Output directory: `dist`

### Method 2: Vercel Web Dashboard (GitHub Connected)
1. Go to [vercel.com/new](https://vercel.com/new).
2. Import your GitHub repository (`Vyana-care`).
3. Set **Root Directory** to `frontend`.
4. Add the Production Environment Variable:
   - **`VITE_API_BASE_URL`**: `https://vyana-care-backend.onrender.com` (Your live Render backend URL)
   - **`VITE_HOTLINE_AMBULANCE`**: `108`
   - **`VITE_HOTLINE_ASHA`**: `9876543210`
   - **`VITE_HOTLINE_PHC`**: `9000010001`
5. Click **Deploy**.

> **Note on Routing:** The repository includes [`frontend/vercel.json`](file:///c:/Desktop/Vyana%20care/Vyana/frontend/vercel.json) and [`frontend/public/_redirects`](file:///c:/Desktop/Vyana%20care/Vyana/frontend/public/_redirects) to ensure direct URL navigation (e.g. `/asha`, `/district`, `/awaaz`) works smoothly without 404 errors.

---

## 🔒 Part 3: Production CORS & Security Lockdown

Once your frontend domain is active (e.g., `https://vyana-care.vercel.app`), update the backend `BACKEND_CORS_ORIGINS` on Render:

```json
["https://vyana-care.vercel.app", "https://vyana-care.netlify.app"]
```

This ensures only authorized frontend clients can invoke backend voice inference and emergency dispatch routes.

---

## 🧪 Part 4: Post-Deployment Live Verification Checklist

Run these validation tests directly against your live deployed production URLs:

- [ ] **1. HTTPS / SSL Check:**
  - Verify `https://` padlock appears on both Frontend (`https://vyana-care.vercel.app`) and Backend (`https://vyana-care-backend.onrender.com/knowledge/topics`).
- [ ] **2. Vernacular Voice Flow:**
  - Open live app on smartphone/desktop.
  - Tap mic and speak Hindi pregnancy query.
  - Confirm Whisper-large-v3 transcribes in real-time and Gemini generates clinical response with audio playback.
- [ ] **3. Offline Fuzzy Matching:**
  - Turn off mobile data / toggle Airplane Mode.
  - Search maternal knowledge base for *"आहार"* or *"खतरे के निशान"*.
  - Confirm local cached library responds instantly.
- [ ] **4. 1-Tap SOS Hotline:**
  - Open Emergency SOS Modal.
  - Tap **108 Govt Ambulance** → Native dialer triggers `tel:108`.
  - Tap **Send SMS Alert** → Confirms live dispatch record created on backend.
- [ ] **5. ASHA Worker Dashboard:**
  - Navigate to `https://vyana-care.vercel.app/asha`.
  - Verify patient cohort, high-risk triage sorting, and ANC visit logging.
- [ ] **6. Browser Console Audit:**
  - Inspect Developer Tools Console → Ensure **0 CORS errors** and **0 uncaught exceptions**.

---

## ⏱️ Part 5: Stability & Anti-Sleep Strategy (For Live Demos)

Free-tier cloud web services (e.g., Render Free Tier) spin down after 15 minutes of inactivity. To keep your live demo warm:

1. **Free Uptime Pinger (Recommended):**
   - Create a free account at [cron-job.org](https://cron-job.org) or [uptimerobot.com](https://uptimerobot.com).
   - Set up an HTTP `GET` monitor every **10 minutes** to:
     ```
     https://vyana-care-backend.onrender.com/knowledge/topics
     ```
2. **Instant Pre-Warm:**
   - 2 minutes before presenting to judges or stakeholders, open the backend URL in your browser to wake the container.
