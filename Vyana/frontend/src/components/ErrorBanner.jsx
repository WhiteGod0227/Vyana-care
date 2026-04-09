import { useEffect } from "react";

function ErrorBanner({ message, onClose }) {
  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(() => onClose?.(), 5000);
    return () => clearTimeout(timer);
  }, [message, onClose]);

  if (!message) return null;

  return (
    <div className="vy-error-banner">
      Something went wrong. Please try again. {message}
    </div>
  );
}

export default ErrorBanner;
