import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useAuth } from "../context/AuthContext";

const ROLE_OPTIONS = [
  { value: "patient", label: "Patient", hint: "Access the registration and voice flow" },
  { value: "asha", label: "ASHA Worker", hint: "Review patients and alerts" },
  { value: "district", label: "District Officer", hint: "Open district analytics" },
  { value: "admin", label: "Admin", hint: "Open the full control room" },
];

function LoginPage() {
  const navigate = useNavigate();
  const { login, user } = useAuth();
  const [role, setRole] = useState(user?.role || "patient");
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [accessCode, setAccessCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const nextUser = await login({ role, accessCode, displayName });
      if (nextUser.role === "asha") {
        navigate("/asha", { replace: true });
      } else if (nextUser.role === "district") {
        navigate("/district", { replace: true });
      } else {
        navigate("/", { replace: true });
      }
    } catch (err) {
      setError(err?.response?.data?.error || err?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box className="vy-login-shell">
      <Card className="vy-card vy-login-card">
        <CardContent>
          <Stack spacing={2.5}>
            <Box>
              <Typography variant="overline" sx={{ letterSpacing: 2, color: "primary.main" }}>
                Secure access
              </Typography>
              <Typography variant="h4" fontWeight={800}>
                Sign in to Vyana Care
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Use the local access codes to enter the patient, ASHA, or district workspace.
              </Typography>
            </Box>

            <Stack direction="row" spacing={1} flexWrap="wrap">
              {ROLE_OPTIONS.map((option) => (
                <Chip
                  key={option.value}
                  label={option.label}
                  color={role === option.value ? "primary" : "default"}
                  variant={role === option.value ? "filled" : "outlined"}
                  onClick={() => setRole(option.value)}
                />
              ))}
            </Stack>

            <Box component="form" onSubmit={handleSubmit} sx={{ display: "grid", gap: 2 }}>
              <TextField select label="Role" value={role} onChange={(event) => setRole(event.target.value)}>
                {ROLE_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label} - {option.hint}
                  </MenuItem>
                ))}
              </TextField>
              <TextField label="Display name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="Optional" />
              <TextField label="Access code" value={accessCode} onChange={(event) => setAccessCode(event.target.value)} type="password" required />

              {error ? <Alert severity="error">{error}</Alert> : null}

              <Button type="submit" variant="contained" size="large" disabled={loading}>
                {loading ? "Signing in..." : "Continue"}
              </Button>
            </Box>

            <Divider />
            <Typography variant="body2" color="text.secondary">
              Demo codes default to <strong>patient-1234</strong>, <strong>asha-1234</strong>, <strong>district-1234</strong>, and <strong>admin-1234</strong> unless overridden in the environment.
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}

export default LoginPage;