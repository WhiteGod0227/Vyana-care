import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Box } from "@mui/material";
import { Toaster } from "react-hot-toast";
import Navbar from "./components/Navbar";
import OfflineBanner from "./components/OfflineBanner";
import useOffline from "./hooks/useOffline";

const PatientPortal = lazy(() => import("./pages/PatientPortal"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const AwaazPage = lazy(() => import("./pages/AwaazPage"));
const AwaazNursePage = lazy(() => import("./pages/AwaazNursePage"));
const AshaDashboard = lazy(() => import("./pages/AshaDashboard"));
const DistrictDashboard = lazy(() => import("./pages/DistrictDashboard"));
const IntegrationsPage = lazy(() => import("./pages/IntegrationsPage"));

function App() {
  const { isOnline, pendingCount, flushQueue, syncStatus } = useOffline();

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <Toaster position="top-right" />
      <OfflineBanner isOnline={isOnline} pendingCount={pendingCount} onSync={flushQueue} syncStatus={syncStatus} />
      <Navbar />
      <main className="vy-main-shell">
        <Suspense fallback={<Box sx={{ minHeight: "40vh" }} />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<PatientPortal />} />
            <Route path="/awaaz" element={<AwaazPage />} />
            <Route path="/awaaz/nurse" element={<AwaazNursePage />} />
            <Route path="/asha" element={<AshaDashboard />} />
            <Route path="/district" element={<DistrictDashboard />} />
            <Route path="/integrations" element={<IntegrationsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
      <footer className="vy-site-footer">
        <img className="vy-footer-logo" src="/vyana-care-logo-enhanced.png" alt="Vyana Care" />
      </footer>
    </Box>
  );
}

export default App;
