# 🎙️ Vyana Care — 3-Minute Live Demo & Pitch Script

> **Audience:** Hackathon Judges, Healthcare Regulators (MoHFW/NHM), Angel Investors, Clinical Stakeholders  
> **Presenter Roles:** 1 Presenter (Speaking & Navigating UI)  
> **Total Time:** 180 Seconds (3 Minutes)

---

## ⏱️ Minute 0:00 – 0:45 | The Hook & The Problem

### 🗣️ Spoken Dialogue:
> *"Every 20 minutes in India, a mother loses her life to preventable pregnancy complications. In rural areas across Bihar, UP, and Rajasthan, 70% of maternal deaths happen because warning signs—like pre-eclampsia or severe anemia—are caught too late.*
>
> *Why? Because existing health apps are built for English-speaking, urban smartphone users with high-speed WiFi. Rural mothers face three fatal barriers:*
> 1. **Literacy & Language:** They cannot type or read complex medical English.
> 2. **Connectivity Deserts:** 2G networks drop constantly.
> 3. **Overburdened ASHA Workers:** One ASHA worker monitors 1,000+ residents with paper registers.
>
> *Meet **Vyana Care (व्यान केयर)** — India's first voice-first, offline-resilient AI maternal health companion and ASHA triage network."*

---

## ⏱️ Minute 0:45 – 1:45 | Live Demo: Voice-First AI & Offline Resilience

### 🖥️ Action on Screen:
*Navigate to Mother's Home screen at `http://localhost:5173/`.*

### 🗣️ Spoken Dialogue & Live Interaction:
> *"Let's put ourselves in the shoes of Savitri Devi, an expectant mother in rural Vaishali. She doesn't need to type. She taps the glowing microphone and speaks naturally in Hindi:"*

```
[TAP MIC BUTTON]
Spoken Voice Query (Hindi):
"नमस्ते व्यान, मुझे पांचवा महीना चल रहा है और मुझे चक्कर आ रहे हैं, मुझे क्या खाना चाहिए?"
```

### 🖥️ Action on Screen:
*The voice waveform pulses. Whisper-large-v3 transcribes in real time, and Gemini 2.5 Flash generates a warm, culturally grounded medical guidance card in Hindi with audio playback.*

### 🗣️ Spoken Dialogue:
> *"Notice three things:*
> - **Zero Typing:** Real-time speech-to-speech interaction in native Hindi.
> - **Culturally Grounded Guidance:** Vyana recommends local, affordable iron-rich foods—palak, jaggery, roasted chana—and flags that persistent dizziness requires blood pressure checking.
> - **Offline-First Guarantee:** If cellular data drops to zero, our local fuzzy-matching knowledge base instantly takes over, ensuring the mother is never left stranded."*

---

## ⏱️ Minute 1:45 – 2:30 | Live Demo: High-Risk Detection & Emergency SOS

### 🖥️ Action on Screen:
*Click the Floating Red **आपातकालीन SOS (Emergency SOS)** button.*

### 🗣️ Spoken Dialogue & Live Interaction:
> *"Now, imagine Savitri experiences severe bleeding at 2 AM. In maternal healthcare, the 'Golden Hour' saves lives. She taps the SOS button."*

```
[TAP EMERGENCY SOS MODAL]
Show:
1. 3-Second Abort Safety Timer (prevents accidental triggers)
2. 1-Tap Auto-Dialer for 108 Emergency Ambulance
3. Automated Twilio Telephony Dispatch with Village GPS Coordinates
```

> *"With one tap, Vyana triggers a dual response: it opens a direct hotline to 108 Ambulance and fires an automated alert SMS to her designated ASHA worker."*

---

## ⏱️ Minute 2:30 – 3:00 | ASHA Worker Dashboard & Conclusion

### 🖥️ Action on Screen:
*Navigate to `/asha` (ASHA Worker Dashboard).*

### 🗣️ Spoken Dialogue:
> *"Now let's switch to the ASHA worker's dashboard. ASHA Didi instantly sees Savitri's high-risk alert prioritized at the top of her triage queue.
>
> She can view the mother's gestational age, previous hemoglobin records, log an upcoming ANC checkup, or trigger a direct WhatsApp follow-up with one click.
>
> **Under the Hood:**
> - **Privacy First:** Fully compliant with India's DPDP Act 2023 with masked phone numbers and encrypted records.
> - **ABHA Integrated:** Seamlessly links with Ayushman Bharat Digital Mission IDs.
> - **Stack:** FastAPI, Google Gemini 2.5 Flash, Groq Whisper, PostgreSQL/SQLite, Twilio, and React.
>
> *Vyana Care transforms maternal healthcare from reactive emergencies into proactive, life-saving community care. Thank you!"*

---

## 💡 Quick Tips for Live Presentation

1. **Audio Testing:** Ensure your microphone is selected and system audio is shared so the audience hears Vyana's Hindi voice response.
2. **Tab Pre-loading:** Keep both tabs (`/` and `/asha`) open side-by-side in split screen or ready in browser tabs for instant switching.
3. **Backup Mode:** If live internet is slow during the presentation, demonstrate the offline cached responses—judges love seeing offline resilience in action!
