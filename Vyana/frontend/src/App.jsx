import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "react-hot-toast";

const VyanaHome = lazy(() => import("./pages/VyanaHome"));
const PatientPortal = lazy(() => import("./pages/PatientPortal"));
const AwaazPage = lazy(() => import("./pages/AwaazPage"));
const AwaazNursePage = lazy(() => import("./pages/AwaazNursePage"));
const AshaDashboard = lazy(() => import("./pages/AshaDashboard"));
const DistrictDashboard = lazy(() => import("./pages/DistrictDashboard"));
const IntegrationsPage = lazy(() => import("./pages/IntegrationsPage"));

function App() {
  return (
    <div style={{ minHeight: "100vh" }}>
      <Toaster position="top-right" />
      <Suspense
        fallback={
          <div
            style={{
              minHeight: "100vh",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "#F5FAF9",
              color: "#0D5C63",
              fontFamily: "Plus Jakarta Sans, sans-serif",
              fontSize: "18px",
              fontWeight: 700,
            }}
          >
            🌸 व्यान केयर लोड हो रहा है...
          </div>
        }
      >
        <Routes>
          <Route path="/" element={<VyanaHome />} />
          <Route path="/patient" element={<VyanaHome />} />
          <Route path="/patient-legacy" element={<PatientPortal />} />
          <Route path="/awaaz" element={<AwaazPage />} />
          <Route path="/awaaz/nurse" element={<AwaazNursePage />} />
          <Route path="/asha" element={<AshaDashboard />} />
          <Route path="/district" element={<DistrictDashboard />} />
          <Route path="/integrations" element={<IntegrationsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </div>
  );
}

export default App;
