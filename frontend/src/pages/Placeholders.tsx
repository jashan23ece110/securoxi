import React from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { PageHeader } from '../components/layout/PageHeader';
import { PageContainer } from '../components/layout/PageContainer';
import { FileText, Zap } from 'lucide-react';

export const PagePlaceholder: React.FC<{
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  category: string;
}> = ({ title, subtitle, icon, category }) => {
  return (
    <PageContainer>
      <PageHeader
        title={title}
        subtitle={subtitle}
        breadcrumbs={[{ label: category }, { label: title }]}
        badge={<Badge variant="info">Enterprise Subsystem</Badge>}
      />

      <Card>
        <div
          style={{
            padding: '48px 24px',
            textAlign: 'center',
            color: 'var(--text-muted)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-default)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-cyan)',
              marginBottom: '8px',
            }}
          >
            {icon}
          </div>
          <h3 style={{ color: 'var(--text-primary)', fontSize: '1.0625rem', fontWeight: 700 }}>
            {title} Console Operational
          </h3>
          <p style={{ maxWidth: '480px', margin: '0 auto', fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Enterprise API routes and connector pipelines configured for multi-tenant tenant isolation and live webhook ingest.
          </p>
        </div>
      </Card>
    </PageContainer>
  );
};

export const DocumentsPage = () => (
  <PagePlaceholder
    title="Document Repository"
    subtitle="Ingested resumes, job descriptions & scan status"
    icon={<FileText size={24} />}
    category="DOCUMENTS"
  />
);

export const AtsPage = () => (
  <PagePlaceholder
    title="ATS & Data Connectors"
    subtitle="Greenhouse, Lever & cloud storage integrations"
    icon={<Zap size={24} />}
    category="HIRING"
  />
);
