import { useEffect, useRef, useState } from "react";
import MicIcon from "@mui/icons-material/Mic";
import StopIcon from "@mui/icons-material/Stop";
import GraphicEqIcon from "@mui/icons-material/GraphicEq";
import SendIcon from "@mui/icons-material/Send";
import SparklesIcon from "@mui/icons-material/AutoAwesome";
import VolumeUpIcon from "@mui/icons-material/VolumeUp";
import toast from "react-hot-toast";
import api from "../api/axios";

const QUICK_SYMPTOMS_HI = [
  { label: "सिर में तेज दर्द", val: "headache", icon: "🤕" },
  { label: "हाथ-पैर में सूजन", val: "swelling", icon: "🦶" },
  { label: "आंखों के आगे धुंधलापन", val: "blurred_vision", icon: "👁️" },
  { label: "खून या रक्तस्राव", val: "bleeding", icon: "🩸" },
  { label: "तेज बुखार", val: "fever", icon: "🌡️" },
  { label: "बच्चे की हलचल कम होना", val: "reduced_fetal_movement", icon: "👶" },
  { label: "चक्कर या कमजोरी", val: "dizziness", icon: "💫" },
  { label: "उल्टी या जी मिचलाना", val: "nausea", icon: "🤢" },
];

const QUICK_SYMPTOMS_EN = [
  { label: "Severe Headache", val: "headache", icon: "🤕" },
  { label: "Hand/Foot Swelling", val: "swelling", icon: "🦶" },
  { label: "Blurred Vision", val: "blurred_vision", icon: "👁️" },
  { label: "Bleeding", val: "bleeding", icon: "🩸" },
  { label: "High Fever", val: "fever", icon: "🌡️" },
  { label: "Reduced Baby Movement", val: "reduced_fetal_movement", icon: "👶" },
  { label: "Dizziness & Fatigue", val: "dizziness", icon: "💫" },
  { label: "Nausea & Vomiting", val: "nausea", icon: "🤢" },
];

export default function VoiceAssistantHero({
  lang,
  patientId,
  isOnline,
  onNewReport,
  onQueueOffline,
}) {
  const isHi = lang === "hi";
  const [recording, setRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [status, setStatus] = useState("idle"); // idle | recording | processing | success
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [showTextInput, setShowTextInput] = useState(false);
  const [typedText, setTypedText] = useState("");

  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  useEffect(() => {
    if (recording) {
      timerRef.current = setInterval(() => {
        setRecordSeconds((s) => s + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
      setRecordSeconds(0);
    }
    return () => clearInterval(timerRef.current);
  }, [recording]);

  const toggleSymptom = (val) => {
    setSelectedSymptoms((prev) =>
      prev.includes(val) ? prev.filter((s) => s !== val) : [...prev, val]
    );
  };

  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        setStatus("processing");
        try {
          const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
          
          if (!isOnline) {
            onQueueOffline?.({
              type: "voice",
              timestamp: new Date().toISOString(),
              message: isHi ? "ऑफ़लाइन आवाज़ रिकॉर्ड की गई" : "Offline voice recorded",
            });
            setStatus("idle");
            return;
          }

          const fd = new FormData();
          fd.append("patient_id", String(patientId || 1));
          fd.append("audio_file", audioBlob, "maternal_voice.webm");

          const res = await api.post("/symptom/report/voice", fd, {
            headers: { "Content-Type": "multipart/form-data" },
          });

          const data = res.data?.data;
          setStatus("idle");
          toast.success(isHi ? "आवाज समझी गई!" : "Voice analyzed!");

          onNewReport?.({
            userText: data?.transcription || (isHi ? "आवाज़ संदेश" : "Voice Message"),
            symptoms: data?.symptoms || [],
            riskResult: data?.risk_result,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            audioBlob,
          });
        } catch (err) {
          setStatus("idle");
          toast.error(isHi ? "आवाज प्रोसेस नहीं हो पाई। कृपया दोबारा प्रयास करें।" : "Could not process audio. Please retry.");
        } finally {
          stream.getTracks().forEach((track) => track.stop());
        }
      };

      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
      setStatus("recording");
    } catch (err) {
      toast.error(isHi ? "माइक्रोफोन की अनुमति नहीं मिली।" : "Microphone access denied.");
    }
  };

  const stopVoiceRecording = () => {
    if (recorderRef.current && recorderRef.current.state === "recording") {
      recorderRef.current.stop();
      setRecording(false);
    }
  };

  const submitManualSymptoms = async () => {
    if (selectedSymptoms.length === 0 && !typedText.trim()) {
      toast.error(isHi ? "कृपया लक्षण चुनें या लिखें" : "Please select or type symptoms");
      return;
    }

    setStatus("processing");
    try {
      const payload = {
        patient_id: Number(patientId || 1),
        symptoms: selectedSymptoms,
        bp_systolic: 120,
        bp_diastolic: 80,
        age: 28,
        pregnancy_week: 28,
        days_since_last_checkup: 0,
        previous_complications: false,
      };

      if (!isOnline) {
        onQueueOffline?.({
          type: "text",
          symptoms: selectedSymptoms,
          timestamp: new Date().toISOString(),
        });
        setStatus("idle");
        setSelectedSymptoms([]);
        return;
      }

      const res = await api.post("/symptom/report/text", payload);
      const data = res.data?.data;
      setStatus("idle");
      toast.success(isHi ? "स्वास्थ्य रिपोर्ट तैयार है" : "Health report ready");

      onNewReport?.({
        userText: typedText || (isHi ? selectedSymptoms.join(", ") : selectedSymptoms.join(", ")),
        symptoms: selectedSymptoms,
        riskResult: data?.risk_result,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });

      setSelectedSymptoms([]);
      setTypedText("");
    } catch (err) {
      setStatus("idle");
      toast.error(isHi ? "रिपोर्ट सबमिट नहीं हो सकी" : "Failed to submit report");
    }
  };

  const quickSymptomsList = isHi ? QUICK_SYMPTOMS_HI : QUICK_SYMPTOMS_EN;
  const timerFormat = `${String(Math.floor(recordSeconds / 60)).padStart(2, "0")}:${String(recordSeconds % 60).padStart(2, "0")}`;

  return (
    <div className="vy-voice-card">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", marginBottom: "8px" }}>
        <SparklesIcon style={{ color: "var(--vy-coral-primary)", fontSize: "20px" }} />
        <span style={{ fontSize: "14px", fontWeight: 700, color: "var(--vy-teal-primary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
          {isHi ? "बोलकर अपनी बात बताएं" : "AI Voice Health Assistant"}
        </span>
      </div>

      <div className="vy-voice-prompt">
        {status === "recording"
          ? (isHi ? "दीदी सुन रही हैं... अपनी परेशानी बताएं" : "Listening... please speak clearly")
          : status === "processing"
          ? (isHi ? "आपकी बात का विश्लेषण हो रहा है..." : "Analyzing your symptoms with clinical risk model...")
          : (isHi ? "माइक का बटन दबाएं और आराम से अपनी समस्या बताएं" : "Tap the microphone and tell us how you are feeling")}
      </div>

      {/* Central Interactive Mic Button with Ripples */}
      <div className="vy-mic-wrapper">
        <button
          type="button"
          className={`vy-mic-btn ${recording ? "recording" : ""}`}
          onClick={recording ? stopVoiceRecording : startVoiceRecording}
          disabled={status === "processing"}
          aria-label={recording ? "Stop recording" : "Start speaking"}
        >
          {status === "processing" ? (
            <GraphicEqIcon style={{ fontSize: "40px", animation: "vyMicBeat 1s infinite" }} />
          ) : recording ? (
            <StopIcon style={{ fontSize: "44px" }} />
          ) : (
            <MicIcon style={{ fontSize: "46px" }} />
          )}
        </button>

        {/* Dynamic Ripple Rings */}
        <div className="vy-ripple-ring" />
        <div className="vy-ripple-ring" />
        <div className="vy-ripple-ring" />
      </div>

      {/* Waveform Animation during recording */}
      {recording ? (
        <div>
          <div className="vy-waveform-container">
            <div className="vy-wave-bar" />
            <div className="vy-wave-bar" />
            <div className="vy-wave-bar" />
            <div className="vy-wave-bar" />
            <div className="vy-wave-bar" />
            <div className="vy-wave-bar" />
            <div className="vy-wave-bar" />
          </div>
          <span className="vy-mic-timer">⏱ {timerFormat}</span>
          <div style={{ marginTop: "10px" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--vy-coral-dark)" }}>
              {isHi ? "बोलने के बाद 'रोकें' बटन पर दबाएं" : "Tap stop when finished speaking"}
            </span>
          </div>
        </div>
      ) : (
        <div className="vy-voice-hint">
          {isHi
            ? "💡 आप हिंदी, मारवाड़ी या हिंग्लिश में बोल सकती हैं। (जैसे: 'सिर बहुत दुख रहा है और पैरों में सूजन है')"
            : "💡 Speak naturally in Hindi, Hinglish, or English. We understand regional accents & symptoms."}
        </div>
      )}

      {/* Quick Selectable Symptoms for Easy Low-Literacy Tap Interaction */}
      <div style={{ marginTop: "28px", borderTop: "1px solid rgba(13, 92, 99, 0.08)", paddingTop: "20px" }}>
        <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--vy-text-body)", marginBottom: "12px", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
          <span>{isHi ? "या सीधे लक्षण छूकर चुनें:" : "Or tap common symptoms directly:"}</span>
        </div>
        
        <div className="vy-quick-symptoms" style={{ justifyContent: "center" }}>
          {quickSymptomsList.map((item) => {
            const isSelected = selectedSymptoms.includes(item.val);
            return (
              <button
                key={item.val}
                type="button"
                className={`vy-symptom-chip ${isSelected ? "selected" : ""}`}
                onClick={() => toggleSymptom(item.val)}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {selectedSymptoms.length > 0 && (
          <div style={{ marginTop: "16px" }}>
            <button
              type="button"
              className="vy-header-sos-btn"
              style={{ background: "linear-gradient(135deg, var(--vy-teal-primary), var(--vy-teal-light))", margin: "0 auto", padding: "10px 24px" }}
              onClick={submitManualSymptoms}
            >
              <SendIcon style={{ fontSize: "16px" }} />
              <span>{isHi ? `जांच करें (${selectedSymptoms.length} लक्षण)` : `Check Symptoms (${selectedSymptoms.length})`}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
