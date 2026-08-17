import React, { useState } from 'react';
import {
  Card,
  StatCard,
  Button,
  StatusBadge,
  Badge,
  DataTable,
  Tabs,
  Alert,
  Input,
  Toggle,
} from '../components/ui';
import { PageHeader, PageToolbar, PageContainer } from '../components/layout';
import {
  Settings,
  Key,
  Users,
  Shield,
  Clock,
  Lock,
  Copy,
  Check,
  Building,
  Radio,
  Sliders,
  Webhook,
  AlertTriangle,
} from 'lucide-react';

interface APIKeyItem {
  id: string;
  name: string;
  keyPrefix: string;
  created: string;
  lastUsed: string;
  scopes: string[];
  status: 'ACTIVE' | 'REVOKED';
}

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'org' | 'rbac' | 'apikeys' | 'retention' | 'security'>('apikeys');
  const [createdSecretKey, setCreatedSecretKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [retentionDays, setRetentionDays] = useState(90);
  const [purgeStatus, setPurgeStatus] = useState<string | null>(null);

  // Security Toggles
  const [ssrfGuardActive, setSsrfGuardActive] = useState(true);
  const [strictTenantIsolation, setStrictTenantIsolation] = useState(true);
  const [ocrSandboxActive, setOcrSandboxActive] = useState(true);
  const [siemExportActive, setSiemExportActive] = useState(true);

  const [apiKeys, setApiKeys] = useState<APIKeyItem[]>([
    {
      id: 'KEY-01',
      name: 'Production Ingestion Gateway Key',
      keyPrefix: 'securoxi_live_8f3a...',
      created: '2026-08-01',
      lastUsed: '2 minutes ago',
      scopes: ['scans:write', 'scans:read', 'brain:read'],
      status: 'ACTIVE',
    },
    {
      id: 'KEY-02',
      name: 'Greenhouse Webhook Ingress Key',
      keyPrefix: 'securoxi_live_12c9...',
      created: '2026-08-10',
      lastUsed: '18 minutes ago',
      scopes: ['integrations:ats', 'screening:read'],
      status: 'ACTIVE',
    },
  ]);

  const handleGenerateKey = () => {
    if (!newKeyName) return;
    const rawSecret = `securoxi_live_${Math.random().toString(36).substring(2, 12)}_${Math.random().toString(36).substring(2, 12)}`;
    const newKey: APIKeyItem = {
      id: `KEY-0${apiKeys.length + 1}`,
      name: newKeyName,
      keyPrefix: `${rawSecret.substring(0, 18)}...`,
      created: new Date().toISOString().substring(0, 10),
      lastUsed: 'Never',
      scopes: ['scans:write', 'scans:read'],
      status: 'ACTIVE',
    };
    setApiKeys([newKey, ...apiKeys]);
    setCreatedSecretKey(rawSecret);
    setNewKeyName('');
  };

  const handleCopySecret = () => {
    if (!createdSecretKey) return;
    navigator.clipboard.writeText(createdSecretKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const handlePurgeData = () => {
    setPurgeStatus(`Automated retention purge executed. Successfully purged records older than ${retentionDays} days.`);
    setTimeout(() => setPurgeStatus(null), 5000);
  };

  const apiKeyColumns = [
    {
      key: 'name',
      header: 'API Key Name',
      sortable: true,
      render: (row: APIKeyItem) => (
        <div>
          <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.875rem' }}>{row.name}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: <code>{row.id}</code></div>
        </div>
      ),
    },
    {
      key: 'keyPrefix',
      header: 'Key Token',
      render: (row: APIKeyItem) => (
        <code style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>{row.keyPrefix}</code>
      ),
    },
    {
      key: 'scopes',
      header: 'Assigned Scopes',
      render: (row: APIKeyItem) => (
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {row.scopes.map((sc) => (
            <Badge key={sc} variant="neutral">{sc}</Badge>
          ))}
        </div>
      ),
    },
    {
      key: 'lastUsed',
      header: 'Last Used',
      render: (row: APIKeyItem) => (
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{row.lastUsed}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      width: '100px',
      render: (row: APIKeyItem) => (
        <StatusBadge status={row.status === 'ACTIVE' ? 'SAFE' : 'FAILED'} label={row.status} />
      ),
    },
  ];

  return (
    <PageContainer>
      {/* 1. Page Header */}
      <PageHeader
        title="Enterprise Control Plane & Security Governance"
        subtitle="API key secrets provisioning, RBAC matrix, organization tenant profile, and automated data retention"
        breadcrumbs={[{ label: 'GOVERNANCE' }, { label: 'SETTINGS' }]}
        badge={<Badge variant="safe">Control Plane Enforcing</Badge>}
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
          label="Tenant Organization"
          value="Securoxi Defense"
          icon={<Building size={18} />}
          subtitle="ID: TENANT-DEFAULT"
        />
        <StatCard
          label="Provisioned API Keys"
          value={apiKeys.length}
          icon={<Key size={18} />}
          subtitle="SHA-256 Hashed Secrets"
        />
        <StatCard
          label="RBAC Roles Defined"
          value="4 Roles"
          deltaType="positive"
          icon={<Users size={18} />}
          subtitle="Least-Privilege Enforced"
        />
        <StatCard
          label="Isolation Boundary"
          value="PostgreSQL RLS"
          icon={<Lock size={18} />}
          subtitle="IDOR Guard Active"
          statusBadge={<StatusBadge status="SAFE" />}
        />
      </div>

      {/* 3. Navigation Tabs */}
      <Card style={{ marginBottom: '18px' }}>
        <Tabs
          activeTab={activeTab}
          onChange={(t) => setActiveTab(t as any)}
          tabs={[
            { id: 'apikeys', label: '1. API Keys & Authentication' },
            { id: 'rbac', label: '2. RBAC Permissions Matrix' },
            { id: 'security', label: '3. Security Controls & SSRF' },
            { id: 'retention', label: '4. Data Retention & Privacy' },
            { id: 'org', label: '5. Tenant Organization' },
          ]}
        />
      </Card>

      {/* 4. Tab 1: API Keys Management */}
      {activeTab === 'apikeys' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Card
            title="Provision Client API Key"
            subtitle="API keys are SHA-256 hashed before persistence. Raw keys are displayed ONCE upon generation."
          >
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                type="text"
                placeholder="Key Description (e.g. ATS Ingress Webhook Key)"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                style={{
                  flex: 1,
                  minWidth: '280px',
                  backgroundColor: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '8px 12px',
                  fontSize: '0.8125rem',
                  outline: 'none',
                }}
              />
              <Button variant="primary" onClick={handleGenerateKey} icon={<Key size={13} />}>
                + Generate Secret Key
              </Button>
            </div>

            {createdSecretKey && (
              <div style={{ marginTop: '16px' }}>
                <Alert type="warning" title="ONE-TIME SECRET KEY REVEAL">
                  <p style={{ marginBottom: '8px', fontSize: '0.8125rem' }}>
                    Copy and store this secret key in your vault now. It will <strong>NEVER</strong> be displayed again.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#040711', padding: '10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)' }}>
                    <code style={{ flex: 1, color: 'var(--status-suspicious)', fontSize: '0.8125rem', wordBreak: 'break-all' }}>
                      {createdSecretKey}
                    </code>
                    <Button variant="secondary" size="xs" onClick={handleCopySecret} icon={copied ? <Check size={12} /> : <Copy size={12} />}>
                      {copied ? 'Copied!' : 'Copy'}
                    </Button>
                  </div>
                </Alert>
              </div>
            )}
          </Card>

          <Card title="Active Client Authentication Keys" subtitle="Authenticated client tokens configured for this tenant">
            <DataTable
              columns={apiKeyColumns}
              data={apiKeys}
              keyExtractor={(row) => row.id}
              pageSize={6}
            />
          </Card>
        </div>
      )}

      {/* 5. Tab 2: RBAC Matrix */}
      {activeTab === 'rbac' && (
        <Card title="Role-Based Access Control (RBAC) Matrix" subtitle="Enforced least-privilege matrix validated on all API requests">
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px 8px' }}>Role</th>
                  <th style={{ padding: '10px 8px' }}>View Scans</th>
                  <th style={{ padding: '10px 8px' }}>Execute Scans</th>
                  <th style={{ padding: '10px 8px' }}>Manage Policies</th>
                  <th style={{ padding: '10px 8px' }}>Audit Trail</th>
                  <th style={{ padding: '10px 8px' }}>Tenant Admin</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { role: 'SUPER_ADMIN', scans: '✓', exec: '✓', pol: '✓', audit: '✓', admin: '✓', color: 'var(--accent-cyan)' },
                  { role: 'SECURITY_ADMIN', scans: '✓', exec: '✓', pol: '✓', audit: '✓', admin: '✕', color: 'var(--text-primary)' },
                  { role: 'RECRUITER', scans: '✓', exec: '✓', pol: '✕', audit: '✕', admin: '✕', color: 'var(--text-primary)' },
                  { role: 'AUDITOR', scans: '✓', exec: '✕', pol: '✕', audit: '✓', admin: '✕', color: 'var(--text-primary)' },
                ].map((r) => (
                  <tr key={r.role} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '12px 8px', fontWeight: 700, color: r.color }}>{r.role}</td>
                    <td style={{ padding: '12px 8px', color: r.scans === '✓' ? 'var(--status-safe)' : 'var(--status-highrisk)' }}>{r.scans}</td>
                    <td style={{ padding: '12px 8px', color: r.exec === '✓' ? 'var(--status-safe)' : 'var(--status-highrisk)' }}>{r.exec}</td>
                    <td style={{ padding: '12px 8px', color: r.pol === '✓' ? 'var(--status-safe)' : 'var(--status-highrisk)' }}>{r.pol}</td>
                    <td style={{ padding: '12px 8px', color: r.audit === '✓' ? 'var(--status-safe)' : 'var(--status-highrisk)' }}>{r.audit}</td>
                    <td style={{ padding: '12px 8px', color: r.admin === '✓' ? 'var(--status-safe)' : 'var(--status-highrisk)' }}>{r.admin}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* 6. Tab 3: Security Controls & SSRF */}
      {activeTab === 'security' && (
        <Card title="Security Controls & Guardrails" subtitle="Deterministic runtime defenses and outbound network protections">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.875rem' }}>SSRF Outbound Guard & Webhook Sandbox</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Blocks all egress to private IP spaces (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.1, 169.254.169.254).
                </div>
              </div>
              <Toggle checked={ssrfGuardActive} onChange={setSsrfGuardActive} label="SSRF Guard" />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.875rem' }}>Strict PostgreSQL Tenant Isolation</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Enforces mandatory <code>WHERE tenant_id = ?</code> filters across all SQL & pgvector similarity queries.
                </div>
              </div>
              <Toggle checked={strictTenantIsolation} onChange={setStrictTenantIsolation} label="Tenant Isolation" />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.875rem' }}>OCR Image-Quarantine Pipeline</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Automatically routes rasterized image-only PDFs to isolated OCR sandbox.
                </div>
              </div>
              <Toggle checked={ocrSandboxActive} onChange={setOcrSandboxActive} label="OCR Quarantine" />
            </div>
          </div>
        </Card>
      )}

      {/* 7. Tab 4: Retention */}
      {activeTab === 'retention' && (
        <Card title="Data Retention & Lifecycle Governance" subtitle="Configure automated record cleanup for GDPR/CCPA compliance">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>Scan Retention Period (Days):</span>
              <input
                type="number"
                value={retentionDays}
                onChange={(e) => setRetentionDays(Number(e.target.value))}
                style={{
                  width: '100px',
                  backgroundColor: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '6px 12px',
                  outline: 'none',
                }}
              />
              <Button variant="secondary" onClick={handlePurgeData}>
                Execute Retention Purge
              </Button>
            </div>

            {purgeStatus && (
              <Alert type="success" title="Retention Purge Executed" onDismiss={() => setPurgeStatus(null)}>
                {purgeStatus}
              </Alert>
            )}
          </div>
        </Card>
      )}

      {/* 8. Tab 5: Org Profile */}
      {activeTab === 'org' && (
        <Card title="Tenant Organization Profile" subtitle="Multi-tenant cluster context">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', fontSize: '0.8125rem' }}>
            <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>ORGANIZATION NAME</span>
              <div style={{ fontWeight: 700, fontSize: '0.9375rem' }}>Securoxi Enterprise Defense</div>
            </div>
            <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>TENANT IDENTIFIER</span>
              <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--accent-cyan)' }}>TENANT-DEFAULT</div>
            </div>
            <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>SERVICE PLAN</span>
              <div style={{ fontWeight: 700 }}>Enterprise Enterprise-Plus (Unlimited Scans)</div>
            </div>
            <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>DATABASE ISOLATION MODE</span>
              <div style={{ fontWeight: 700, color: 'var(--status-safe)' }}>Row-Level Security (RLS) Active</div>
            </div>
          </div>
        </Card>
      )}
    </PageContainer>
  );
};
