import { useEffect, useState } from "react";
import { Box, Button, Card, CardContent, Chip, Stack, TextField, Typography } from "@mui/material";
import toast from "react-hot-toast";
import api from "../api/axios";

function IntegrationsPage() {
  const [health, setHealth] = useState(null);
  const [abhaId, setAbhaId] = useState("");
  const [patientId, setPatientId] = useState("");
  const [twilioToNumber, setTwilioToNumber] = useState("+919026792218");
  const [twilioMessage, setTwilioMessage] = useState("Vyana Care Twilio verification call");
  const [twilioResult, setTwilioResult] = useState(null);
  const [twilioLoading, setTwilioLoading] = useState(false);
  const [hmisPreview, setHmisPreview] = useState(null);
  const [ambulanceHistory, setAmbulanceHistory] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [healthRes, ambulanceRes] = await Promise.all([
          api.get("/health"),
          api.get("/ambulance/history"),
        ]);
        setHealth(healthRes.data?.data || null);
        setAmbulanceHistory(ambulanceRes.data?.data?.dispatches || []);
      } catch {
        toast.error("Integrations data load nahi ho saka");
      }
    };
    load();
  }, []);

  const linkAbha = async () => {
    try {
      await api.post("/abha/link-patient", { patient_id: Number(patientId), abha_id: abhaId });
      toast.success("ABHA link successful");
    } catch {
      toast.error("ABHA link failed");
    }
  };

  const generateHmis = async () => {
    try {
      const res = await api.get("/hmis/export/weekly/Barmer");
      setHmisPreview(res.data?.data?.report || null);
      toast.success("HMIS report ready");
    } catch {
      toast.error("HMIS report failed");
    }
  };

  const pushHmis = async () => {
    try {
      await api.post("/hmis/sync", { district: "Barmer" });
      toast.success("HMIS sync done");
    } catch {
      toast.error("HMIS sync failed");
    }
  };

  const triggerTwilioTestCall = async () => {
    setTwilioLoading(true);
    setTwilioResult(null);
    try {
      const res = await api.post("/ivr/twilio-test-call", {
        to_number: twilioToNumber,
        message: twilioMessage,
      });
      setTwilioResult(res.data?.data || null);
      toast.success("Twilio test call queued");
    } catch (error) {
      const message = error?.response?.data?.error || "Twilio test call failed";
      toast.error(message);
      setTwilioResult({ error: message });
    } finally {
      setTwilioLoading(false);
    }
  };

  return (
    <Box className="vy-page">
      <Card className="vy-card">
        <CardContent>
          <Typography variant="h5" fontWeight={700}>Government Integrations</Typography>
          <Typography variant="body2" color="text.secondary">District officer control panel for ABHA, HMIS, and 108.</Typography>
        </CardContent>
      </Card>

      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <Card className="vy-card" sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6">ABHA Integration</Typography>
            <Chip sx={{ mt: 1, mb: 2, mr: 1 }} color={health?.abha_api === "available" ? "success" : "warning"} label={health?.abha_api === "available" ? "Connected" : "Sandbox/Mock"} />
            <Chip sx={{ mt: 1, mb: 2 }} color={health?.twilio_api === "available" ? "success" : "warning"} label={health?.twilio_api === "available" ? "Twilio Connected" : "Twilio Missing"} />
            <Stack spacing={1.5}>
              <TextField label="Patient ID" value={patientId} onChange={(e) => setPatientId(e.target.value)} />
              <TextField label="ABHA ID" value={abhaId} onChange={(e) => setAbhaId(e.target.value)} />
              <Button variant="contained" onClick={linkAbha}>ABHA Link Karein</Button>
            </Stack>
          </CardContent>
        </Card>

        <Card className="vy-card" sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6">Twilio Voice Test</Typography>
            <Chip sx={{ mt: 1, mb: 2 }} color={health?.twilio_api === "available" ? "success" : "warning"} label={health?.twilio_api === "available" ? "Configured" : "Needs Config"} />
            <Stack spacing={1.5}>
              <TextField label="To Number" value={twilioToNumber} onChange={(e) => setTwilioToNumber(e.target.value)} />
              <TextField label="Voice Message" value={twilioMessage} onChange={(e) => setTwilioMessage(e.target.value)} multiline minRows={3} />
              <Button variant="contained" onClick={triggerTwilioTestCall} disabled={twilioLoading}>
                {twilioLoading ? "Placing Call..." : "Place Twilio Test Call"}
              </Button>
              {twilioResult ? (
                <pre className="vy-json-preview">{JSON.stringify(twilioResult, null, 2)}</pre>
              ) : null}
            </Stack>
          </CardContent>
        </Card>

        <Card className="vy-card" sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6">HMIS Sync</Typography>
            <Stack spacing={1.5} sx={{ mt: 2 }}>
              <Button variant="outlined" onClick={generateHmis}>Weekly Report Generate Karein</Button>
              <Button variant="contained" onClick={pushHmis}>HMIS Mein Push Karein</Button>
              {hmisPreview ? (
                <pre className="vy-json-preview">{JSON.stringify(hmisPreview, null, 2)}</pre>
              ) : null}
            </Stack>
          </CardContent>
        </Card>
      </Stack>

      <Card className="vy-card">
        <CardContent>
          <Typography variant="h6">108 Ambulance Tracker</Typography>
          <div className="vy-table-wrap">
            <table className="vy-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Village</th>
                  <th>Status</th>
                  <th>ETA</th>
                </tr>
              </thead>
              <tbody>
                {ambulanceHistory.slice(0, 10).map((row) => (
                  <tr key={row.dispatch_id}>
                    <td>{row.patient_name}</td>
                    <td>{row.village}</td>
                    <td>{row.status}</td>
                    <td>{row.eta_minutes} min</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </Box>
  );
}

export default IntegrationsPage;
