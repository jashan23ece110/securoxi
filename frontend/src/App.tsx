import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { HomePage } from './pages/Home';
import { OverviewPage } from './pages/Overview';
import { SecurityBrainPage } from './pages/SecurityBrain';
import { IncidentsPage } from './pages/Incidents';
import { ScansPage } from './pages/Scans';
import { ScreeningPage } from './pages/Screening';
import { MonitoringPage } from './pages/Monitoring';
import { PoliciesPage } from './pages/Policies';
import { AuditPage } from './pages/Audit';
import { SettingsPage } from './pages/Settings';
import { DocumentsPage } from './pages/Documents';
import { ATSPage } from './pages/ATS';
import { DesignSystemShowcase } from './pages/DesignSystemShowcase';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/overview" element={<OverviewPage />} />
          <Route path="/security-brain" element={<SecurityBrainPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/scans" element={<ScansPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/screening" element={<ScreeningPage />} />
          <Route path="/ats" element={<ATSPage />} />
          <Route path="/monitoring" element={<MonitoringPage />} />
          <Route path="/policies" element={<PoliciesPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/design-system" element={<DesignSystemShowcase />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
};

export default App;
