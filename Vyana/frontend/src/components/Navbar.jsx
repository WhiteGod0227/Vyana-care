import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { IconButton } from "@mui/material";
import NotificationsIcon from "@mui/icons-material/Notifications";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import MenuIcon from "@mui/icons-material/Menu";
import CloseIcon from "@mui/icons-material/Close";
import toast from "react-hot-toast";
import api from "../api/axios";
import AlertPanel from "./AlertPanel";
import { useAuth } from "../context/AuthContext";

const navLinks = [
  { path: "/", label: "Patient" },
  { path: "/awaaz", label: "Vaani" },
  { path: "/asha", label: "ASHA" },
  { path: "/district", label: "District" },
  { path: "/integrations", label: "Integrations" },
];

function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [openPanel, setOpenPanel] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [shake, setShake] = useState(false);

  const patientId = localStorage.getItem("patient_id") || "Not registered";

  const openFeature = (featureId) => {
    if (featureId === "feature-vaani") {
      navigate("/awaaz");
      setProfileOpen(false);
      return;
    }

    if (location.pathname !== "/") {
      navigate("/");
    }

    setTimeout(() => {
      const section = document.getElementById(featureId);
      if (section) section.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 120);

    setProfileOpen(false);
  };

  const fetchAlerts = async () => {
    try {
      const res = await api.get("/asha/1/alerts");
      const next = res.data?.data?.alerts || [];
      setAlerts((prev) => {
        if (next.length > prev.length) {
          setShake(true);
          setTimeout(() => setShake(false), 700);
        }
        return next;
      });
    } catch {
      setAlerts([]);
    }
  };

  useEffect(() => {
    const bootstrap = setTimeout(fetchAlerts, 0);
    const timer = setInterval(fetchAlerts, 30000);
    return () => {
      clearTimeout(bootstrap);
      clearInterval(timer);
    };
  }, []);

  const handleAck = async (alertId) => {
    try {
      await api.post(`/alert/${alertId}/acknowledge`, { acknowledged_by: "ASHA Worker" });
      setAlerts((prev) => prev.filter((a) => a.alert_id !== alertId));
      toast.success("Alert acknowledged successfully.");
    } catch {
      toast.error("Could not acknowledge alert.");
    }
  };

  return (
    <header className="vy-navbar">
      <div className="vy-navbar-left">
        <img className="vy-brand-logo" src="/vyana-care-logo-enhanced.png" alt="Vyana Care" />
      </div>

      <nav className={`vy-nav-pills ${mobileOpen ? "open" : ""}`}>
        {navLinks.map((link) => (
          <Link
            key={link.path}
            to={link.path}
            onClick={() => setMobileOpen(false)}
            className={location.pathname === link.path ? "active" : ""}
          >
            {link.label}
          </Link>
        ))}
      </nav>

      <div className="vy-navbar-right">
        {user ? (
          <div className="vy-user-chip">
            <span>{user.display_name}</span>
            <small>{user.role}</small>
          </div>
        ) : null}
        {!user ? (
          <button className="vy-quick-btn" onClick={() => navigate("/login")}>Sign in</button>
        ) : (
          <button className="vy-quick-btn" onClick={() => logout()}>Sign out</button>
        )}
        <IconButton
          onClick={() => {
            setOpenPanel((v) => !v);
            setProfileOpen(false);
          }}
          className={`vy-icon-btn ${shake ? "vy-bell-shake" : ""} ${openPanel ? "active" : ""}`}
        >
          <div className="vy-badge-wrap">
            <NotificationsIcon sx={{ color: "#fff" }} />
            {alerts.length > 0 ? <span className="vy-badge">{alerts.length}</span> : null}
          </div>
        </IconButton>
        <IconButton
          onClick={() => {
            setProfileOpen((v) => !v);
            setOpenPanel(false);
          }}
          className={`vy-icon-btn vy-profile-trigger ${profileOpen ? "active" : ""}`}
        >
          <AccountCircleIcon sx={{ color: "#fff" }} />
        </IconButton>
        <IconButton className="vy-mobile-menu-btn" onClick={() => setMobileOpen((v) => !v)}>
          {mobileOpen ? <CloseIcon sx={{ color: "#fff" }} /> : <MenuIcon sx={{ color: "#fff" }} />}
        </IconButton>
      </div>

      <AlertPanel open={openPanel} alerts={alerts} onAcknowledge={handleAck} />
      {profileOpen ? (
        <div className="vy-profile-panel vy-card">
          <h4>Profile</h4>
          <div className="vy-profile-meta">
            <span>Role: Frontline User</span>
            <span>Patient ID: {patientId}</span>
          </div>
          <div className="vy-profile-actions">
            <button className="vy-quick-btn" onClick={() => openFeature("feature-register")}>Registration</button>
            <button className="vy-quick-btn" onClick={() => openFeature("feature-vaani")}>Vaani Voice</button>
            <button className="vy-quick-btn" onClick={() => openFeature("feature-symptoms")}>Symptoms</button>
            <button className="vy-quick-btn" onClick={() => openFeature("feature-history")}>Report History</button>
          </div>
        </div>
      ) : null}
    </header>
  );
}

export default Navbar;
