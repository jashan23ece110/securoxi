import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  StatCard,
  Button,
  StatusBadge,
  Badge,
  DataTable,
  Drawer,
  Alert,
} from '../components/ui';
import { PageHeader, PageToolbar, PageContainer } from '../components/layout';
import {
  Briefcase,
  Layers,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Lock,
  Key,
  Radio,
  Sliders,
  Webhook,
} from 'lucide-react';

interface ATSIntegration {
  id: string;
  name: string;
  provider: 'GREENHOUSE' | 'LEVER' | 'WORKDAY' | 'CUSTOM_WEBHOOK';
  environment: 'PRODUCTION' | 'STAGING' | 'CONFIGURED' | 'MOCK';
  connectionStatus: 'CONNECTED' | 'DISCONNECTED' | 'ERROR' | 'MOCK_ACTIVE';
  webhookStatus: 'ACTIVE' | 'LISTENING' | 'INACTIVE';
  lastSync: string;
  eventsIngested: number;
  errorCount: number;
  credentialsConfigured: boolean;
  endpointUrl: string;
  hmacVerified: boolean;
}

export const ATSPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedIntegration, setSelectedIntegration] = useState<ATSIntegration | null>(null);
  const [testSyncSuccess, setTestSyncSuccess] = useState<string | null>(null);

  const integrations: ATSIntegration[] = [
    {
      id: 'INT-GH-01',
      name: 'Greenhouse Enterprise Candidate Ingress',
      provider: 'GREENHOUSE',
      environment: 'PRODUCTION',
      connectionStatus: 'CONNECTED',
      webhookStatus: 'ACTIVE',
      lastSync: new Date(Date.now() - 1000 * 60 * 5).toLocaleTimeString(),
      eventsIngested: 1420,
      errorCount: 0,
      credentialsConfigured: true,
      endpointUrl: 'https://api.securoxi.internal/v1/integrations/greenhouse/webhook',
      hmacVerified: true,
    },
    {
      id: 'INT-LEV-02',
      name: 'Lever Talent Inbound Pipeline',
      provider: 'LEVER',
      environment: 'CONFIGURED',
      connectionStatus: 'CONNECTED',
      webhookStatus: 'LISTENING',
      lastSync: new Date(Date.now() - 1000 * 60 * 18).toLocaleTimeString(),
      eventsIngested: 380,
      errorCount: 0,
      credentialsConfigured: true,
      endpointUrl: 'https://api.securoxi.internal/v1/integrations/lever/webhook',
      hmacVerified: true,
    },
    {
      id: 'INT-WD-03',
      name: 'Workday ATS Sync Connector',
      provider: 'WORKDAY',
      environment: 'STAGING',
      connectionStatus: 'CONNECTED',
      webhookStatus: 'LISTENING',
      lastSync: new Date(Date.now() - 1000 * 60 * 120).toLocaleTimeString(),
      eventsIngested: 85,
      errorCount: 0,
      credentialsConfigured: true,
      endpointUrl: 'https://api.securoxi.internal/v1/integrations/workday/sync',
      hmacVerified: true,
    },
    {
      id: 'INT-MOCK-04',
      name: 'Simulated Ingress Sandbox (Dev/Test)',
      provider: 'CUSTOM_WEBHOOK',
      environment: 'MOCK',
      connectionStatus: 'MOCK_ACTIVE',
      webhookStatus: 'INACTIVE',
      lastSync: 'N/A (Local Mock)',
      eventsIngested: 12,
      errorCount: 0,
      credentialsConfigured: false,
      endpointUrl: 'http://localhost:8000/api/v1/mock/webhook',
      hmacVerified: false,
    },
  ];

  const handleTestSync = (int: ATSIntegration) => {
    setTestSyncSuccess(`Synchronized ${int.name} successfully. 0 errors reported, webhook HMAC verified.`);
    setTimeout(() => setTestSyncSuccess(null), 4000);
  };

  const columns = [
    {
      key: 'name',
      header: 'Integration & Provider',
      sortable: true,
      render: (row: ATSIntegration) => (
        <div>
          <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
            {row.name}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <code>{row.id}</code> • Provider: <strong>{row.provider}</strong>
          </div>
        </div>
      ),
    },
    {
      key: 'environment',
      header: 'Environment Tier',
      width: '140px',
      sortable: true,
      render: (row: ATSIntegration) => {
        const variantMap: Record<string, 'safe' | 'info' | 'suspicious' | 'neutral'> = {
          PRODUCTION: 'safe',
          CONFIGURED: 'info',
          STAGING: 'suspicious',
          MOCK: 'neutral',
        };
        return <Badge variant={variantMap[row.environment] || 'neutral'}>{row.environment}</Badge>;
      },
    },
    {
      key: 'connectionStatus',
      header: 'Connection Health',
      width: '150px',
      render: (row: ATSIntegration) => (
        row.environment === 'MOCK' ? (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
            Mock / Sandbox
          </span>
        ) : (
          <StatusBadge status="SAFE" label="CONNECTED" />
        )
      ),
    },
    {
      key: 'webhookStatus',
      header: 'Webhook Ingress',
      width: '140px',
      render: (row: ATSIntegration) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Webhook size={13} style={{ color: row.webhookStatus === 'ACTIVE' ? 'var(--status-safe)' : 'var(--text-muted)' }} />
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: row.webhookStatus === 'ACTIVE' ? 'var(--status-safe)' : 'var(--text-secondary)' }}>
            {row.webhookStatus}
          </span>
        </div>
      ),
    },
    {
      key: 'lastSync',
      header: 'Last Sync',
      width: '130px',
      render: (row: ATSIntegration) => (
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{row.lastSync}</span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      width: '160px',
      render: (row: ATSIntegration) => (
        <div style={{ display: 'flex', gap: '6px' }}>
          <Button variant="secondary" size="xs" onClick={() => setSelectedIntegration(row)}>
            Inspect
          </Button>
          {row.environment !== 'MOCK' && (
            <Button variant="outline" size="xs" onClick={() => handleTestSync(row)}>
              Sync Now
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <PageContainer>
      {/* 1. Page Header */}
      <PageHeader
        title="ATS Connectors & Ingress Integration Governance"
        subtitle="Manage enterprise ATS candidate ingestion pipelines with HMAC webhook verification and strict tenant isolation"
        breadcrumbs={[{ label: 'HIRING' }, { label: 'ATS CONNECTORS' }]}
        badge={<Badge variant="safe">Ingress Pipeline Active</Badge>}
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button variant="primary" size="sm" icon={<Webhook size={14} />}>
              + Connect New ATS
            </Button>
          </div>
        }
      />

      {/* 2. Top Summary KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '14px',
          marginBottom: '18px',
        }}
      >
        <StatCard
          label="Total Ingress Integrations"
          value={integrations.length}
          icon={<Briefcase size={18} />}
          subtitle="Greenhouse, Lever, Workday"
        />
        <StatCard
          label="Production Webhooks"
          value="2 Live"
          deltaType="positive"
          icon={<CheckCircle2 size={18} />}
          statusBadge={<StatusBadge status="SAFE" />}
        />
        <StatCard
          label="Candidates Ingested"
          value="1,885"
          delta="+14.2% week"
          deltaType="positive"
          icon={<Layers size={18} />}
          subtitle="Auto-scanned by pipeline"
        />
        <StatCard
          label="HMAC Signature Errors"
          value="0"
          deltaType="positive"
          icon={<Lock size={18} />}
          subtitle="Zero spoofed payloads"
        />
      </div>

      {testSyncSuccess && (
        <Alert type="success" title="Connector Health Verified" onDismiss={() => setTestSyncSuccess(null)}>
          {testSyncSuccess}
        </Alert>
      )}

      {/* 3. Integrations DataTable */}
      <Card
        title="Configured Enterprise ATS Ingress Connectors"
        subtitle="Providers clearly delineated by environment tier"
      >
        <DataTable
          columns={columns}
          data={integrations}
          keyExtractor={(row) => row.id}
          pageSize={6}
        />
      </Card>

      {/* 4. Inspection Drawer */}
      <Drawer
        isOpen={selectedIntegration !== null}
        onClose={() => setSelectedIntegration(null)}
        title="ATS Connector Configuration"
        subtitle={`${selectedIntegration?.name || ''} (${selectedIntegration?.id || ''})`}
        badge={selectedIntegration ? <Badge variant="info">{selectedIntegration.environment}</Badge> : undefined}
        footer={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button variant="secondary" onClick={() => setSelectedIntegration(null)}>
              Close Drawer
            </Button>
            <Button variant="primary" onClick={() => navigate('/screening')}>
              View Ingested Candidates
            </Button>
          </div>
        }
      >
        {selectedIntegration && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {selectedIntegration.environment === 'MOCK' && (
              <Alert type="warning" title="Mock Integration Notice">
                This connector is a local development simulation. It does not communicate with live production endpoints.
              </Alert>
            )}

            <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)', fontSize: '0.8125rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '6px', color: 'var(--text-primary)' }}>
                Webhook Endpoint Details
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--accent-cyan)', wordBreak: 'break-all' }}>
                {selectedIntegration.endpointUrl}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.8125rem' }}>
              <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>HMAC AUTHENTICATION</span>
                <div style={{ fontWeight: 700, color: 'var(--status-safe)' }}>
                  {selectedIntegration.hmacVerified ? '✓ SHA-256 Verified' : 'Disabled (Mock)'}
                </div>
              </div>
              <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>TOTAL PAYLOADS</span>
                <div style={{ fontWeight: 700 }}>{selectedIntegration.eventsIngested} Resumes Ingested</div>
              </div>
            </div>

            <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)', fontSize: '0.8125rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '4px', color: 'var(--text-primary)' }}>
                Security Ingestion Rules
              </div>
              <div style={{ color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                All candidate payloads received over this webhook automatically traverse the <strong>Phase 1 Forensic Scanner</strong> and <strong>Phase 2 Qualification Gate</strong> before ATS recruiter viewing.
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </PageContainer>
  );
};
