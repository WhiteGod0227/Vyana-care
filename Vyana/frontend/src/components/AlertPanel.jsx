import { AnimatePresence, motion as Motion } from "framer-motion";
import { Button } from "@mui/material";

function levelLabel(level) {
  if (level === 1) return "L1: ASHA Notified";
  if (level === 2) return "L2: Family Informed";
  return "L3: PHC Alerted";
}

function AlertPanel({ open, alerts, onAcknowledge }) {
  const visible = open === undefined ? true : open;

  return (
    <AnimatePresence>
      {visible ? (
        <Motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          className="vy-alert-panel vy-card"
        >
          <h4>Active Alerts ({alerts.length})</h4>
          {alerts.length === 0 ? <p className="vy-muted">No active alerts right now.</p> : null}
          {alerts.map((item) => (
            <Motion.div
              key={item.alert_id}
              layout
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 30 }}
              className="vy-alert-item"
            >
              <strong>{item.patient_name}</strong>
              <p>{item.risk_reason}</p>
              <div className="vy-alert-meta">
                <span>{levelLabel(item.escalation_level)}</span>
                <span>{item.time_ago}</span>
              </div>
              <div className="vy-progress-bar">
                <div
                  className="vy-progress-inner"
                  style={{ width: `${Math.min(100, item.escalation_level * 33)}%` }}
                />
              </div>
              <Button size="small" variant="contained" onClick={() => onAcknowledge(item.alert_id)}>
                Acknowledge ✓
              </Button>
            </Motion.div>
          ))}
        </Motion.div>
      ) : null}
    </AnimatePresence>
  );
}

export default AlertPanel;
