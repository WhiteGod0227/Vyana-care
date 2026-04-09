import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button, Chip, MenuItem, Select, TextField } from "@mui/material";
import MicIcon from "@mui/icons-material/Mic";
import StopCircleIcon from "@mui/icons-material/StopCircle";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import RefreshIcon from "@mui/icons-material/Refresh";
import LockIcon from "@mui/icons-material/Lock";
import ThumbUpAltOutlinedIcon from "@mui/icons-material/ThumbUpAltOutlined";
import BookmarkBorderIcon from "@mui/icons-material/BookmarkBorder";
import CampaignIcon from "@mui/icons-material/Campaign";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import HourglassTopIcon from "@mui/icons-material/HourglassTop";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import SearchIcon from "@mui/icons-material/Search";
import ShieldIcon from "@mui/icons-material/Shield";
import FavoriteIcon from "@mui/icons-material/Favorite";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import { motion as Motion } from "framer-motion";
import toast from "react-hot-toast";
import api from "../api/axios";
import EmptyState from "../components/EmptyState";
import LoadingSkeleton from "../components/LoadingSkeleton";
import ErrorBanner from "../components/ErrorBanner";
import AwaazAudioPlayer from "../components/AwaazAudioPlayer";

const DISTRICTS = ["Barmer", "Jaisalmer", "Jodhpur"];
const LANGUAGES = ["Hindi", "Bengali", "Tamil", "Telugu", "Marathi", "Gujarati", "Other"];
const TOPICS = [
  "Symptoms",
  "Hospital Visit",
  "Emotional Support",
  "Warning Signs",
  "Delivery Experience",
  "Nutrition",
  "Family Support",
  "Postnatal Care",
];
const FEED_LANGUAGES = ["All", "Hindi", "Bengali", "Tamil", "Other"];
const FEED_TOPICS = ["All", "Symptoms", "Hospital Visit", "Emotional Support", "Warning Signs", "Delivery Experience", "Nutrition"];
const FEED_TRIMESTERS = ["All", "First Trimester", "Second Trimester", "Third Trimester"];
const SORT_OPTIONS = [
  { value: "newest", label: "Newest" },
  { value: "most_helpful", label: "Most Helpful" },
  { value: "most_played", label: "Most Played" },
];

const MODERATION_FLOW = [
  { title: "Audio Upload", icon: CloudUploadIcon, tone: "done" },
  { title: "AI Text Conversion", icon: TextSnippetIcon, tone: "done" },
  { title: "Pregnancy Check", icon: SearchIcon, tone: "done" },
  { title: "Safety Filter", icon: ShieldIcon, tone: "done" },
  { title: "Distress Detection", icon: FavoriteIcon, tone: "done" },
  { title: "Human Approval", icon: FactCheckIcon, tone: "pending" },
  { title: "Goes Live", icon: AutoAwesomeIcon, tone: "pending" },
];

function formatTime(value) {
  if (!Number.isFinite(value) || value < 0) return "00:00";
  const minutes = Math.floor(value / 60);
  const seconds = Math.floor(value % 60);
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

async function getBlobDuration(blob) {
  const url = URL.createObjectURL(blob);
  try {
    const audio = new Audio(url);
    return await new Promise((resolve, reject) => {
      audio.addEventListener("loadedmetadata", () => resolve(audio.duration || 0), { once: true });
      audio.addEventListener("error", () => reject(new Error("duration failed")), { once: true });
      audio.src = url;
    });
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}

async function encodeWav(audioBuffer) {
  const numChannels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const samples = audioBuffer.length;
  const bytesPerSample = 2;
  const blockAlign = numChannels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = samples * blockAlign;
  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);
  const writeString = (offset, string) => {
    for (let index = 0; index < string.length; index += 1) {
      view.setUint8(offset + index, string.charCodeAt(index));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, dataSize, true);

  const channelData = [];
  for (let channel = 0; channel < numChannels; channel += 1) {
    channelData.push(audioBuffer.getChannelData(channel));
  }

  let offset = 44;
  for (let sample = 0; sample < samples; sample += 1) {
    for (let channel = 0; channel < numChannels; channel += 1) {
      const value = Math.max(-1, Math.min(1, channelData[channel][sample] || 0));
      view.setInt16(offset, value < 0 ? value * 0x8000 : value * 0x7fff, true);
      offset += 2;
    }
  }

  return new Blob([buffer], { type: "audio/wav" });
}

async function trimAudioBlob(blob, startSeconds, endSeconds) {
  const context = new (window.AudioContext || window.webkitAudioContext)();
  try {
    const arrayBuffer = await blob.arrayBuffer();
    const decoded = await context.decodeAudioData(arrayBuffer.slice(0));
    const startFrame = Math.max(0, Math.floor(startSeconds * decoded.sampleRate));
    const endFrame = Math.min(decoded.length, Math.floor(endSeconds * decoded.sampleRate));
    const frameCount = Math.max(1, endFrame - startFrame);
    const output = context.createBuffer(decoded.numberOfChannels, frameCount, decoded.sampleRate);

    for (let channel = 0; channel < decoded.numberOfChannels; channel += 1) {
      const source = decoded.getChannelData(channel).slice(startFrame, endFrame);
      output.copyToChannel(source, channel, 0);
    }

    return encodeWav(output);
  } finally {
    await context.close();
  }
}

function prettyTopic(topic) {
  return topic
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function getTrimesterLabel(week) {
  const value = Number(week || 0);
  if (!value) return "Unknown";
  if (value <= 13) return "First Trimester";
  if (value <= 27) return "Second Trimester";
  return "Third Trimester";
}

function WaveformBars({ bars, recording }) {
  return (
    <div className="vy-waveform" aria-hidden="true">
      {bars.map((bar, index) => (
        <span key={`${index}-${bar}`} style={{ height: `${bar}%` }} className={recording ? "active" : ""} />
      ))}
    </div>
  );
}

function AwaazPage() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [waveBars, setWaveBars] = useState(Array.from({ length: 24 }, () => 18));
  const [recordName, setRecordName] = useState("awaaz.webm");
  const [reviewBlob, setReviewBlob] = useState(null);
  const [reviewUrl, setReviewUrl] = useState("");
  const [reviewDuration, setReviewDuration] = useState(0);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);
  const [speakerAge, setSpeakerAge] = useState("");
  const [speakerDistrict, setSpeakerDistrict] = useState("Barmer");
  const [pregnancyWeekAtTime, setPregnancyWeekAtTime] = useState("");
  const [language, setLanguage] = useState("Hindi");
  const [selectedTopics, setSelectedTopics] = useState(["Symptoms"]);
  const [submissionId, setSubmissionId] = useState(null);
  const [submissionStatus, setSubmissionStatus] = useState(null);
  const [submissionMessage, setSubmissionMessage] = useState("");
  const [submissionReason, setSubmissionReason] = useState("");
  const [distressDetected, setDistressDetected] = useState(false);
  const [uploadLabel, setUploadLabel] = useState("No file selected yet");

  const [feedLoading, setFeedLoading] = useState(true);
  const [feed, setFeed] = useState([]);
  const [feedPage, setFeedPage] = useState(1);
  const [feedHasMore, setFeedHasMore] = useState(false);
  const [feedSearch, setFeedSearch] = useState("");
  const [feedLanguage, setFeedLanguage] = useState("All");
  const [feedTopic, setFeedTopic] = useState("All");
  const [feedTrimester, setFeedTrimester] = useState("All");
  const [feedSort, setFeedSort] = useState("newest");
  const [expandedId, setExpandedId] = useState(null);

  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const analyserRef = useRef(null);
  const rafRef = useRef(null);
  const statusTimerRef = useRef(null);
  const fileInputRef = useRef(null);

  const stats = useMemo(() => {
    const totalStories = feed.length;
    const totalListens = feed.reduce((sum, item) => sum + (item.play_count || 0), 0);
    const languages = new Set(feed.map((item) => item.language_detected || "Other"));
    return [
      { label: "Total Stories", value: totalStories },
      { label: "Total Listens", value: totalListens },
      { label: "Languages", value: languages.size || 1 },
    ];
  }, [feed]);

  const canSubmit = Boolean(reviewBlob && reviewDuration >= 10 && !loading);
  const currentStage = submissionStatus || (submissionId ? "PENDING_AI" : "IDLE");

  const resetDraft = () => {
    if (reviewUrl) URL.revokeObjectURL(reviewUrl);
    setRecordName("awaaz.webm");
    setReviewBlob(null);
    setReviewUrl("");
    setReviewDuration(0);
    setTrimStart(0);
    setTrimEnd(0);
    setRecordSeconds(0);
    setUploadLabel("No file selected yet");
  };

  const setBlobForReview = async (blob, name) => {
    if (reviewUrl) URL.revokeObjectURL(reviewUrl);
    const duration = await getBlobDuration(blob);
    const normalizedDuration = Math.max(0, duration || 0);
    const nextUrl = URL.createObjectURL(blob);
    setRecordName(name);
    setReviewBlob(blob);
    setReviewUrl(nextUrl);
    setReviewDuration(normalizedDuration);
    setTrimStart(0);
    setTrimEnd(normalizedDuration);
    setSubmissionStatus(null);
    setSubmissionMessage("");
    setSubmissionReason("");
    setDistressDetected(false);
  };

  const fetchFeed = useCallback(async (pageToLoad = 1, append = false) => {
    setFeedLoading(true);
    try {
      const res = await api.get("/awaaz/feed", {
        params: {
          language: feedLanguage,
          topic: feedTopic,
          sort: feedSort,
          page: pageToLoad,
        },
      });
      const payload = res.data?.data || { items: [], has_more: false, page: 1 };
      setFeed((prev) => (append ? [...prev, ...(payload.items || [])] : payload.items || []));
      setFeedHasMore(Boolean(payload.has_more));
      setFeedPage(payload.page || pageToLoad);
    } catch {
      setFeed([]);
      setFeedHasMore(false);
    } finally {
      setFeedLoading(false);
    }
  }, [feedLanguage, feedSort, feedTopic]);

  useEffect(() => {
    fetchFeed(1, false);
  }, [fetchFeed]);

  useEffect(() => {
    if (!submissionId) return undefined;

    const pollStatus = async () => {
      try {
        const res = await api.get(`/awaaz/status/${submissionId}`);
        const payload = res.data?.data || {};
        setSubmissionStatus(payload.status || "PENDING_AI");
        setSubmissionMessage(payload.message || "");
        setSubmissionReason(payload.reason || "");
        setDistressDetected(Boolean(payload.distress_detected));
        if (payload.status === "PUBLISHED") {
          toast.success("Aapki Vaani publish ho gayi!");
        }
        if (payload.status === "AI_REJECTED" && payload.distress_detected) {
          setSubmissionMessage("Hum dekh rahe hain aap thodi pareshan lag rahi hain.");
        }
      } catch {
        // keep polling quietly
      }
    };

    pollStatus();
    statusTimerRef.current = setInterval(pollStatus, 5000);
    return () => {
      if (statusTimerRef.current) clearInterval(statusTimerRef.current);
    };
  }, [submissionId]);

  useEffect(() => {
    return () => {
      if (reviewUrl) URL.revokeObjectURL(reviewUrl);
      if (statusTimerRef.current) clearInterval(statusTimerRef.current);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, [reviewUrl]);

  const updateWave = () => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    const nextBars = Array.from({ length: 24 }, (_, index) => {
      const value = data[index * 2] || data[index] || 0;
      return Math.max(12, Math.min(100, Math.round((value / 255) * 100)));
    });
    setWaveBars(nextBars);
    rafRef.current = requestAnimationFrame(updateWave);
  };

  const startRecording = async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Microphone unavailable");
      }
      resetDraft();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      analyserRef.current = analyser;
      updateWave();

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = async () => {
        try {
          const blob = new Blob(chunksRef.current, { type: "audio/webm" });
          await setBlobForReview(blob, "awaaz.webm");
          toast.success("Audio ready for review.");
        } catch {
          setError("Upload mein kuch gadbad hui — dobara try karein");
        } finally {
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
          }
          if (rafRef.current) cancelAnimationFrame(rafRef.current);
          if (audioContext.state !== "closed") {
            await audioContext.close();
          }
        }
      };

      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
      setRecordSeconds(0);
      const timer = setInterval(() => setRecordSeconds((value) => value + 1), 1000);
      recorder.addEventListener("stop", () => clearInterval(timer), { once: true });
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

  const onFileSelect = async (file) => {
    if (!file) return;
    const allowed = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/webm", "audio/ogg", "audio/mp4", "audio/m4a", "audio/x-m4a"];
    if (!allowed.includes(file.type) && !file.name.match(/\.(mp3|wav|webm|ogg|m4a)$/i)) {
      setError("Sirf audio files accept hoti hain");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File bahut badi hai — 10MB se kam honi chahiye");
      return;
    }
    setLoading(true);
    try {
      await setBlobForReview(file, file.name);
      setUploadLabel(`${file.name}`);
      toast.success("File review ke liye taiyar hai.");
    } catch {
      setError("Upload mein kuch gadbad hui — dobara try karein");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = async (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file) await onFileSelect(file);
  };

  const applyTrim = async () => {
    if (!reviewBlob) return;
    if (trimEnd <= trimStart || trimEnd > reviewDuration) {
      setError("Audio bahut chhota hai — kam se kam 10 second bolein");
      return;
    }
    setLoading(true);
    try {
      const trimmed = await trimAudioBlob(reviewBlob, trimStart, trimEnd);
      await setBlobForReview(trimmed, recordName.replace(/\.[^.]+$/, ".wav"));
      toast.success("Trim applied.");
    } catch {
      setError("Upload mein kuch gadbad hui — dobara try karein");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!reviewBlob) return;
    const duration = Math.max(10, Math.round(reviewDuration || 0));
    if (duration < 10) {
      setError("Audio bahut chhota hai — kam se kam 10 second bolein");
      return;
    }
    if (duration > 300) {
      setError("Audio bahut bada hai — 5 minute se kam rakein");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("audio_file", reviewBlob, recordName.endsWith(".wav") ? recordName : recordName.replace(/\.[^.]+$/, ".wav"));
      formData.append("audio_duration_seconds", String(duration));
      formData.append("language", language);
      formData.append("topics", JSON.stringify(selectedTopics));
      if (speakerAge) formData.append("speaker_age", String(Number(speakerAge)));
      if (speakerDistrict) formData.append("speaker_district", speakerDistrict);
      if (pregnancyWeekAtTime) formData.append("pregnancy_week_at_time", String(Number(pregnancyWeekAtTime)));

      const res = await api.post("/awaaz/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const payload = res.data?.data || {};
      setSubmissionId(payload.submission_id);
      setSubmissionStatus("PENDING_AI");
      setSubmissionMessage(payload.message || "Aapki Vaani review ho rahi hai");
      setSubmissionReason("");
      setDistressDetected(false);
      toast.success("Vaani upload ho gayi!");
    } catch (err) {
      const message = err?.response?.data?.error || "Upload mein kuch gadbad hui — dobara try karein";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const toggleTopic = (topic) => {
    setSelectedTopics((prev) => (prev.includes(topic) ? prev.filter((item) => item !== topic) : [...prev, topic]));
  };

  const handleReaction = async (audioId, reactionType) => {
    try {
      const res = await api.post(`/awaaz/react/${audioId}`, { reaction_type: reactionType });
      const payload = res.data?.data || {};
      setFeed((prev) => prev.map((item) => (item.id === audioId ? { ...item, helpful_count: payload.helpful_count ?? item.helpful_count, play_count: payload.play_count ?? item.play_count } : item)));
      toast.success("Shukriya — aapne ek maa ki madad ki!");
    } catch {
      setError("Upload mein kuch gadbad hui — dobara try karein");
    }
  };

  const handlePlay = async (audioId) => {
    try {
      await api.post(`/awaaz/play/${audioId}`);
      setFeed((prev) => prev.map((item) => (item.id === audioId ? { ...item, play_count: (item.play_count || 0) + 1 } : item)));
    } catch {
      // silent
    }
  };

  const filteredFeed = useMemo(() => {
    const query = feedSearch.trim().toLowerCase();
    return feed.filter((item) => {
      const text = [item.ai_analysis_summary, item.transcription, item.language_detected, ...(item.helpful_topics || [])].filter(Boolean).join(" ").toLowerCase();
      const trimester = getTrimesterLabel(item.speaker_pregnancy_week_at_time || null);
      const trimesterMatches = feedTrimester === "All" || trimester === feedTrimester;
      return (!query || text.includes(query)) && trimesterMatches;
    });
  }, [feed, feedSearch, feedTrimester]);

  const statusCards = useMemo(() => {
    const status = currentStage;
    return [
      { key: "upload", label: "Vaani upload ho rahi hai...", done: Boolean(submissionId), active: status === "PENDING_AI" || !status },
      { key: "whisper", label: "Whisper AI transcribe kar rahi hai...", done: ["PENDING_NURSE", "AI_REJECTED", "NURSE_REJECTED", "PUBLISHED"].includes(status), active: status === "PENDING_AI" },
      { key: "gemini", label: "Gemini AI review kar rahi hai...", done: ["PENDING_NURSE", "AI_REJECTED", "NURSE_REJECTED", "PUBLISHED"].includes(status), active: status === "PENDING_AI" },
      { key: "nurse", label: "Nurse ka approval baki hai", done: status === "PUBLISHED", active: status === "PENDING_NURSE" },
    ];
  }, [currentStage, submissionId]);

  return (
    <div className="vy-page vy-awaaz-page">
      <ErrorBanner message={error} onClose={() => setError("")} />

      <Motion.section className="vy-awaaz-hero" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
        <div className="vy-awaaz-hero-top">
          <span className="vy-pill">Vaani Community Voice Sharing</span>
          <CampaignIcon />
        </div>
        <h1>Vaani — Ek maa ki awaaz, doosri maa ki himmat</h1>
        <p>Recovered maao ki kahaniyan sunein — woh jo guzri, woh jo seekhi, aur jo aage kisi aur maa ke kaam aaye.</p>
        <div className="vy-awaaz-stats">
          {stats.map((item) => (
            <div key={item.label}>
              <b>{item.value}</b>
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </Motion.section>

      <Motion.section className="vy-moderation-flow" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
        <div className="vy-section-head">
          <div>
            <h3>AI Moderation Flow</h3>
            <p>Har story pehle machine se safe hoti hai, phir nurse approval ke baad live jaati hai.</p>
          </div>
        </div>
        <div className="vy-flow-track">
          {MODERATION_FLOW.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={step.title} className={`vy-flow-step ${step.tone}`} style={{ animationDelay: `${index * 110}ms` }}>
                <span className="vy-flow-icon">
                  <Icon fontSize="small" />
                </span>
                <strong>{step.title}</strong>
              </div>
            );
          })}
        </div>
      </Motion.section>

      <section className="vy-card vy-awaaz-share" id="vaani-share">
        <div className="vy-section-head">
          <div>
            <h3>Apni kahani share karein</h3>
            <p>Aapki Vaani doosri maa ki madad kar sakti hai.</p>
          </div>
          <div className="vy-stepper">
            <span className={reviewBlob ? "done" : "active"}>1 Record</span>
            <span className={reviewBlob ? "done" : ""}>2 Review</span>
            <span className={submissionId ? "active" : ""}>3 Submit</span>
          </div>
        </div>

        <div className="vy-grid-two vy-awaaz-options">
          <div className="vy-option-card">
            <div className="vy-option-head">
              <h4>Record Now</h4>
              <span>Live mic</span>
            </div>
            <button
              className={`vy-mic-btn vy-mic-btn-small ${recording ? "recording" : ""}`}
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onMouseLeave={stopRecording}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              disabled={loading}
            >
              {recording ? <StopCircleIcon /> : <MicIcon />}
            </button>
            <div className="vy-mini-meta">Kam se kam 10 second | Zyada se zyada 5 minute</div>
            <div className="vy-timer-row">
              <span>Recording: {formatTime(recordSeconds)}</span>
              <Button size="small" variant="outlined" onClick={stopRecording} disabled={!recording}>
                Stop
              </Button>
            </div>
            <WaveformBars bars={waveBars} recording={recording} />
          </div>

          <div className="vy-option-card vy-upload-card">
            <div className="vy-option-head">
              <h4>Upload Story</h4>
              <span>mp3 / wav / webm / ogg / m4a</span>
            </div>
            <div
              className="vy-drop-zone vy-upload-zone"
              onDragOver={(event) => event.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
            >
              <UploadFileIcon fontSize="large" />
              <p>Drag and drop audio here</p>
              <small>Max 10MB</small>
              <strong>{uploadLabel}</strong>
            </div>
            <input
              ref={fileInputRef}
              hidden
              type="file"
              accept="audio/mp3,audio/wav,audio/webm,audio/ogg,audio/m4a,.mp3,.wav,.webm,.ogg,.m4a"
              onChange={(event) => onFileSelect(event.target.files?.[0])}
            />
            <Button variant="outlined" onClick={() => fileInputRef.current?.click()} fullWidth>
              File chunein
            </Button>
          </div>
        </div>

        {reviewBlob ? (
          <div className="vy-review-section" id="vaani-review">
            <div className="vy-section-head">
              <div>
                <h3>Review Your Recording</h3>
                <p>Kya aap apni Vaani sunna chahti hain pehle? Play karein aur sun lein.</p>
              </div>
            </div>
            <AwaazAudioPlayer key={reviewUrl} src={reviewUrl} className="vy-audio-hero-player" onPlay={() => setExpandedId(null)} />
            <div className="vy-trim-row">
              <TextField type="number" label="Trim Start (sec)" value={trimStart} onChange={(event) => setTrimStart(Number(event.target.value))} />
              <TextField type="number" label="Trim End (sec)" value={trimEnd} onChange={(event) => setTrimEnd(Number(event.target.value))} />
              <Button variant="outlined" onClick={applyTrim} disabled={!reviewBlob}>
                Dobara Trim Karein
              </Button>
            </div>
            <div className="vy-action-row">
              <Button variant="outlined" onClick={resetDraft} startIcon={<RefreshIcon />}>
                Dobara Record Karein
              </Button>
              <Button variant="contained" onClick={() => document.getElementById("vaani-metadata")?.scrollIntoView({ behavior: "smooth" })} disabled={!reviewBlob}>
                Haan, Submit Karein
              </Button>
            </div>
          </div>
        ) : null}

        <div className="vy-metadata-section" id="vaani-metadata">
          <div className="vy-section-head">
            <div>
              <h3>Thodi aur jaankari</h3>
              <p>Aapki identity bilkul safe rahegi — naam ya chehra kabhi nahi dikhega.</p>
            </div>
            <div className="vy-privacy-box">
              <LockIcon fontSize="small" />
              <span>Aapka naam, chehra, ya phone number kabhi bhi share nahi hoga.</span>
            </div>
          </div>

          <div className="vy-grid-two">
            <TextField type="number" label="Aapki aayu (optional)" value={speakerAge} onChange={(event) => setSpeakerAge(event.target.value)} />
            <TextField select label="District (optional)" value={speakerDistrict} onChange={(event) => setSpeakerDistrict(event.target.value)}>
              {DISTRICTS.map((district) => (
                <MenuItem key={district} value={district}>
                  {district}
                </MenuItem>
              ))}
            </TextField>
            <TextField type="number" label="Pregnancy week jab deliver hui" value={pregnancyWeekAtTime} onChange={(event) => setPregnancyWeekAtTime(event.target.value)} />
            <TextField select label="Bhasha" value={language} onChange={(event) => setLanguage(event.target.value)}>
              {LANGUAGES.map((item) => (
                <MenuItem key={item} value={item}>
                  {item}
                </MenuItem>
              ))}
            </TextField>
          </div>

          <div className="vy-topic-grid">
            {TOPICS.map((topic) => (
              <Chip key={topic} label={topic} color={selectedTopics.includes(topic) ? "primary" : "default"} onClick={() => toggleTopic(topic)} />
            ))}
          </div>

          <div className="vy-privacy-reminder">
            <LockIcon />
            <p>Aapka naam, chehra, ya phone number kabhi bhi share nahi hoga. Sirf aapki aayu aur district dikhega — woh bhi aapki marzi se.</p>
          </div>

              <Button variant="contained" fullWidth size="large" onClick={handleSubmit} disabled={!canSubmit}>
            Submit Karein
          </Button>
        </div>
      </section>

      {submissionId ? (
        <section className="vy-card vy-processing-card">
          <div className="vy-section-head">
            <div>
              <h3>Status</h3>
              <p>{submissionMessage || "Aapki Vaani review ho rahi hai"}</p>
            </div>
            <span className="vy-submission-id">#{submissionId}</span>
          </div>

          <div className="vy-stage-list">
            {statusCards.map((stage) => (
              <div key={stage.key} className={`vy-stage ${stage.done ? "done" : ""} ${stage.active ? "active" : ""}`}>
                {stage.done ? <CheckCircleIcon fontSize="small" /> : stage.active ? <HourglassTopIcon fontSize="small" /> : <ErrorOutlineIcon fontSize="small" />}
                <span>{stage.label}</span>
              </div>
            ))}
          </div>

          {currentStage === "AI_REJECTED" && distressDetected ? (
            <div className="vy-support-card">
              <h4>Hum dekh rahe hain aap thodi pareshan lag rahi hain.</h4>
              <p>Kya ASHA didi se baat karni hai?</p>
              <Button variant="contained" onClick={() => toast.success("ASHA support request sent.")}>Help Button</Button>
            </div>
          ) : null}

          {currentStage === "AI_REJECTED" && !distressDetected ? (
            <div className="vy-reject-card">
              <h4>Aapki Vaani is baar publish nahi ho saki</h4>
              <p>{submissionReason}</p>
              <Button variant="outlined" onClick={resetDraft}>Dobara try karein</Button>
            </div>
          ) : null}

          {currentStage === "PENDING_NURSE" ? (
            <div className="vy-hold-card">
              <h4>AI ne approve kar liya! Nurse ji review kar rahi hain.</h4>
              <p>Estimated time: 24 ghante mein decision</p>
            </div>
          ) : null}

          {currentStage === "PUBLISHED" ? (
            <div className="vy-success-card">
              <h4>Congratulations! Aapki Vaani community mein aa gayi.</h4>
              <Button variant="contained" onClick={() => document.getElementById("vaani-feed")?.scrollIntoView({ behavior: "smooth" })}>
                Apni story sunein
              </Button>
            </div>
          ) : null}

          {currentStage === "NURSE_REJECTED" ? (
            <div className="vy-nurse-reject-card">
              <h4>Nurse review mein Vaani approve nahi hui.</h4>
              <p>{submissionReason}</p>
              <Button variant="outlined" onClick={() => toast.info("Aap ASHA didi se baat kar sakti hain.")}>ASHA didi se baat karein</Button>
            </div>
          ) : null}
        </section>
      ) : null}

      <section className="vy-card vy-feed-card" id="vaani-feed">
        <div className="vy-section-head">
          <div>
            <h3>Doosri Maao Ki Vaani</h3>
            <p>Published stories from recovered mothers.</p>
          </div>
          <Button variant="outlined" onClick={() => toast.success("Vaani feed refreshed.")}>Refresh Feed</Button>
        </div>

        <div className="vy-feed-filters">
          <TextField size="small" label="Vaani, topic ya bhasha dhundho..." value={feedSearch} onChange={(event) => setFeedSearch(event.target.value)} />
          <div className="vy-chip-row">
            {FEED_LANGUAGES.map((item) => (
              <button key={item} className={`vy-filter-chip ${feedLanguage === item ? "active" : ""}`} onClick={() => setFeedLanguage(item)}>{item}</button>
            ))}
          </div>
          <div className="vy-chip-row">
            {FEED_TRIMESTERS.map((item) => (
              <button key={item} className={`vy-filter-chip ${feedTrimester === item ? "active" : ""}`} onClick={() => setFeedTrimester(item)}>{item}</button>
            ))}
          </div>
          <div className="vy-chip-row scroll">
            {FEED_TOPICS.map((item) => (
              <button key={item} className={`vy-filter-chip ${feedTopic === item ? "active" : ""}`} onClick={() => setFeedTopic(item)}>{item}</button>
            ))}
          </div>
          <div className="vy-sort-row">
            {SORT_OPTIONS.map((item) => (
              <button key={item.value} className={`vy-filter-chip ${feedSort === item.value ? "active" : ""}`} onClick={() => setFeedSort(item.value)}>{item.label}</button>
            ))}
          </div>
        </div>

        {feedLoading ? <LoadingSkeleton height={180} /> : null}
        {!feedLoading && filteredFeed.length === 0 ? (
          <EmptyState text="Abhi koi story nahi hai. Pehli Vaani aap share karein!" actionText="Share Story" onAction={() => document.getElementById("vaani-share")?.scrollIntoView({ behavior: "smooth" })} />
        ) : null}

        <div className="vy-feed-list">
          {filteredFeed.map((item) => {
            const expanded = expandedId === item.id;
            return (
              <Motion.div
                key={item.id}
                layout
                className="vy-feed-card-item"
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.24 }}
                transition={{ duration: 0.45, ease: "easeOut" }}
                style={{ animationDelay: `${(item.id % 6) * 90}ms` }}
                onClick={() => setExpandedId((prev) => (prev === item.id ? null : item.id))}
              >
                <div className="vy-feed-main">
                  <button
                    className="vy-play-circle"
                    onClick={(event) => {
                      event.stopPropagation();
                      handlePlay(item.id);
                    }}
                  >
                    ▶
                  </button>
                  <div className="vy-feed-copy">
                    <strong>
                      {(item.speaker_age ? `${item.speaker_age} saal ki maa` : "Anonymous maa")}
                      {item.speaker_district ? `, ${item.speaker_district} se` : ""}
                    </strong>
                    <div className="vy-tag-row">
                      <span className="vy-mini-chip">{getTrimesterLabel(item.speaker_pregnancy_week_at_time)}</span>
                      {item.language_detected ? <span className="vy-mini-chip">{item.language_detected}</span> : null}
                    </div>
                    <div className="vy-tag-row">
                      {(item.helpful_topics || []).map((topic) => (
                        <span key={topic} className="vy-mini-chip">{prettyTopic(topic)}</span>
                      ))}
                    </div>
                    <p>{item.ai_analysis_summary || item.transcription || "Recovered mother story"}</p>
                    <div className="vy-feed-meta">
                      <span>{formatTime(item.audio_duration_seconds)}</span>
                      <span>{item.play_count} plays</span>
                      <span>{item.helpful_count} helpful</span>
                    </div>
                    <div className="vy-card-waveform" aria-hidden="true">
                      {Array.from({ length: 12 }, (_, index) => {
                        const height = 24 + ((item.id * (index + 3) * 17) % 56);
                        return <span key={`${item.id}-${index}`} style={{ height: `${height}%` }} />;
                      })}
                    </div>
                  </div>
                  <button className="vy-play-save" onClick={(event) => { event.stopPropagation(); handleReaction(item.id, "saved"); }}>
                    <BookmarkBorderIcon fontSize="small" />
                  </button>
                </div>

                {expanded ? (
                  <div className="vy-feed-expanded" onClick={(event) => event.stopPropagation()}>
                    <AwaazAudioPlayer key={item.audio_file_url} src={item.audio_file_url} onPlay={() => handlePlay(item.id)} />
                    <p>{item.ai_analysis_summary || "Summary unavailable."}</p>
                    <div className="vy-tag-row">
                      {(item.helpful_topics || []).map((topic) => <span key={`${item.id}-${topic}`} className="vy-mini-chip">{prettyTopic(topic)}</span>)}
                    </div>
                    <div className="vy-action-row">
                      <Button variant="contained" onClick={() => handleReaction(item.id, "helpful")} startIcon={<ThumbUpAltOutlinedIcon />}>Helpful laga?</Button>
                      <Button variant="outlined" onClick={() => handleReaction(item.id, "saved")} startIcon={<BookmarkBorderIcon />}>Save karein</Button>
                    </div>
                  </div>
                ) : null}
              </Motion.div>
            );
          })}
        </div>

        {feedHasMore ? (
          <Button variant="outlined" onClick={() => fetchFeed(feedPage + 1, true)}>Load more</Button>
        ) : null}
      </section>
    </div>
  );
}

export default AwaazPage;
