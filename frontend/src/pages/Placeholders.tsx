import React from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const PagePlaceholder: React.FC<{ title: string; subtitle: string; icon: string }> = ({
  title,
  subtitle,
  icon,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span>{icon}</span>
            <span>{title}</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{subtitle}</p>
        </div>
        <Badge variant="info">Stage 1 Architecture Shell Ready</Badge>
      </div>

      <Card>
        <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>{icon}</div>
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>{title} Subsystem Ready</h3>
          <p style={{ maxWidth: '480px', margin: '0 auto', fontSize: '0.875rem' }}>
            Frontend application shell and design system tokens initialized. Full interactive view will be populated in Stage 2.
          </p>
        </div>
      </Card>
    </div>
  );
};

export const OverviewPage = () => <PagePlaceholder title="Enterprise Overview" subtitle="System risk summary & threat telemetry" icon="📊" />;
export const SecurityBrainPage = () => <PagePlaceholder title="Security Brain" subtitle="AI reasoning layer & attack graphs" icon="🧠" />;
export const IncidentsPage = () => <PagePlaceholder title="Incident Response" subtitle="Triaged security events & automated policy actions" icon="🚨" />;
export const DocumentsPage = () => <PagePlaceholder title="Document Repository" subtitle="Ingested resumes, job descriptions & scan status" icon="📄" />;
export const ScansPage = () => <PagePlaceholder title="Scan Console" subtitle="On-demand layout-aware document threat scanner" icon="🔍" />;
export const ScreeningPage = () => <PagePlaceholder title="Security-Aware Candidate Screening" subtitle="Semantic resume-to-JD fit & clearance scoring" icon="👤" />;
export const AtsPage = () => <PagePlaceholder title="ATS & Data Connectors" subtitle="Greenhouse, Lever & cloud storage integrations" icon="⚡" />;
export const MonitoringPage = () => <PagePlaceholder title="Continuous Monitoring" subtitle="Real-time event ingestion pipeline & rate metrics" icon="📈" />;
export const PoliciesPage = () => <PagePlaceholder title="Security Policies" subtitle="Deterministic policy engine rules & RBAC governance" icon="🛡️" />;
export const AuditPage = () => <PagePlaceholder title="Audit Trail" subtitle="Immutable multi-tenant audit logs & event history" icon="📜" />;
export const SettingsPage = () => <PagePlaceholder title="Enterprise Control Plane" subtitle="Tenant settings, API keys & retention controls" icon="⚙️" />;
