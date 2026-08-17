import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { DesignSystemShowcase } from './pages/DesignSystemShowcase';
import {
  OverviewPage,
  SecurityBrainPage,
  IncidentsPage,
  DocumentsPage,
  ScansPage,
  ScreeningPage,
  AtsPage,
  MonitoringPage,
  PoliciesPage,
  AuditPage,
  SettingsPage,
} from './pages/Placeholders';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<OverviewPage />} />
          <Route path="/security-brain" element={<SecurityBrainPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/scans" element={<ScansPage />} />
          <Route path="/screening" element={<ScreeningPage />} />
          <Route path="/ats" element={<AtsPage />} />
          <Route path="/monitoring" element={<MonitoringPage />} />
          <Route path="/policies" element={<PoliciesPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/design-system" element={<DesignSystemShowcase />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
};

export default App;
