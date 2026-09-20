import { useState } from "react";
import VolumeUpIcon from "@mui/icons-material/VolumeUp";
import StopIcon from "@mui/icons-material/Stop";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import PersonIcon from "@mui/icons-material/Person";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import toast from "react-hot-toast";

export default function ConversationStream({ lang, messages = [], onOpenSos }) {
  const isHi = lang === "hi";
  const [speakingIndex, setSpeakingIndex] = useState(null);

  const speakText = (text, index) => {
    if (!("speechSynthesis" in window)) {
      toast.error(isHi ? "ऑडियो उपलब्ध नहीं है" : "Text to speech not supported");
      return;
    }

    if (speakingIndex === index) {
      window.speechSynthesis.cancel();
      setSpeakingIndex(null);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = isHi ? "hi-IN" : "en-IN";
    utterance.rate = 0.95;

    utterance.onend = () => setSpeakingIndex(null);
    utterance.onerror = () => setSpeakingIndex(null);

    setSpeakingIndex(index);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <section className="vy-chat-section">
      <div className="vy-section-header">
        <h3 className="vy-section-title">
          <span className="vy-section-icon">💬</span>
          <span>{isHi ? "आपकी और दीदी की बातचीत" : "Your Consultation History"}</span>
        </h3>
        <span style={{ fontSize: "13px", color: "var(--vy-text-soft)", fontWeight: 600 }}>
          {messages.length} {isHi ? "संदेश" : "messages"}
        </span>
      </div>

      <div className="vy-chat-stream">
        {messages.map((msg, index) => {
          const isUser = msg.sender === "user";
          const riskLevel = msg.riskResult?.level;
          const score = msg.riskResult?.score;

          return (
            <div
              key={msg.id || index}
              className={`vy-chat-bubble ${isUser ? "user" : "assistant"}`}
            >
              <div className="vy-bubble-meta">
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  {isUser ? (
                    <>
                      <PersonIcon style={{ fontSize: "16px", color: "var(--vy-coral-primary)" }} />
                      <span>{isHi ? "माता / आप" : "You (Mother)"}</span>
                    </>
                  ) : (
                    <>
                      <SupportAgentIcon style={{ fontSize: "18px", color: "var(--vy-teal-primary)" }} />
                      <span>{isHi ? "व्यान स्वास्थ्य साथी" : "Vyana Care Sister"}</span>
                    </>
                  )}
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span>{msg.timestamp}</span>

                  {!isUser && (
                    <button
                      type="button"
                      className="vy-bubble-audio-btn"
                      onClick={() => speakText(msg.text, index)}
                      title={isHi ? "आवाज में सुनें" : "Listen to audio"}
                    >
                      {speakingIndex === index ? (
                        <>
                          <StopIcon style={{ fontSize: "14px" }} />
                          <span>{isHi ? "रोकें" : "Stop"}</span>
                        </>
                      ) : (
                        <>
                          <VolumeUpIcon style={{ fontSize: "14px" }} />
                          <span>{isHi ? "सुनें" : "Listen"}</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>

              {/* Message text content */}
              <div style={{ fontSize: "15px", whiteSpace: "pre-wrap" }}>
                {msg.text}
              </div>

              {/* Clinical Risk Badge & Action Guidance */}
              {msg.riskResult && (
                <div style={{ marginTop: "12px", borderTop: "1px solid rgba(13, 92, 99, 0.1)", paddingTop: "10px" }}>
                  <div
                    className={`vy-risk-badge ${
                      riskLevel === "HIGH" ? "high" : riskLevel === "MEDIUM" ? "medium" : "low"
                    }`}
                  >
                    {riskLevel === "HIGH" ? (
                      <ErrorOutlineIcon style={{ fontSize: "16px" }} />
                    ) : riskLevel === "MEDIUM" ? (
                      <WarningAmberIcon style={{ fontSize: "16px" }} />
                    ) : (
                      <CheckCircleOutlineIcon style={{ fontSize: "16px" }} />
                    )}
                    <span>
                      {isHi
                        ? riskLevel === "HIGH"
                          ? `⚠️ उच्च जोखिम (स्कोर: ${score || 89}) - तुरंत डॉक्टर या आशा दीदी से मिलें`
                          : riskLevel === "MEDIUM"
                          ? `⚠️ मध्यम जोखिम (स्कोर: ${score || 45}) - 24 घंटे में जांच कराएं`
                          : `✅ सामान्य स्थिति (स्कोर: ${score || 15}) - सब ठीक लग रहा है`
                        : `${riskLevel} Risk (Score: ${score || 20}) - ${
                            riskLevel === "HIGH" ? "Urgent care required" : "Routine checkup advised"
                          }`}
                    </span>
                  </div>

                  {riskLevel === "HIGH" && (
                    <div style={{ marginTop: "10px" }}>
                      <button
                        type="button"
                        className="vy-emergency-action-btn"
                        style={{ padding: "8px 18px", fontSize: "13px" }}
                        onClick={onOpenSos}
                      >
                        🚨 {isHi ? "आशा दीदी / 108 एम्बुलेंस को अभी कॉल करें" : "Call ASHA / 108 Emergency"}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
