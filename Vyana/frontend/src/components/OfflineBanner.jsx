import { motion } from "framer-motion";
import { Button } from "@mui/material";

function OfflineBanner({ isOnline, pendingCount, onSync, syncStatus }) {
  if (isOnline && pendingCount === 0) {
    return null;
  }

  return (
    <motion.div className="vy-offline-top" initial={{ y: -72, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -72, opacity: 0 }}>
      <div>
        {!isOnline ? "Aap offline hain - changes save ho rahe hain" : "Pending data sync ke liye ready hai"}
      </div>
      <div className="vy-offline-actions">
        <span className="vy-offline-badge">{pendingCount}</span>
        <Button size="small" variant="contained" disabled={!isOnline || pendingCount === 0 || syncStatus === "syncing"} onClick={onSync}>
          {syncStatus === "syncing" ? "Sync ho raha hai..." : "Abhi Sync Karein"}
        </Button>
      </div>
    </motion.div>
  );
}

export default OfflineBanner;
