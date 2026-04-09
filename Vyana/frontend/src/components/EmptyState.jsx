import { Button } from "@mui/material";

function EmptyState({ text = "No data available yet.", actionText, onAction }) {
  return (
    <div className="vy-empty">
      <div className="vy-empty-icon">○</div>
      <h4>{text}</h4>
      {actionText ? (
        <Button variant="outlined" onClick={onAction}>
          {actionText}
        </Button>
      ) : null}
    </div>
  );
}

export default EmptyState;
