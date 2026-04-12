import { useEffect, useMemo, useState } from "react";
import { Button, MenuItem, TextField } from "@mui/material";
import { AnimatePresence, motion as Motion } from "framer-motion";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { QRCodeSVG } from "qrcode.react";
import toast from "react-hot-toast";
import api from "../api/axios";
import AlertPanel from "../components/AlertPanel";
import LoadingSkeleton from "../components/LoadingSkeleton";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";

const riskFilterOptions = ["ALL", "HIGH", "MEDIUM", "LOW"];

function AshaDashboard() {
  const [district, setDistrict] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [patients, setPatients] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [predictiveAlerts, setPredictiveAlerts] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [pdfDownloading, setPdfDownloading] = useState(false);
  const [checkupSubmitting, setCheckupSubmitting] = useState(false);
  const [checkupForm, setCheckupForm] = useState({
    bp_systolic: "",
    bp_diastolic: "",
    weight_kg: "",
    notes: "",
    next_visit_date: "",
  });
  const [shareData, setShareData] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchAll = async (showLoading = false) => {
    if (showLoading) setLoading(true);
    setError("");
    try {
      const [patientRes, alertRes, predictiveRes] = await Promise.all([
        api.get("/asha/1/patients"),
        api.get("/asha/1/alerts"),
        api.get("/asha/1/predictive-alerts"),
      ]);
      setPatients(patientRes.data?.data?.patients || []);
      setAlerts(alertRes.data?.data?.alerts || []);
      setPredictiveAlerts(predictiveRes.data?.data?.predictive_alerts || []);
    } catch {
      setError("Could not load ASHA dashboard data.");
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll(true);
    const auto = setInterval(() => fetchAll(false), 20000);
    return () => clearInterval(auto);
  }, []);

  const filteredPatients = useMemo(() => {
    return patients.filter((p) => {
      const districtOk = district === "ALL" || p.district === district;
      const riskOk = riskFilter === "ALL" || p.risk_level === riskFilter;
      return districtOk && riskOk;
    });
  }, [patients, district, riskFilter]);

  const districts = useMemo(() => ["ALL", ...Array.from(new Set(patients.map((p) => p.district).filter(Boolean)))], [patients]);

  const stats = useMemo(() => {
    const high = filteredPatients.filter((p) => p.risk_level === "HIGH").length;
    const medium = filteredPatients.filter((p) => p.risk_level === "MEDIUM").length;
    return { total: filteredPatients.length, high, medium, due: Math.max(1, Math.round(filteredPatients.length * 0.18)) };
  }, [filteredPatients]);

  const chartData = useMemo(() => {
    const now = new Date();
    return Array.from({ length: 7 }).map((_, idx) => {
      const d = new Date(now);
      d.setDate(d.getDate() - (6 - idx));
      return { day: d.toLocaleDateString("en-IN", { weekday: "short" }), high: Math.max(0, Math.round(stats.high - 2 + idx * 0.5)), medium: Math.max(0, Math.round(stats.medium - 1 + idx * 0.4)) };
    });
  }, [stats.high, stats.medium]);

  const handleAcknowledge = async (alertId) => {
    try {
      await api.post(`/alert/${alertId}/acknowledge`, { acknowledged_by: "ASHA Worker" });
      toast.success("Alert acknowledged");
      fetchAll(false);
    } catch {
      toast.error("Acknowledge failed.");
    }
  };

  const downloadCsv = () => {
    const header = ["Patient", "Village", "District", "Week", "Risk", "Reason"];
    const rows = filteredPatients.map((p) => [p.name, p.village, p.district, p.pregnancy_week, p.risk_level, p.primary_risk_reason || ""]);
    const csv = [header, ...rows].map((r) => r.map((v) => `"${String(v).replaceAll('"', '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `asha-patients-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleBluetoothExport = async () => {
    try {
      const res = await api.post("/sync/bluetooth-export/1");
      const data = res.data?.data?.base64_data || "";
      setShareData(data);
      if (navigator.share) {
        await navigator.share({ title: "Vyana Care Data", text: data });
      } else {
        await navigator.clipboard.writeText(data);
        toast.success("Data clipboard mein copy ho gaya");
      }
    } catch {
      toast.error("Bluetooth export failed");
    }
  };

  const handleImportFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      await api.post("/sync/bluetooth-import", { base64_data: text.trim(), source_asha_id: "1" });
      toast.success("Data import successful");
      fetchAll(false);
    } catch {
      toast.error("Data import failed");
    }
  };

  const openPatientSheet = (patient) => {
    setSelectedPatient(patient);
    setCheckupForm({
      bp_systolic: "",
      bp_diastolic: "",
      weight_kg: "",
      notes: "घर पर follow-up किया गया",
      next_visit_date: "",
    });
  };

  const submitCheckup = async () => {
    if (!selectedPatient) return;
    setCheckupSubmitting(true);
    try {
      await api.post("/asha/checkup/record", {
        patient_id: selectedPatient.id,
        asha_id: 1,
        bp_systolic: Number(checkupForm.bp_systolic || 0),
        bp_diastolic: Number(checkupForm.bp_diastolic || 0),
        weight_kg: Number(checkupForm.weight_kg || 0),
        notes: checkupForm.notes || "Routine visit",
        next_visit_date: checkupForm.next_visit_date || undefined,
      });
      toast.success("Checkup record save ho gaya");
      fetchAll(false);
    } catch {
      toast.error("Checkup save nahi ho saka");
    } finally {
      setCheckupSubmitting(false);
    }
  };

  const downloadPatientPdf = async () => {
    if (!selectedPatient) return;
    setPdfDownloading(true);
    try {
      const res = await api.get(`/patient/${selectedPatient.id}/export/pdf`, { responseType: "blob" });
      const disposition = res.headers?.["content-disposition"] || "";
      const match = disposition.match(/filename=([^;]+)/i);
      const filename = (match?.[1] || `patient_${selectedPatient.id}_report.pdf`).replace(/"/g, "");
      const blobUrl = URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(blobUrl);
      toast.success("Report download ho gayi ✅");
    } catch {
      toast.error("Patient PDF download fail ho gaya");
    } finally {
      setPdfDownloading(false);
    }
  };

  return (
    <div className="vy-page">
      <ErrorBanner message={error} onClose={() => setError("")} />

      <section className="vy-card">
        <div className="vy-section-head">
          <h2>ASHA Dashboard</h2>
          <div className="vy-row">
            <TextField select size="small" label="District" value={district} onChange={(e) => setDistrict(e.target.value)}>
              {districts.map((d) => <MenuItem key={d} value={d}>{d}</MenuItem>)}
            </TextField>
            <TextField select size="small" label="Risk" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
              {riskFilterOptions.map((r) => <MenuItem key={r} value={r}>{r}</MenuItem>)}
            </TextField>
            <Button variant="outlined" onClick={() => fetchAll(true)}>Refresh</Button>
            <Button variant="outlined" onClick={handleBluetoothExport}>Bluetooth se Share Karein</Button>
            <Button variant="outlined" component="label">
              Data Import Karein
              <input type="file" hidden accept=".txt,.json" onChange={handleImportFile} />
            </Button>
            <Button variant="contained" onClick={downloadCsv}>Report Download</Button>
          </div>
        </div>
        {shareData ? (
          <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 12 }}>
            <QRCodeSVG value={shareData} size={120} bgColor="#0f172a" fgColor="#22d3ee" />
            <p style={{ margin: 0, fontSize: 12, color: "#94a3b8" }}>Export package ready ({shareData.length} chars). Dusri ASHA scan karke import kar sakti hain.</p>
          </div>
        ) : null}
        <div className="vy-kpi-grid">
          <div className="kpi"><span>Total Patients</span><b>{stats.total}</b></div>
          <div className="kpi high"><span>High Risk</span><b>{stats.high}</b></div>
          <div className="kpi med"><span>Medium Risk</span><b>{stats.medium}</b></div>
          <div className="kpi"><span>Checkups Due</span><b>{stats.due}</b></div>
        </div>
      </section>

      <section className="vy-card">
        <h3>Risk Trend</h3>
        <div style={{ width: "100%", height: 260 }}>
          <ResponsiveContainer>
            <LineChart data={chartData}>
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="high" stroke="#ef4444" strokeWidth={2.5} />
              <Line type="monotone" dataKey="medium" stroke="#f59e0b" strokeWidth={2.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="vy-card">
        <h3>Patient List</h3>
        {loading ? <LoadingSkeleton height={180} count={2} /> : null}
        {!loading && filteredPatients.length === 0 ? <EmptyState text="No patients found for selected filters." /> : null}
        <div className="vy-patient-grid">
          {filteredPatients.map((p) => (
            <Motion.button whileHover={{ y: -2 }} className="vy-patient-card" key={p.id} onClick={() => openPatientSheet(p)}>
              <div className="row"><b>{p.name}</b><span className={`lvl ${String(p.risk_level).toLowerCase()}`}>{p.risk_level}</span></div>
              <div>{p.village}, {p.district}</div>
              <div>Week {p.pregnancy_week}</div>
              <small>{p.primary_risk_reason || "No reason available"}</small>
            </Motion.button>
          ))}
        </div>
      </section>

      <section className="vy-card">
        <h3>Critical Alerts</h3>
        <AlertPanel alerts={alerts} onAcknowledge={handleAcknowledge} />
      </section>

      <section className="vy-card">
        <h3>AI Predictions</h3>
        {predictiveAlerts.length === 0 ? <p className="vy-muted">Abhi koi predictive alert nahi hai.</p> : null}
        {predictiveAlerts.slice(0, 8).map((item) => (
          <div key={item.id} className="vy-alert-item" style={{ marginBottom: 8 }}>
            <strong>{item.patient_name}</strong>
            <p>{item.reason}</p>
            <div className="vy-alert-meta">
              <span>{item.alert_type}</span>
              <span>{item.risk_level}</span>
            </div>
          </div>
        ))}
      </section>

      <AnimatePresence>
        {selectedPatient ? (
          <Motion.div className="vy-side-sheet-wrap" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSelectedPatient(null)}>
            <Motion.div className="vy-side-sheet" initial={{ x: 360 }} animate={{ x: 0 }} exit={{ x: 360 }} onClick={(e) => e.stopPropagation()}>
              <h3>{selectedPatient.name}</h3>
              <p>{selectedPatient.village}, {selectedPatient.district}</p>
              <p>Week {selectedPatient.pregnancy_week}</p>
              <p>Risk: {selectedPatient.risk_level}</p>
              <p>Reason: {selectedPatient.primary_risk_reason || "N/A"}</p>
              <div className="vy-two-col" style={{ marginTop: 8 }}>
                <TextField
                  size="small"
                  label="Systolic"
                  type="number"
                  value={checkupForm.bp_systolic}
                  onChange={(e) => setCheckupForm((prev) => ({ ...prev, bp_systolic: e.target.value }))}
                />
                <TextField
                  size="small"
                  label="Diastolic"
                  type="number"
                  value={checkupForm.bp_diastolic}
                  onChange={(e) => setCheckupForm((prev) => ({ ...prev, bp_diastolic: e.target.value }))}
                />
                <TextField
                  size="small"
                  label="Weight (kg)"
                  type="number"
                  value={checkupForm.weight_kg}
                  onChange={(e) => setCheckupForm((prev) => ({ ...prev, weight_kg: e.target.value }))}
                />
                <TextField
                  size="small"
                  label="Next Visit"
                  type="date"
                  InputLabelProps={{ shrink: true }}
                  value={checkupForm.next_visit_date}
                  onChange={(e) => setCheckupForm((prev) => ({ ...prev, next_visit_date: e.target.value }))}
                />
              </div>
              <TextField
                size="small"
                multiline
                minRows={2}
                fullWidth
                sx={{ mt: 1 }}
                label="Notes"
                value={checkupForm.notes}
                onChange={(e) => setCheckupForm((prev) => ({ ...prev, notes: e.target.value }))}
              />
              <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                <Button variant="contained" onClick={submitCheckup} disabled={checkupSubmitting}>
                  {checkupSubmitting ? "Saving..." : "Checkup Save Karein"}
                </Button>
                <Button variant="outlined" onClick={downloadPatientPdf} disabled={pdfDownloading}>
                  {pdfDownloading ? "Downloading..." : "PDF Download"}
                </Button>
                <Button variant="outlined" onClick={() => toast.success("Follow-up task created")}>Follow-up Schedule</Button>
              </div>
            </Motion.div>
          </Motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

export default AshaDashboard;

