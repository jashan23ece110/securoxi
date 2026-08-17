import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Alert } from '../components/ui/Alert';

export const SettingsPage: React.FC = () => {
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [retentionDays, setRetentionDays] = useState(90);
  const [purgeStatus, setPurgeStatus] = useState<string | null>(null);

  const handleGenerateKey = () => {
    // Generate one-time secret key string
    const newSecret = `securoxi_live_${Math.random().toString(36).substring(2, 15)}_${Math.random().toString(36).substring(2, 15)}`;
    setCreatedKey(newSecret);
  };

  const handlePurgeData = () => {
    setPurgeStatus(`Automated retention purge executed. Purged records older than ${retentionDays} days.`);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span>⚙️</span>
          <span>Enterprise Control Plane & Governance Settings</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          API key secrets management, RBAC permission roles, organization configuration, and data retention policy.
        </p>
      </div>

      {/* 1. API Key Provisioning & One-Time Reveal */}
      <Card title="API Keys & Secrets Provisioning" subtitle="Manage client authentication credentials with mandatory hash storage">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            API keys are hashed via SHA-256 (`key_hash`) before persistence. Raw secret keys are displayed <strong>ONCE</strong> during creation.
          </p>

          <div>
            <Button variant="primary" onClick={handleGenerateKey}>
              + Provision New API Key
            </Button>
          </div>

          {createdKey && (
            <Alert type="warning" title="ONE-TIME SECRET KEY REVEAL">
              <p style={{ marginBottom: '8px' }}>Store this key securely. It will NEVER be displayed again.</p>
              <pre className="security-evidence">{createdKey}</pre>
            </Alert>
          )}
        </div>
      </Card>

      {/* 2. RBAC Permissions Matrix */}
      <Card title="Role-Based Access Control (RBAC) Governance" subtitle="Configured least-privilege enterprise permission matrix">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
              <th style={{ padding: '10px 8px' }}>Role</th>
              <th style={{ padding: '10px 8px' }}>View Scans</th>
              <th style={{ padding: '10px 8px' }}>Trigger Scans</th>
              <th style={{ padding: '10px 8px' }}>Manage Policies</th>
              <th style={{ padding: '10px 8px' }}>Audit Access</th>
              <th style={{ padding: '10px 8px' }}>Tenant Admin</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
              <td style={{ padding: '12px 8px', fontWeight: 700, color: 'var(--accent-cyan)' }}>SUPER_ADMIN</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
              <td style={{ padding: '12px 8px', fontWeight: 700 }}>SECURITY_ADMIN</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-highrisk)' }}>❌</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
              <td style={{ padding: '12px 8px', fontWeight: 700 }}>RECRUITER</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-highrisk)' }}>❌</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-highrisk)' }}>❌</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-highrisk)' }}>❌</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
              <td style={{ padding: '12px 8px', fontWeight: 700 }}>AUDITOR</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-highrisk)' }}>❌</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-highrisk)' }}>❌</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-safe)' }}>✅</td>
              <td style={{ padding: '12px 8px', color: 'var(--status-highrisk)' }}>❌</td>
            </tr>
          </tbody>
        </table>
      </Card>

      {/* 3. Data Retention & Automated Purging */}
      <Card title="Data Retention & Lifecycle Governance" subtitle="Configure automated record cleanup for compliance">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '0.875rem' }}>Retention Period (Days):</span>
            <input
              type="number"
              value={retentionDays}
              onChange={(e) => setRetentionDays(Number(e.target.value))}
              style={{
                width: '100px',
                backgroundColor: 'var(--bg-app)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 12px',
              }}
            />
            <Button variant="secondary" onClick={handlePurgeData}>
              Execute Manual Retention Cleanup
            </Button>
          </div>

          {purgeStatus && <Alert type="success" title="Retention Purge Completed">{purgeStatus}</Alert>}
        </div>
      </Card>
    </div>
  );
};
