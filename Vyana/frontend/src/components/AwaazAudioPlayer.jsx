import { useEffect, useRef, useState } from "react";
import { IconButton, MenuItem, Select } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import VolumeUpIcon from "@mui/icons-material/VolumeUp";

function formatTime(value) {
  if (!Number.isFinite(value) || value < 0) return "00:00";
  const minutes = Math.floor(value / 60);
  const seconds = Math.floor(value % 60);
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function AwaazAudioPlayer({ src, onPlay, onEnded, compact = false, className = "" }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.9);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return undefined;

    const handleLoaded = () => setDuration(audio.duration || 0);
    const handleTime = () => setCurrentTime(audio.currentTime || 0);
    const handleEnd = () => {
      setPlaying(false);
      setCurrentTime(0);
      onEnded?.();
    };

    audio.addEventListener("loadedmetadata", handleLoaded);
    audio.addEventListener("timeupdate", handleTime);
    audio.addEventListener("ended", handleEnd);

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoaded);
      audio.removeEventListener("timeupdate", handleTime);
      audio.removeEventListener("ended", handleEnd);
    };
  }, [src, onEnded]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = volume;
    audio.playbackRate = speed;
  }, [volume, speed]);

  const togglePlay = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (playing) {
      audio.pause();
      setPlaying(false);
      return;
    }

    try {
      await audio.play();
      setPlaying(true);
      onPlay?.();
    } catch {
      setPlaying(false);
    }
  };

  const seek = (nextValue) => {
    const audio = audioRef.current;
    if (!audio) return;
    const value = Number(nextValue);
    audio.currentTime = value;
    setCurrentTime(value);
  };

  return (
    <div className={`vy-audio-player ${compact ? "compact" : ""} ${className}`}>
      <audio ref={audioRef} src={src} preload="metadata" />
      <div className="vy-audio-main-row">
        <IconButton className="vy-audio-play" onClick={togglePlay}>
          {playing ? <PauseIcon /> : <PlayArrowIcon />}
        </IconButton>
        <div className="vy-audio-progress-wrap">
          <input
            className="vy-audio-progress"
            type="range"
            min="0"
            max={duration || 0}
            step="0.1"
            value={currentTime}
            onChange={(e) => seek(e.target.value)}
          />
          <div className="vy-audio-time-row">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>
      </div>
      <div className="vy-audio-controls">
        <div className="vy-audio-volume">
          <VolumeUpIcon fontSize="small" />
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
          />
        </div>
        <Select
          size="small"
          value={speed}
          onChange={(e) => setSpeed(Number(e.target.value))}
          sx={{ minWidth: 88 }}
        >
          <MenuItem value={0.75}>0.75x</MenuItem>
          <MenuItem value={1}>1x</MenuItem>
          <MenuItem value={1.25}>1.25x</MenuItem>
        </Select>
      </div>
    </div>
  );
}

export default AwaazAudioPlayer;
