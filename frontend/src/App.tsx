import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { MotionConfig } from "framer-motion";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { SchoolsPage } from "./pages/SchoolsPage";
import { StudentsPage } from "./pages/StudentsPage";
import { RiskIntelligencePage } from "./pages/RiskIntelligencePage";
import { PlannerPage } from "./pages/PlannerPage";
import { InterventionsPage } from "./pages/InterventionsPage";
import { OutcomesPage } from "./pages/OutcomesPage";
import { AssistantPage } from "./pages/AssistantPage";
import { ImpactReportsPage } from "./pages/ImpactReportsPage";
import { DataUploadPage } from "./pages/DataUploadPage";
import { NotificationsPage } from "./pages/NotificationsPage";

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FFF9FB] text-sm text-[#687482]">
        Loading ShikshaSetu Foundation...
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export function App() {
  return (
    <MotionConfig reducedMotion="user">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="schools" element={<SchoolsPage />} />
              <Route path="students" element={<StudentsPage />} />
              <Route path="risk-intelligence" element={<RiskIntelligencePage />} />
              <Route path="planner" element={<PlannerPage />} />
              <Route path="interventions" element={<InterventionsPage />} />
              <Route path="outcomes" element={<OutcomesPage />} />
              <Route path="assistant" element={<AssistantPage />} />
              <Route path="impact-reports" element={<ImpactReportsPage />} />
              <Route path="data-upload" element={<DataUploadPage />} />
              <Route path="notifications" element={<NotificationsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </MotionConfig>
  );
}

export default App;
