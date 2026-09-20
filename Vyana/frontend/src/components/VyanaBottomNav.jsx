import HomeIcon from "@mui/icons-material/HomeRounded";
import MicIcon from "@mui/icons-material/MicRounded";
import MenuBookIcon from "@mui/icons-material/MenuBookRounded";
import PhoneInTalkIcon from "@mui/icons-material/PhoneInTalkRounded";
import DashboardIcon from "@mui/icons-material/DashboardRounded";

export default function VyanaBottomNav({
  lang,
  activeSection,
  setActiveSection,
  onOpenSos,
  onOpenStaffMenu,
}) {
  const isHi = lang === "hi";

  return (
    <nav className="vy-bottom-nav" aria-label="Mobile Navigation">
      <div className="vy-bottom-nav-inner">
        {/* Home */}
        <button
          type="button"
          className={`vy-nav-item ${activeSection === "home" ? "active" : ""}`}
          onClick={() => setActiveSection("home")}
        >
          <HomeIcon className="nav-icon" />
          <span>{isHi ? "मुख्य" : "Home"}</span>
        </button>

        {/* Talk / Voice */}
        <button
          type="button"
          className={`vy-nav-item ${activeSection === "voice" ? "active" : ""}`}
          onClick={() => {
            setActiveSection("voice");
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
        >
          <MicIcon className="nav-icon" />
          <span>{isHi ? "बोलें" : "Talk"}</span>
        </button>

        {/* SOS Emergency */}
        <button
          type="button"
          className="vy-nav-item sos-item"
          onClick={onOpenSos}
        >
          <PhoneInTalkIcon className="nav-icon" />
          <span>{isHi ? "मदद (108)" : "SOS"}</span>
        </button>

        {/* Knowledge Library */}
        <button
          type="button"
          className={`vy-nav-item ${activeSection === "library" ? "active" : ""}`}
          onClick={() => {
            setActiveSection("library");
            const el = document.getElementById("knowledge-section");
            if (el) el.scrollIntoView({ behavior: "smooth" });
          }}
        >
          <MenuBookIcon className="nav-icon" />
          <span>{isHi ? "जानकारी" : "Guide"}</span>
        </button>

        {/* Staff Portals */}
        <button
          type="button"
          className="vy-nav-item"
          onClick={onOpenStaffMenu}
        >
          <DashboardIcon className="nav-icon" />
          <span>{isHi ? "पोर्टल" : "Portals"}</span>
        </button>
      </div>
    </nav>
  );
}
