import { useEffect, useState } from "react";
import { Button, TextField } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import LockIcon from "@mui/icons-material/Lock";
import { motion as Motion } from "framer-motion";
import toast from "react-hot-toast";
import api from "../api/axios";
import LoadingSkeleton from "../components/LoadingSkeleton";
import ErrorBanner from "../components/ErrorBanner";
import AwaazAudioPlayer from "../components/AwaazAudioPlayer";

const ACCESS_CODE = "NURSE2026";

function prettyTopic(topic) {
  return topic
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function scoreFlag(value) {
  return value ? "good" : value === false ? "bad" : "neutral";
}

function AwaazNursePage() {
  const [accessCode, setAccessCode] = useState("");
  const [authorized, setAuthorized] = useState(() => localStorage.getItem("awaaz_nurse_access") === "granted");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState([]);
  const [rejectReason, setRejectReason] = useState({});
  const [expandedId, setExpandedId] = useState(null);

  const fetchPending = async () => {
    setLoading(true);
    try {
      const res = await api.get("/awaaz/nurse/pending");
      setItems(res.data?.data?.submissions || []);
    } catch {
      setError("Pending submissions load nahi ho payi.");
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authorized) fetchPending();
  }, [authorized]);

  const login = () => {
    if (accessCode !== ACCESS_CODE) {
      setError("Invalid nurse access code.");
      return;
    }
    localStorage.setItem("awaaz_nurse_access", "granted");
    setAuthorized(true);
    setError("");
  };

  const review = async (submissionId, decision) => {
    try {
      const payload = {
        nurse_id: 1,
        decision,
        rejection_reason: decision === "rejected" ? rejectReason[submissionId] || "" : null,
      };
      await api.post(`/awaaz/nurse/review/${submissionId}`, payload);
      toast.success(decision === "approved" ? "Vaani published." : "Vaani rejected.");
      setItems((prev) => prev.filter((item) => item.id !== submissionId));
      setRejectReason((prev) => {
        const next = { ...prev };
        delete next[submissionId];
        return next;
      });
    } catch (err) {
      setError(err?.response?.data?.error || "Review submit nahi ho payi.");
    }
  };

  if (!authorized) {
    return (
      <div className="vy-card vy-nurse-login">
        <ErrorBanner message={error} onClose={() => setError("")} />
        <LockIcon sx={{ fontSize: 48, color: "#06b6d4" }} />
        <h3>Vaani Nurse Access</h3>
        <p>Protected PHC nurse panel ke liye access code daliy.</p>
        <TextField label="Access Code" value={accessCode} onChange={(event) => setAccessCode(event.target.value)} fullWidth />
        <Button variant="contained" onClick={login} fullWidth>
          Unlock Panel
        </Button>
      </div>
    );
  }

  return (
    <div className="vy-page">
      <ErrorBanner message={error} onClose={() => setError("")} />
      <section className="vy-awaaz-hero nurse">
        <span className="vy-pill">PHC Nurse Review</span>
        <h1>Vaani Nurse Panel</h1>
        <p>Pending submissions ko transcript, audio aur AI checks ke saath review karein.</p>
      </section>

      <section className="vy-card">
        <div className="vy-section-head">
          <div>
            <h3>Pending Submissions</h3>
            <p>AI se pass hua content ab human approval ke liye ready hai.</p>
          </div>
          <Button variant="outlined" onClick={fetchPending}>Refresh</Button>
        </div>
        {loading ? <LoadingSkeleton height={180} /> : null}
        {!loading && items.length === 0 ? <p className="vy-muted">Koi pending submission nahi hai.</p> : null}
        <div className="vy-nurse-list">
          {items.map((item) => {
            const expanded = expandedId === item.id;
            return (
              <Motion.div key={item.id} layout className="vy-nurse-card">
                <div className="vy-nurse-top">
                  <div>
                    <strong>{item.speaker_age ? `${item.speaker_age} saal` : "Anonymous maa"}</strong>
                    <p>{item.speaker_district || "Unknown district"} • {item.language_detected || "Hindi"} • {item.audio_duration_seconds}s</p>
                  </div>
                  <div className="vy-score-pill">{item.ai_overall_score ?? 0}/100</div>
                </div>

                <div className="vy-nurse-checks">
                  <span className={scoreFlag(item.ai_check_pregnancy_related)}><CheckCircleIcon fontSize="small" /> Pregnancy related</span>
                  <span className={scoreFlag(item.ai_check_safe_advice)}><CheckCircleIcon fontSize="small" /> Safe advice</span>
                  <span className={scoreFlag(!item.ai_check_distress_detected ? true : false)}><CheckCircleIcon fontSize="small" /> Distress check</span>
                  <span className={scoreFlag(item.ai_check_respectful)}><CheckCircleIcon fontSize="small" /> Respectful</span>
                </div>

                <AwaazAudioPlayer key={item.audio_file_url} src={item.audio_file_url} compact />
                <p>{item.ai_analysis_summary}</p>
                <div className="vy-tag-row">
                  {(item.helpful_topics || []).map((topic) => <span key={`${item.id}-${topic}`} className="vy-mini-chip">{prettyTopic(topic)}</span>)}
                </div>

                <Button variant="text" onClick={() => setExpandedId((prev) => (prev === item.id ? null : item.id))}>
                  {expanded ? "Transcript hide karein" : "Transcript dikhaayein"}
                </Button>
                {expanded ? <div className="vy-transcript-box">{item.transcription || "Transcript unavailable."}</div> : null}

                <div className="vy-action-row">
                  <Button variant="contained" onClick={() => review(item.id, "approved")} startIcon={<CheckCircleIcon />}>Publish Karein</Button>
                  <Button variant="outlined" color="error" onClick={() => review(item.id, "rejected")} startIcon={<CancelIcon />}>Reject Karein</Button>
                </div>
                <TextField
                  label="Rejection reason Hindi mein likhein"
                  value={rejectReason[item.id] || ""}
                  onChange={(event) => setRejectReason((prev) => ({ ...prev, [item.id]: event.target.value }))}
                  multiline
                  minRows={2}
                  fullWidth
                />
              </Motion.div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

export default AwaazNursePage;
