import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import FavoriteIcon from "@mui/icons-material/Favorite";
import SecurityIcon from "@mui/icons-material/Security";
import SpatialAudioOffIcon from "@mui/icons-material/SpatialAudioOff";
import EscalatorWarningIcon from "@mui/icons-material/EscalatorWarning";
import LocalHospitalIcon from "@mui/icons-material/LocalHospital";
import MapIcon from "@mui/icons-material/Map";
import RecordVoiceOverIcon from "@mui/icons-material/RecordVoiceOver";
import HubIcon from "@mui/icons-material/Hub";
import CloseIcon from "@mui/icons-material/Close";
import toast from "react-hot-toast";
import api from "../api/axios";

import VyanaHeader from "../components/VyanaHeader";
import VoiceAssistantHero from "../components/VoiceAssistantHero";
import ConversationStream from "../components/ConversationStream";
import HealthKnowledgeLibrary from "../components/HealthKnowledgeLibrary";
import EmergencySOSModal from "../components/EmergencySOSModal";
import VyanaBottomNav from "../components/VyanaBottomNav";

const INITIAL_MESSAGES_HI = [
  {
    id: "init-1",
    sender: "assistant",
    text: "नमस्ते! मैं आपकी व्यान स्वास्थ्य दीदी हूँ। 🙏\nआप गर्भावस्था में कैसा महसूस कर रही हैं? कोई दर्द, कमजोरी या समस्या हो तो नीचे माइक का बटन दबाकर सीधे बोलें। मैं हमेशा आपकी मदद के लिए यहाँ हूँ।",
    timestamp: "अभी",
  },
];

const INITIAL_MESSAGES_EN = [
  {
    id: "init-1",
    sender: "assistant",
    text: "Hello! I am your Vyana Care Health Companion. 🙏\nHow are you feeling today? If you have any discomfort, pain, or health questions, simply tap the microphone below and speak naturally. I am here to assist you.",
    timestamp: "Just now",
  },
];

export default function VyanaHome() {
  const [lang, setLang] = useState(() => localStorage.getItem("vyana_lang") || "hi");
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingCount, setPendingCount] = useState(() => {
    try {
      const q = JSON.parse(localStorage.getItem("vyana_offline_queue") || "[]");
      return q.length;
    } catch {
      return 0;
    }
  });

  const [activeSection, setActiveSection] = useState("home");
  const [sosOpen, setSosOpen] = useState(false);
  const [staffMenuOpen, setStaffMenuOpen] = useState(false);

  const [messages, setMessages] = useState(() => {
    try {
      const cached = localStorage.getItem("vyana_conversation_history");
      if (cached) {
        const parsed = JSON.parse(cached);
        if (parsed.length > 0) return parsed;
      }
    } catch {
      // ignore
    }
    return lang === "hi" ? INITIAL_MESSAGES_HI : INITIAL_MESSAGES_EN;
  });

  // Language update & persistence
  useEffect(() => {
    localStorage.setItem("vyana_lang", lang);
    if (messages.length === 1 && messages[0].id === "init-1") {
      setMessages(lang === "hi" ? INITIAL_MESSAGES_HI : INITIAL_MESSAGES_EN);
    }
  }, [lang]);

  // Persist messages
  useEffect(() => {
    try {
      localStorage.setItem("vyana_conversation_history", JSON.stringify(messages));
    } catch {
      // ignore
    }
  }, [messages]);

  // Fetch past consultations from backend
  useEffect(() => {
    async function loadPastConsultations() {
      if (!navigator.onLine) return;
      try {
        const res = await api.get("/patient/1/history?limit=4");
        if (res.data?.success && res.data?.data?.consultations?.length) {
          const list = res.data.data.consultations.reverse();
          const restored = [lang === "hi" ? INITIAL_MESSAGES_HI[0] : INITIAL_MESSAGES_EN[0]];
          for (const item of list) {
            restored.push({
              id: `user-${item.id}`,
              sender: "user",
              text: item.user_text,
              timestamp: item.timestamp,
            });
            const isHi = lang === "hi";
            const reply = item.risk_level === "HIGH"
              ? (isHi ? `⚠️ ध्यान दें: ${item.primary_reason || "गंभीर लक्षण"}` : `⚠️ Alert: ${item.primary_reason || "High risk symptoms"}`)
              : (isHi ? `✅ नियमित सलाह: ${item.primary_reason || "सब ठीक है"}` : `✅ Reassuring: ${item.primary_reason || "All looks normal"}`);
            restored.push({
              id: `asst-${item.id}`,
              sender: "assistant",
              text: reply,
              riskResult: { level: item.risk_level, score: item.risk_score, primary_reason: item.primary_reason },
              timestamp: item.timestamp,
            });
          }
          setMessages(restored);
        }
      } catch {
        // use local state
      }
    }
    loadPastConsultations();
  }, [lang]);

  // Online / Offline monitor & sync queue
  useEffect(() => {
    const handleOnline = async () => {
      setIsOnline(true);
      toast.success(lang === "hi" ? "इंटरनेट जुड़ गया! डेटा सिंक हो रहा है" : "Internet connected! Data syncing");
      // Flush offline queue if present
      try {
        const q = JSON.parse(localStorage.getItem("vyana_offline_queue") || "[]");
        if (q.length > 0) {
          for (const item of q) {
            if (item.type === "text" && item.symptoms) {
              await api.post("/symptom/report/text", {
                patient_id: 1,
                symptoms: item.symptoms,
                bp_systolic: 120,
                bp_diastolic: 80,
                pregnancy_week: 28,
              });
            }
          }
          localStorage.removeItem("vyana_offline_queue");
          setPendingCount(0);
          toast.success(lang === "hi" ? "ऑफ़लाइन रिपोर्ट सिंक हो गई!" : "Offline reports synced to server!");
        }
      } catch {
        // ignore
      }
    };
    const handleOffline = () => {
      setIsOnline(false);
      toast(lang === "hi" ? "ऑफ़लाइन मोड: आप अभी भी जानकारी पढ़ और बोल सकते हैं" : "Offline mode: You can still speak and read guides", {
        icon: "📡",
      });
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [lang]);

  const handleQueueOffline = (item) => {
    const existing = JSON.parse(localStorage.getItem("vyana_offline_queue") || "[]");
    existing.push(item);
    localStorage.setItem("vyana_offline_queue", JSON.stringify(existing));
    setPendingCount(existing.length);
    toast.success(lang === "hi" ? "ऑफ़लाइन सुरक्षित किया गया! नेटवर्क आने पर सिंक होगा।" : "Saved offline! Will sync when connected.");
  };

  const handleNewReport = ({ userText, symptoms, riskResult, timestamp }) => {
    const isHi = lang === "hi";
    
    // User message
    const userMsg = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: userText,
      timestamp: timestamp || "अभी",
    };

    // AI Assistant response based on risk result
    let replyText = "";
    if (riskResult?.level === "HIGH") {
      replyText = isHi
        ? `⚠️ ध्यान दें: ${riskResult.primary_reason || "गंभीर लक्षण पाए गए हैं"}\n\n${riskResult.recommendation || "तुरंत डॉक्टर के पास जाएं।"}\n\nआपकी आशा दीदी और निकटतम अस्पताल को आपातकालीन सूचना भेज दी गई है। कृपया घबराएं नहीं और आराम करें।`
        : `⚠️ Alert: ${riskResult.primary_reason || "High risk symptoms detected"}\n\n${riskResult.recommendation || "Please visit the nearest health centre immediately."}\n\nAn urgent notification has been queued for your ASHA worker.`;
    } else if (riskResult?.level === "MEDIUM") {
      replyText = isHi
        ? `⚠️ ${riskResult.primary_reason || "मध्यम लक्षण"}\n\n${riskResult.recommendation || "अगले 24 घंटे में आशा दीदी से मिलें।"}\n\nखूब पानी पिएं और पर्याप्त आराम करें।`
        : `⚠️ Notice: ${riskResult.primary_reason || "Moderate symptoms detected"}\n\n${riskResult.recommendation || "Consult your ASHA worker within 24 hours."}\n\nStay well-hydrated and rest.`;
    } else {
      replyText = isHi
        ? `✅ सब ठीक लग रहा है! कोई बड़ा खतरा नहीं पाया गया।\n\n${riskResult?.recommendation || "नियमित जांच समय पर कराते रहें और पौष्टिक आहार लें।"}\n\nयदि बाद में कोई नया लक्षण दिखे, तो मुझे दोबारा बताएं।`
        : `✅ Everything looks reassuring! No major risk indicators found.\n\n${riskResult?.recommendation || "Continue your routine checkups and healthy diet."}`;
    }

    const assistantMsg = {
      id: `asst-${Date.now() + 1}`,
      sender: "assistant",
      text: replyText,
      riskResult,
      timestamp: "अभी",
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
  };

  const isHi = lang === "hi";

  return (
    <div className="vy-maternal-app">
      {/* Top Glass Navigation */}
      <VyanaHeader
        lang={lang}
        setLang={setLang}
        isOnline={isOnline}
        pendingCount={pendingCount}
        onOpenSos={() => setSosOpen(true)}
      />

      <main className="vy-container">
        {/* Welcoming Hero Section */}
        <section className="vy-hero-section">
          <div className="vy-hero-badge">
            <SecurityIcon style={{ fontSize: "16px" }} />
            <span>{isHi ? "सुरक्षित व विश्वसनीय मातृ स्वास्थ्य" : "Trusted Rural Maternal Care"}</span>
          </div>

          <h2 className="vy-hero-title">
            {isHi ? (
              <>
                स्वस्थ मां, सुरक्षित बच्चा — <span className="highlight-coral">व्यान केयर</span>
              </>
            ) : (
              <>
                Healthy Mother, Safe Baby — <span className="highlight-coral">Vyana Care</span>
              </>
            )}
          </h2>

          <p className="vy-hero-subtitle">
            {isHi
              ? "ग्रामीण माताओं के लिए सरल व सुरक्षित स्वास्थ्य परामर्श। बिना लिखे, केवल अपनी भाषा में बोलकर तुरंत डॉक्टर जैसी सलाह पाएं।"
              : "Voice-guided clinical maternal guidance designed for rural Indian families. No typing needed — speak naturally in Hindi or Hinglish."}
          </p>
        </section>

        {/* Central Voice Assistant Interface */}
        <VoiceAssistantHero
          lang={lang}
          patientId={1}
          isOnline={isOnline}
          onNewReport={handleNewReport}
          onQueueOffline={handleQueueOffline}
        />

        {/* Conversation / Consultation Stream */}
        <ConversationStream
          lang={lang}
          messages={messages}
          onOpenSos={() => setSosOpen(true)}
        />

        {/* Emergency SOS Banner */}
        <section className="vy-emergency-banner">
          <div className="vy-emergency-info">
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <LocalHospitalIcon style={{ fontSize: "24px" }} />
              <h3>{isHi ? "आपातकालीन स्थिति में तुरंत मदद" : "24/7 Maternal Emergency Hotline"}</h3>
            </div>
            <p>
              {isHi
                ? "तेज रक्तस्राव, गंभीर सिरदर्द या प्रसव पीड़ा होने पर सीधे 108 या आशा दीदी को कॉल करें।"
                : "Free 108 ambulance dispatch and direct contact with village health workers."}
            </p>
          </div>

          <button
            type="button"
            className="vy-emergency-action-btn"
            onClick={() => setSosOpen(true)}
          >
            🚨 {isHi ? "1-क्लिक आपातकालीन कॉल" : "1-Tap Emergency SOS"}
          </button>
        </section>

        {/* Health Knowledge Base (Offline-accessible) */}
        <div id="knowledge-section">
          <HealthKnowledgeLibrary lang={lang} />
        </div>

        {/* Frontline & District Portals Hub Cards */}
        <section style={{ marginTop: "32px", marginBottom: "40px" }}>
          <div className="vy-section-header">
            <h3 className="vy-section-title">
              <span className="vy-section-icon">👩‍⚕️</span>
              <span>{isHi ? "स्वास्थ्य कार्यकर्ता व जिला पोर्टल" : "Frontline Worker & District Portals"}</span>
            </h3>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
            <Link to="/asha" style={{ textDecoration: "none" }}>
              <div className="vy-knowledge-card" style={{ height: "100%", cursor: "pointer" }}>
                <div className="vy-kc-icon-box" style={{ background: "var(--vy-teal-soft)" }}>
                  <EscalatorWarningIcon />
                </div>
                <h4>{isHi ? "आशा कार्यकर्ता डैशबोर्ड" : "ASHA Worker Portal"}</h4>
                <p>{isHi ? "गर्भवती महिलाओं की सूची, ट्राइएज और अलर्ट्स देखें।" : "Triage patients, acknowledge high-risk alerts, and log home visits."}</p>
                <span className="vy-kc-tag">{isHi ? "खोलें →" : "Open Portal →"}</span>
              </div>
            </Link>

            <Link to="/awaaz" style={{ textDecoration: "none" }}>
              <div className="vy-knowledge-card" style={{ height: "100%", cursor: "pointer" }}>
                <div className="vy-kc-icon-box" style={{ background: "var(--vy-coral-soft)", color: "var(--vy-coral-dark)" }}>
                  <RecordVoiceOverIcon />
                </div>
                <h4>{isHi ? "वाणी - मातृ आवाज समुदाय" : "Vaani - Community Audio"}</h4>
                <p>{isHi ? "ग्रामीण माताओं के अनुभव, ऑडियो सलाह और सामुदायिक फीड।" : "Listen to verified audio experiences shared by rural mothers."}</p>
                <span className="vy-kc-tag" style={{ background: "var(--vy-coral-soft)", color: "var(--vy-coral-dark)" }}>{isHi ? "खोलें →" : "Open Community →"}</span>
              </div>
            </Link>

            <Link to="/district" style={{ textDecoration: "none" }}>
              <div className="vy-knowledge-card" style={{ height: "100%", cursor: "pointer" }}>
                <div className="vy-kc-icon-box" style={{ background: "var(--vy-sage-soft)", color: "#237A70" }}>
                  <MapIcon />
                </div>
                <h4>{isHi ? "जिला स्वास्थ्य विश्लेषिकी" : "District Analytics & GIS"}</h4>
                <p>{isHi ? "बाड़मेर व जैसलमेर जिले का लाइव हीटमैप और डेटा।" : "Interactive GIS map with high-risk epidemiological hot spots."}</p>
                <span className="vy-kc-tag" style={{ background: "var(--vy-sage-soft)", color: "#237A70" }}>{isHi ? "खोलें →" : "Open Analytics →"}</span>
              </div>
            </Link>

            <Link to="/integrations" style={{ textDecoration: "none" }}>
              <div className="vy-knowledge-card" style={{ height: "100%", cursor: "pointer" }}>
                <div className="vy-kc-icon-box" style={{ background: "var(--vy-sun-soft)", color: "#9C4221" }}>
                  <HubIcon />
                </div>
                <h4>{isHi ? "सरकारी स्वास्थ्य एकीकरण" : "Govt Health Integrations"}</h4>
                <p>{isHi ? "ABHA आईडी, HMIS रिपोर्ट व 108 एम्बुलेंस ट्रैकिंग।" : "ABHA digital health ID linking, HMIS export & 108 dispatch."}</p>
                <span className="vy-kc-tag" style={{ background: "var(--vy-sun-soft)", color: "#9C4221" }}>{isHi ? "खोलें →" : "Open Integrations →"}</span>
              </div>
            </Link>
          </div>
        </section>
      </main>

      {/* Emergency SOS Modal Drawer */}
      <EmergencySOSModal
        lang={lang}
        isOpen={sosOpen}
        onClose={() => setSosOpen(false)}
      />

      {/* Staff Portals Quick Switcher Modal */}
      {staffMenuOpen && (
        <div className="vy-modal-overlay" onClick={() => setStaffMenuOpen(false)}>
          <div className="vy-sos-modal" style={{ borderTopColor: "var(--vy-teal-primary)" }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ margin: 0, color: "var(--vy-teal-primary)" }}>
                {isHi ? "सभी स्वास्थ्य पोर्टल" : "Vyana Care Portals"}
              </h3>
              <button
                type="button"
                onClick={() => setStaffMenuOpen(false)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--vy-text-soft)" }}
              >
                <CloseIcon />
              </button>
            </div>

            <div className="vy-sos-buttons-stack">
              <Link to="/asha" className="vy-sos-hotline-btn asha" onClick={() => setStaffMenuOpen(false)}>
                <span>👩‍⚕️ {isHi ? "आशा कार्यकर्ता डैशबोर्ड" : "ASHA Worker Dashboard"}</span>
                <span>→</span>
              </Link>
              <Link to="/district" className="vy-sos-hotline-btn asha" onClick={() => setStaffMenuOpen(false)}>
                <span>🗺️ {isHi ? "जिला अधिकारी हीटमैप व विश्लेषण" : "District Officer GIS & Analytics"}</span>
                <span>→</span>
              </Link>
              <Link to="/awaaz" className="vy-sos-hotline-btn asha" onClick={() => setStaffMenuOpen(false)}>
                <span>🎙️ {isHi ? "वाणी - सामुदायिक आवाज मंच" : "Vaani Community Audio Platform"}</span>
                <span>→</span>
              </Link>
              <Link to="/awaaz/nurse" className="vy-sos-hotline-btn asha" onClick={() => setStaffMenuOpen(false)}>
                <span>🏥 {isHi ? "नर्स मॉडरेशन पैनल" : "Nurse Moderation Queue"}</span>
                <span>→</span>
              </Link>
              <Link to="/integrations" className="vy-sos-hotline-btn asha" onClick={() => setStaffMenuOpen(false)}>
                <span>🏛️ {isHi ? "ABHA, HMIS व 108 सरकारी एकीकरण" : "ABHA & 108 Integrations"}</span>
                <span>→</span>
              </Link>
            </div>

            <button type="button" className="vy-sos-close-btn" onClick={() => setStaffMenuOpen(false)}>
              {isHi ? "बंद करें" : "Close"}
            </button>
          </div>
        </div>
      )}

      {/* Mobile-Friendly Bottom Navigation Dock */}
      <VyanaBottomNav
        lang={lang}
        activeSection={activeSection}
        setActiveSection={setActiveSection}
        onOpenSos={() => setSosOpen(true)}
        onOpenStaffMenu={() => setStaffMenuOpen(true)}
      />
    </div>
  );
}
