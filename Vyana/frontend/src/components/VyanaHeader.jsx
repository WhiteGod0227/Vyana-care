import { Link } from "react-router-dom";
import PhoneInTalkIcon from "@mui/icons-material/PhoneInTalk";
import LanguageIcon from "@mui/icons-material/Language";
import DashboardIcon from "@mui/icons-material/Dashboard";
import WifiIcon from "@mui/icons-material/Wifi";
import WifiOffIcon from "@mui/icons-material/WifiOff";
import FavoriteIcon from "@mui/icons-material/Favorite";

export default function VyanaHeader({
  lang,
  setLang,
  isOnline,
  pendingCount = 0,
  onOpenSos,
}) {
  const isHi = lang === "hi";

  return (
    <header className="vy-glass-nav">
      <div className="vy-container vy-nav-inner">
        {/* Brand logo & tagline */}
        <Link to="/" className="vy-brand">
          <div className="vy-brand-icon">
            <FavoriteIcon fontSize="inherit" />
          </div>
          <div className="vy-brand-text">
            <h1>{isHi ? "व्यान केयर" : "Vyana Care"}</h1>
            <span>{isHi ? "मातृ स्वास्थ्य साथी" : "Maternal Health Companion"}</span>
          </div>
        </Link>

        {/* Action Controls */}
        <div className="vy-nav-actions">
          {/* Online / Offline status badge */}
          <div className="vy-status-pill" title={isOnline ? "Server connected" : "Offline mode enabled"}>
            <span className={`vy-status-dot ${isOnline ? "online" : "offline"}`} />
            <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
              {isOnline ? (
                <>
                  <WifiIcon style={{ fontSize: "14px", color: "var(--vy-sage-green)" }} />
                  {isHi ? "ऑनलाइन" : "Online"}
                </>
              ) : (
                <>
                  <WifiOffIcon style={{ fontSize: "14px", color: "var(--vy-coral-primary)" }} />
                  {isHi ? `ऑफलाइन (${pendingCount})` : `Offline (${pendingCount})`}
                </>
              )}
            </span>
          </div>

          {/* Language Switcher */}
          <div className="vy-lang-pill">
            <button
              type="button"
              className={`vy-lang-btn ${isHi ? "active" : ""}`}
              onClick={() => setLang("hi")}
            >
              हिंदी
            </button>
            <button
              type="button"
              className={`vy-lang-btn ${!isHi ? "active" : ""}`}
              onClick={() => setLang("en")}
            >
              Eng
            </button>
          </div>

          {/* Emergency SOS Call button */}
          <button
            type="button"
            className="vy-header-sos-btn"
            onClick={onOpenSos}
            title={isHi ? "आपातकालीन सहायता (108)" : "Emergency SOS (108)"}
          >
            <PhoneInTalkIcon style={{ fontSize: "16px" }} />
            <span>{isHi ? "मदद (108)" : "SOS (108)"}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
