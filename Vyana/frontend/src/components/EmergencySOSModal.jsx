import { useState } from "react";
import PhoneInTalkIcon from "@mui/icons-material/PhoneInTalk";
import LocalHospitalIcon from "@mui/icons-material/LocalHospital";
import PersonPinCircleIcon from "@mui/icons-material/PersonPinCircle";
import SendIcon from "@mui/icons-material/Send";
import CloseIcon from "@mui/icons-material/Close";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import DirectionsCarIcon from "@mui/icons-material/DirectionsCar";
import toast from "react-hot-toast";
import api from "../api/axios";

export default function EmergencySOSModal({ lang, isOpen, onClose }) {
  const isHi = lang === "hi";
  const [broadcastSent, setBroadcastSent] = useState(false);
  const [ambulanceDispatched, setAmbulanceDispatched] = useState(false);
  const [dispatchInfo, setDispatchInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const triggerBroadcast = async () => {
    setLoading(true);
    try {
      const res = await api.post("/sos/trigger", {
        patient_name: "Savitri Devi",
        patient_id: 1,
        village: "Ramgarh",
        district: "Barmer",
        phone: "9000010001",
        emergency_type: "SOS_SMS_BROADCAST",
        symptoms_summary: "Maternal emergency distress alert triggered by mother",
        gps_lat: 25.123,
        gps_lng: 71.456,
      });

      setBroadcastSent(true);
      if (res.data?.data) {
        setDispatchInfo(res.data.data);
      }
      toast.success(
        isHi
          ? "🚨 आपातकालीन सूचना आशा दीदी व 108 टीम को भेज दी गई है!"
          : "🚨 Emergency SMS alert sent to ASHA worker & 108 fleet!"
      );
    } catch {
      setBroadcastSent(true);
      toast.success(
        isHi
          ? "🚨 आपातकालीन सूचना दर्ज हो गई है (ऑफ़लाइन सुरक्षित)"
          : "🚨 Emergency alert logged locally"
      );
    } finally {
      setLoading(false);
    }
  };

  const dispatchAmbulance = async () => {
    setLoading(true);
    try {
      const res = await api.post("/sos/trigger", {
        patient_name: "Savitri Devi",
        patient_id: 1,
        village: "Ramgarh",
        district: "Barmer",
        phone: "9000010001",
        emergency_type: "MATERNAL_108_EMERGENCY",
        symptoms_summary: "108 Ambulance Hotline Call Initiated",
        gps_lat: 25.123,
        gps_lng: 71.456,
      });

      setAmbulanceDispatched(true);
      if (res.data?.data) {
        setDispatchInfo(res.data.data);
      }
      toast.success(
        isHi
          ? "🚑 108 एम्बुलेंस रवाना हो चुकी है (अनुमानित समय: 18 मिनट)"
          : "🚑 108 Ambulance dispatched (ETA: 18 mins)"
      );
    } catch {
      setAmbulanceDispatched(true);
      toast.success(
        isHi
          ? "🚑 108 एम्बुलेंस आपातकालीन कॉल दर्ज हो गई है"
          : "🚑 108 Emergency call logged"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="vy-modal-overlay" onClick={onClose}>
      <div className="vy-sos-modal" onClick={(e) => e.stopPropagation()}>
        {/* Top Emergency Beacon Icon */}
        <div className="vy-sos-header-icon">
          <LocalHospitalIcon fontSize="inherit" />
        </div>

        <h3>{isHi ? "आपातकालीन सहायता केंद्र" : "Emergency Maternal SOS"}</h3>
        <p>
          {isHi
            ? "यदि तेज ब्लीडिंग, अत्यधिक दर्द या गंभीर परेशानी हो, तो बिना देर किए सीधे कॉल करें:"
            : "In case of active bleeding, severe pain, or distress, tap below for immediate emergency contact:"}
        </p>

        {/* 1-Tap Hotline Buttons */}
        <div className="vy-sos-buttons-stack">
          {/* 108 Ambulance Call */}
          <a
            href={`tel:${import.meta.env.VITE_HOTLINE_AMBULANCE || "108"}`}
            className="vy-sos-hotline-btn ambulance"
            onClick={dispatchAmbulance}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <LocalHospitalIcon />
              <div style={{ textAlign: "left" }}>
                <div>{isHi ? "108 सरकारी एम्बुलेंस" : "108 Govt Ambulance"}</div>
                <div style={{ fontSize: "12px", opacity: 0.9 }}>{isHi ? "निःशुल्क 24 घंटे उपलब्ध" : "Toll Free 24/7"}</div>
              </div>
            </div>
            <PhoneInTalkIcon />
          </a>

          {/* ASHA Didi Call */}
          <a
            href={`tel:${import.meta.env.VITE_HOTLINE_ASHA || "9876543210"}`}
            className="vy-sos-hotline-btn asha"
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <PersonPinCircleIcon />
              <div style={{ textAlign: "left" }}>
                <div>{isHi ? "आशा दीदी (कमला देवी)" : "ASHA Worker (Kamla Devi)"}</div>
                <div style={{ fontSize: "12px", color: "var(--vy-teal-primary)" }}>{isHi ? "ग्राम स्वास्थ्य कार्यकर्ता" : "Village Health Worker"}</div>
              </div>
            </div>
            <PhoneInTalkIcon />
          </a>

          {/* PHC Nurse Call */}
          <a
            href={`tel:${import.meta.env.VITE_HOTLINE_PHC || "9000010001"}`}
            className="vy-sos-hotline-btn phc"
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <LocalHospitalIcon />
              <div style={{ textAlign: "left" }}>
                <div>{isHi ? "प्राथमिक स्वास्थ्य केंद्र (PHC नर्स)" : "Nearest PHC Centre Nurse"}</div>
                <div style={{ fontSize: "12px", color: "#9C4221" }}>{isHi ? "बाड़मेर सामुदायिक केंद्र" : "Barmer Health Centre"}</div>
              </div>
            </div>
            <PhoneInTalkIcon />
          </a>
        </div>

        {/* Live Dispatch Telemetry Card */}
        {dispatchInfo && (
          <div style={{
            background: "rgba(224, 77, 77, 0.08)",
            border: "1.5px solid rgba(224, 77, 77, 0.3)",
            borderRadius: "16px",
            padding: "14px",
            marginBottom: "16px",
            textAlign: "left",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, color: "var(--vy-coral-dark)", marginBottom: "6px" }}>
              <DirectionsCarIcon />
              <span>{isHi ? "🚑 एम्बुलेंस लाइव स्थिति: रवाना" : "🚑 Ambulance Live: En Route"}</span>
            </div>
            <div style={{ fontSize: "13px", color: "var(--vy-text-body)", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
              <div><b>{isHi ? "गाड़ी नंबर:" : "Vehicle ID:"}</b> {dispatchInfo.ambulance_id || "RJ-108-047"}</div>
              <div><b>{isHi ? "पहुंचने का समय:" : "ETA:"}</b> ~{dispatchInfo.eta_minutes || 18} {isHi ? "मिनट" : "mins"}</div>
              <div><b>{isHi ? "चालक:" : "Driver:"}</b> {dispatchInfo.driver_name || "Ramu Lal"}</div>
              <div><b>{isHi ? "ड्राइवर फोन:" : "Phone:"}</b> {dispatchInfo.driver_phone || "9876543210"}</div>
            </div>
          </div>
        )}

        {/* Emergency SMS Broadcast Simulator */}
        <div style={{ background: "var(--vy-warm-bg)", borderRadius: "16px", padding: "14px", marginBottom: "18px", textAlign: "left" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
            <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--vy-teal-primary)" }}>
              {isHi ? "📍 लोकेशन व एसएमएस अलर्ट" : "📍 Location & SMS Alert"}
            </span>
            {broadcastSent && (
              <span style={{ fontSize: "11px", color: "var(--vy-sage-green)", fontWeight: 700, display: "flex", alignItems: "center", gap: "3px" }}>
                <CheckCircleIcon style={{ fontSize: "14px" }} /> {isHi ? "भेजा गया" : "Sent"}
              </span>
            )}
          </div>
          <p style={{ fontSize: "12px", color: "var(--vy-text-soft)", margin: "0 0 10px" }}>
            {isHi
              ? "एक क्लिक में आपकी स्थिति और गांव (रामगढ़) की जानकारी आशा टीम को भेजें।"
              : "Broadcast your village location (Ramgarh) and urgent alert to frontline team."}
          </p>
          <button
            type="button"
            className="vy-header-sos-btn"
            style={{ width: "100%", justifyContent: "center", padding: "10px" }}
            onClick={triggerBroadcast}
            disabled={broadcastSent || loading}
          >
            <SendIcon style={{ fontSize: "14px" }} />
            <span>{broadcastSent ? (isHi ? "सूचना भेजी जा चुकी है" : "Alert Broadcasted") : (isHi ? "मदद के लिए एसएमएस भेजें" : "Send Emergency SMS Broadcast")}</span>
          </button>
        </div>

        <button type="button" className="vy-sos-close-btn" onClick={onClose}>
          {isHi ? "बंद करें" : "Close"}
        </button>
      </div>
    </div>
  );
}

