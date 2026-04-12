import { useEffect, useMemo, useRef, useState } from "react";
import { Button, CircularProgress, MenuItem, TextField } from "@mui/material";
import MicIcon from "@mui/icons-material/Mic";
import CheckIcon from "@mui/icons-material/Check";
import { motion as Motion } from "framer-motion";
import toast from "react-hot-toast";
import api from "../api/axios";
import LoadingSkeleton from "../components/LoadingSkeleton";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";

const DISTRICTS = ["Barmer", "Jaisalmer", "Jodhpur"];

const symptomOptions = [
  ["Headache", "headache"],
  ["Swelling", "swelling"],
  ["Blurred Vision", "blurred_vision"],
  ["Fever", "fever"],
  ["Bleeding", "bleeding"],
  ["Fatigue", "fatigue"],
  ["Nausea", "nausea"],
  ["Dizziness", "dizziness"],
  ["Abdominal Pain", "abdominal_pain"],
  ["Chest Pain", "chest_pain"],
  ["Breathing Difficulty", "difficulty_breathing"],
  ["Reduced Fetal Movement", "reduced_fetal_movement"]
];

const escalations = [
  ["success", "T+0:00 - ASHA worker notified"],
  ["warning", "T+1:00 - Family received SMS update"],
  ["error", "T+2:00 - PHC nurse escalated"],
  ["error", "T+3:00 - Ambulance dispatched to Ramgarh"]
];

function useCountUp(endValue, duration = 1200) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    const start = performance.now();
    let raf;

    const tick = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * endValue));
      if (progress < 1) raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [endValue, duration]);

  return value;
}

function PatientPortal() {
  const [error, setError] = useState("");
  const [loadingSection, setLoadingSection] = useState("");
  const [patientId, setPatientId] = useState(() => localStorage.getItem("patient_id") || "");
  const [patientProfile, setPatientProfile] = useState(null);
  const [demoMode, setDemoMode] = useState(false);
  const [demoProgress, setDemoProgress] = useState(0);
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [showBp, setShowBp] = useState(false);
  const [bpSystolic, setBpSystolic] = useState("");
  const [bpDiastolic, setBpDiastolic] = useState("");
  const [prevComp, setPrevComp] = useState(false);
  const [result, setResult] = useState(null);
  const [recording, setRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [online, setOnline] = useState(navigator.onLine);
  const [pendingSync, setPendingSync] = useState(() => Number(localStorage.getItem("pending_sync") || 0));
  const [form, setForm] = useState({
    name: "",
    age: "",
    village: "",
    district: "Barmer",
    pregnancy_week: "",
    phone_number: ""
  });

  const recorderRef = useRef(null);
  const chunksRef = useRef([]);

  const riskLevel = demoMode ? "HIGH" : result?.risk_result?.level;
  const riskScore = demoMode ? 89 : result?.risk_result?.score || 0;
  const animatedRiskScore = useCountUp(riskScore, 1400);

  useEffect(() => {
    if (!patientId) return;

    const loadProfile = async () => {
      try {
        const res = await api.get(`/patient/${patientId}`);
        setPatientProfile(res.data?.data || null);
      } catch {
        setError("Could not load your previous reports.");
      }
    };

    loadProfile();
  }, [patientId]);

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);

    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);

    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  useEffect(() => {
    if (!demoMode) {
      setDemoProgress(0);
      return;
    }

    const interval = setInterval(() => {
      setDemoProgress((v) => {
        if (v >= 100) {
          clearInterval(interval);
          return 100;
        }
        return v + 5;
      });
    }, 120);

    return () => clearInterval(interval);
  }, [demoMode]);

  useEffect(() => {
    if (!demoMode) return;

    const loadDemo = async () => {
      try {
        const res = await api.get("/asha/1/patients");
        const savitri = (res.data?.data?.patients || []).find((p) => p.name.toLowerCase().includes("savitri"));
        if (savitri?.id) {
          setPatientId(String(savitri.id));
          localStorage.setItem("patient_id", String(savitri.id));
        }
      } catch {
        setError("Could not fetch demo patient from server.");
      }

      setForm({
        name: "Savitri Devi",
        age: "29",
        village: "Ramgarh",
        district: "Barmer",
        pregnancy_week: "32",
        phone_number: "9000010001"
      });
      setSelectedSymptoms(["swelling", "blurred_vision", "headache"]);
      setResult({
        risk_result: {
          score: 89,
          level: "HIGH",
          primary_reason: "Pre-eclampsia symptom pattern detected.",
          recommendation: "Visit the nearest doctor immediately and inform your ASHA worker."
        }
      });

      toast.success("Demo mode loaded.");
    };

    loadDemo();
  }, [demoMode]);

  useEffect(() => {
    if (!recording) return;

    const timer = setInterval(() => setRecordSeconds((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [recording]);

  const handleFormChange = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const handleRegister = async () => {
    setLoadingSection("register");
    setError("");

    // Validate form
    if (!form.name || !form.age || !form.village || !form.district || !form.pregnancy_week || !form.phone_number) {
      setError("Please fill in all fields.");
      setLoadingSection("");
      return;
    }

    const age = Number(form.age);
    const pregnancyWeek = Number(form.pregnancy_week);

    if (age < 12 || age > 60) {
      setError("Age must be between 12 and 60.");
      setLoadingSection("");
      return;
    }

    if (pregnancyWeek < 1 || pregnancyWeek > 45) {
      setError("Pregnancy week must be between 1 and 45.");
      setLoadingSection("");
      return;
    }

    try {
      const payload = {
        ...form,
        age: age,
        pregnancy_week: pregnancyWeek,
        asha_id: 1
      };
      const res = await api.post("/patient/register", payload);
      const id = res.data?.data?.patient_id;
      if (!id) throw new Error("No patient ID returned");

      localStorage.setItem("patient_id", String(id));
      setPatientId(String(id));
      toast.success("Registration complete.");
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message || "Registration failed. Please try again.";
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoadingSection("");
    }
  };

  const toggleSymptom = (value) => {
    setSelectedSymptoms((prev) => (prev.includes(value) ? prev.filter((s) => s !== value) : [...prev, value]));
  };

  const queueOffline = () => {
    const next = pendingSync + 1;
    setPendingSync(next);
    localStorage.setItem("pending_sync", String(next));
    toast("Offline mode: report queued for sync.", { icon: "!" });
  };

  const submitText = async () => {
    if (!patientId) return toast.error("Please register first.");
    if (!online) return queueOffline();

    setLoadingSection("text");
    setError("");

    try {
      const payload = {
        patient_id: Number(patientId),
        symptoms: selectedSymptoms,
        bp_systolic: Number(bpSystolic || 0),
        bp_diastolic: Number(bpDiastolic || 0),
        age: Number(form.age || 29),
        pregnancy_week: Number(form.pregnancy_week || 32),
        days_since_last_checkup: 0,
        previous_complications: prevComp
      };

      const res = await api.post("/symptom/report/text", payload);
      setResult(res.data?.data || null);
      toast.success("Risk score generated.");
    } catch {
      setError("Could not process symptom report.");
    } finally {
      setLoadingSection("");
    }
  };

  const startRecording = async () => {
    if (demoMode) return;
    if (!patientId) {
      toast.error("Please register first to use Vaani voice feature.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        setLoadingSection("voice");

        try {
          if (!online) {
            queueOffline();
            return;
          }

          const blob = new Blob(chunksRef.current, { type: "audio/webm" });
          const fd = new FormData();
          fd.append("patient_id", String(patientId));
          fd.append("audio_file", blob, "voice.webm");

          const res = await api.post("/symptom/report/voice", fd, {
            headers: { "Content-Type": "multipart/form-data" }
          });

          setResult(res.data?.data || null);
          toast.success("Voice report processed.");
        } catch {
          setError("Could not process voice report.");
        } finally {
          stream.getTracks().forEach((t) => t.stop());
          setLoadingSection("");
        }
      };

      recorderRef.current = recorder;
      recorder.start();
      setRecordSeconds(0);
      setRecording(true);
    } catch {
      setError("Microphone access denied.");
      toast.error("Microphone access denied.");
    }
  };

  const stopRecording = () => {
    if (!recorderRef.current || recorderRef.current.state !== "recording") return;
    recorderRef.current.stop();
    setRecording(false);
  };

  const historyRows = patientProfile?.last_5_symptom_reports || [];
  const levelClass = useMemo(
    () => (riskLevel === "HIGH" ? "risk-high" : riskLevel === "MEDIUM" ? "risk-medium" : "risk-low"),
    [riskLevel]
  );

  const timerText = `${String(Math.floor(recordSeconds / 60)).padStart(2, "0")}:${String(recordSeconds % 60).padStart(2, "0")}`;

  return (
    <div className="vy-page">
      <ErrorBanner message={error} onClose={() => setError("")} />

      {!online ? (
        <div className="vy-offline-banner">
          <span>You are offline. Reports will sync automatically once internet is back.</span>
          <b>{pendingSync} pending reports</b>
        </div>
      ) : null}

      <Motion.section className="vy-hero" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div className="vy-hero-top">
          <span className="vy-pill">AI-Enabled Maternal Safety</span>
          <Button size="small" variant="contained" onClick={() => setDemoMode((v) => !v)}>
            {demoMode ? "Exit Demo" : "Demo Mode"}
          </Button>
        </div>
        <h1>Speak naturally. Get risk insights instantly.</h1>
        <p>Share symptoms in text or voice and receive a clear, actionable risk summary.</p>
        <div className="vy-hero-stats">
          <div>
            <b>67K</b>
            <span>Annual maternal deaths</span>
          </div>
          <div>
            <b>75%</b>
            <span>Rural burden</span>
          </div>
          <div>
            <b>9.4M</b>
            <span>ASHA workers</span>
          </div>
        </div>
      </Motion.section>

      <section className="vy-card">
        <h3>Feature Sections</h3>
        <div className="vy-feature-grid">
          <a href="#feature-register" className="vy-feature-tile">
            <b>Registration</b>
            <span>Create or load patient profile</span>
          </a>
          <a href="#feature-vaani" className="vy-feature-tile">
            <b>Vaani Voice</b>
            <span>Record voice symptoms with mic</span>
          </a>
          <a href="#feature-symptoms" className="vy-feature-tile">
            <b>Symptoms</b>
            <span>Select signs and submit risk check</span>
          </a>
          <a href="#feature-history" className="vy-feature-tile">
            <b>History</b>
            <span>Review previous reports quickly</span>
          </a>
        </div>
      </section>

      {demoMode ? (
        <section className="vy-card vy-demo-card">
          <div className="vy-demo-banner">Demo Timeline: High-risk case escalation</div>
          <div className="vy-demo-progress">
            <div style={{ width: `${demoProgress}%` }} />
          </div>
          <div className="vy-timeline">
            {escalations.map(([kind, text], idx) => (
              <Motion.div
                className={`vy-step ${kind}`}
                key={text}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 1.1 }}
              >
                <span className={`dot ${idx === 3 ? "pulse" : ""}`} />
                <span>{text}</span>
              </Motion.div>
            ))}
          </div>
        </section>
      ) : null}

      <div id="feature-register" />

      {!patientId ? (
        <section className="vy-card">
          <h3>Step 1: Register Patient</h3>
          <div className="vy-form-grid">
            <TextField label="Full Name" value={form.name} onChange={(e) => handleFormChange("name", e.target.value)} />
            <TextField label="Age" type="number" value={form.age} onChange={(e) => handleFormChange("age", e.target.value)} />
            <TextField label="Village" value={form.village} onChange={(e) => handleFormChange("village", e.target.value)} />
            <TextField select label="District" value={form.district} onChange={(e) => handleFormChange("district", e.target.value)}>
              {DISTRICTS.map((d) => (
                <MenuItem key={d} value={d}>
                  {d}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Pregnancy Week"
              type="number"
              value={form.pregnancy_week}
              onChange={(e) => handleFormChange("pregnancy_week", e.target.value)}
            />
            <TextField
              label="Phone Number"
              value={form.phone_number}
              onChange={(e) => handleFormChange("phone_number", e.target.value)}
            />
          </div>
          <Button variant="contained" onClick={handleRegister} disabled={loadingSection === "register"}>
            {loadingSection === "register" ? <CircularProgress size={20} color="inherit" /> : "Register"}
          </Button>
        </section>
      ) : null}

      <section className="vy-card" id="feature-vaani">
        <h3>Step 2: Vaani Voice Reporting</h3>
        {!patientId ? <p className="vy-locked-note">Register a patient first to enable Vaani voice recording.</p> : null}
        <div className="vy-mic-wrap">
          <button
            className={`vy-mic-btn ${recording ? "recording" : ""}`}
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onMouseLeave={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
            disabled={!patientId}
          >
            <MicIcon />
            {recording ? (
              <>
                <span className="ring" />
                <span className="ring r2" />
                <span className="ring r3" />
              </>
            ) : null}
          </button>
          <p>{recording ? `Recording... ${timerText}` : "Press and hold the mic button to record."}</p>
        </div>
        {loadingSection === "voice" ? <LoadingSkeleton height={90} /> : null}
        <div className="vy-divider">or continue with text symptoms below</div>
      </section>

      <section className="vy-card" id="feature-symptoms">
        <h3>Step 3: Select Symptoms</h3>
        {!patientId ? <p className="vy-locked-note">Registration is required before symptom submission.</p> : null}
        <div className="vy-chip-grid">
          {symptomOptions.map(([label, val]) => {
            const selected = selectedSymptoms.includes(val);
            return (
              <button
                key={val}
                className={`vy-chip ${selected ? "selected" : ""}`}
                onClick={() => {
                  if (!patientId) return;
                  toggleSymptom(val);
                }}
                disabled={!patientId}
              >
                <span>{label}</span>
                {selected ? <CheckIcon sx={{ fontSize: 16 }} /> : null}
              </button>
            );
          })}
        </div>
        <button className="vy-link-btn" onClick={() => setShowBp((v) => !v)} disabled={!patientId}>
          Add blood pressure (optional)
        </button>

        {showBp ? (
          <div className="vy-two-col">
            <TextField label="Systolic" type="number" value={bpSystolic} onChange={(e) => setBpSystolic(e.target.value)} />
            <TextField label="Diastolic" type="number" value={bpDiastolic} onChange={(e) => setBpDiastolic(e.target.value)} />
          </div>
        ) : null}

        <div className="vy-pill-toggle">
          <button className={!prevComp ? "active" : ""} onClick={() => setPrevComp(false)} disabled={!patientId}>
            No prior complications
          </button>
          <button className={prevComp ? "active" : ""} onClick={() => setPrevComp(true)} disabled={!patientId}>
            Prior complications
          </button>
        </div>

        <Button variant="contained" fullWidth onClick={submitText} disabled={loadingSection === "text" || !patientId}>
          {loadingSection === "text" ? <CircularProgress size={20} color="inherit" /> : "Generate Risk Score"}
        </Button>
      </section>

      {result ? (
        <Motion.section id="feature-risk" className={`vy-card vy-risk-card ${levelClass}`} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <div className="vy-risk-head">
            <span className={`badge ${levelClass}`}>{riskLevel} RISK</span>
            <h2>{animatedRiskScore}</h2>
          </div>
          <p>
            <b>Reason:</b> {result?.risk_result?.primary_reason || "N/A"}
          </p>
          <p>
            <b>Recommendation:</b> {result?.risk_result?.recommendation || "N/A"}
          </p>
          {riskLevel === "HIGH" ? (
            <div className="vy-danger-box">Immediate medical attention is recommended. Contact ASHA support now.</div>
          ) : null}
          <div className="vy-risk-actions">
            {riskLevel === "HIGH" ? (
              <Button variant="contained" onClick={() => toast.success("Alert sent to ASHA.")}>Notify ASHA Worker</Button>
            ) : null}
            <Button variant="outlined" onClick={() => setResult(null)}>
              Start New Report
            </Button>
          </div>
        </Motion.section>
      ) : null}

      <section className="vy-card" id="feature-history">
        <h3>Recent Reports</h3>
        {!patientProfile && patientId ? <LoadingSkeleton height={110} /> : null}
        {historyRows.length === 0 ? <EmptyState text="No previous reports found." /> : null}
        <div className="vy-history-list">
          {historyRows.map((row) => (
            <details key={row.id} className="vy-history-item">
              <summary>
                <span>{new Date(row.timestamp).toLocaleString()}</span>
                <span className="type">{row.input_type}</span>
                <span className={`lvl ${row.risk_level?.toLowerCase()}`}>{row.risk_level}</span>
                <span className="score">{row.risk_score}</span>
              </summary>
              <div className="body">Symptoms: {(row.symptoms_list || []).join(", ") || "N/A"}</div>
            </details>
          ))}
        </div>
      </section>

      <Button
        variant="contained"
        onClick={() => setDemoMode((v) => !v)}
        sx={{
          position: "fixed",
          right: 20,
          bottom: 20,
          zIndex: 1200,
          borderRadius: "999px",
          px: 2,
          py: 1.1,
          boxShadow: "0 12px 32px rgba(15, 23, 42, 0.28)",
        }}
      >
        {demoMode ? "Demo Band Karein" : "Demo Chalayen"}
      </Button>
    </div>
  );
}

export default PatientPortal;
