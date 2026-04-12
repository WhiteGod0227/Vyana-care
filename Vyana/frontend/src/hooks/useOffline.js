import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import api from "../api/axios";

const STORAGE_KEY = "vyana_offline_queue";

function readQueue() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export default function useOffline() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingQueue, setPendingQueue] = useState(() => readQueue());
  const [syncStatus, setSyncStatus] = useState("idle");

  const queueAction = useCallback((actionType, payload) => {
    const next = [
      ...readQueue(),
      {
        action_type: actionType,
        payload,
        local_timestamp: new Date().toISOString(),
        local_id: crypto.randomUUID(),
      },
    ];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setPendingQueue(next);
    toast.success("Offline save hua - sync hoga jab net aayega");
  }, []);

  const flushQueue = useCallback(async () => {
    const current = readQueue();
    if (!navigator.onLine || current.length === 0) {
      return;
    }

    setSyncStatus("syncing");
    try {
      const deviceId = localStorage.getItem("vyana_device_id") || crypto.randomUUID();
      localStorage.setItem("vyana_device_id", deviceId);

      const response = await api.post("/sync/batch", { device_id: deviceId, queued_actions: current });
      const processed = response.data?.data?.processed || 0;
      localStorage.removeItem(STORAGE_KEY);
      setPendingQueue([]);
      setSyncStatus("done");
      toast.success(`${processed} actions sync ho gaye!`);
    } catch {
      setSyncStatus("idle");
    }
  }, []);

  useEffect(() => {
    const onOnline = () => {
      setIsOnline(true);
      flushQueue();
    };
    const onOffline = () => setIsOnline(false);

    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    if (navigator.onLine) {
      flushQueue();
    }

    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, [flushQueue]);

  const pendingCount = useMemo(() => pendingQueue.length, [pendingQueue]);

  return {
    isOnline,
    pendingQueue,
    pendingCount,
    syncStatus,
    queueAction,
    flushQueue,
  };
}
