import { Navigate, Route, Routes } from "react-router-dom";
import { Box } from "@mui/material";
import { Toaster } from "react-hot-toast";
import Navbar from "./components/Navbar";
import PatientPortal from "./pages/PatientPortal";
import LoginPage from "./pages/LoginPage";
import AwaazPage from "./pages/AwaazPage";
import AwaazNursePage from "./pages/AwaazNursePage";
import AshaDashboard from "./pages/AshaDashboard";
import DistrictDashboard from "./pages/DistrictDashboard";

function App() {
  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <Toaster position="top-right" />
      <Navbar />
      <main className="vy-main-shell">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<PatientPortal />} />
          <Route path="/awaaz" element={<AwaazPage />} />
          <Route path="/awaaz/nurse" element={<AwaazNursePage />} />
          <Route path="/asha" element={<AshaDashboard />} />
          <Route path="/district" element={<DistrictDashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="vy-site-footer">
        <img className="vy-footer-logo" src="/vyana-care-logo-enhanced.png" alt="Vyana Care" />
      </footer>
    </Box>
  );
}

export default App;
