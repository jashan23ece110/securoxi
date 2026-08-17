import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge, VerdictBadge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { LoadingState, EmptyState, ErrorState } from '../components/ui/States';

export const DesignSystemShowcase: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'components' | 'states'>('components');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '4px' }}>SECUROXI Design System Showcase</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Foundational enterprise security component tokens, status indicators, and UI primitives.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
        <Button variant={activeTab === 'components' ? 'primary' : 'secondary'} onClick={() => setActiveTab('components')}>
          UI Primitives & Badges
        </Button>
        <Button variant={activeTab === 'states' ? 'primary' : 'secondary'} onClick={() => setActiveTab('states')}>
          Component States & Alerts
        </Button>
      </div>

      {activeTab === 'components' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Security Status Badges */}
          <Card title="Security Status & Verdict Badges" subtitle="Standardized security classification tokens">
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
              <VerdictBadge verdict="SAFE" />
              <VerdictBadge verdict="SUSPICIOUS" />
              <VerdictBadge verdict="HIGH_RISK" />
              <VerdictBadge verdict="CRITICAL" />
              <VerdictBadge verdict="BLOCKED" />
              <Badge variant="info">PROCESSING</Badge>
              <Badge variant="info">REVIEW_REQUIRED</Badge>
            </div>
          </Card>

          {/* Buttons */}
          <Card title="Action Buttons" subtitle="Primary, secondary, danger, and stateful variants">
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
              <Button variant="primary">Primary Action</Button>
              <Button variant="secondary">Secondary Action</Button>
              <Button variant="danger">High-Impact Block</Button>
              <Button variant="secondary" isLoading>
                Processing...
              </Button>
              <Button variant="secondary" disabled>
                Disabled Action
              </Button>
            </div>
          </Card>

          {/* Security Evidence Block */}
          <Card title="Security Evidence & Code Display" subtitle="Monospaced technical inspection output">
            <pre className="security-evidence">
{`[SECUROXI RUNTIME SECURITY INSPECTION]
Boundary: INPUT | Source: UNTRUSTED_RESUME
Threat Classification: PROMPT_INJECTION
Pattern Matched: r"ignore\\s+(all\\s+)?(previous\\s+)?instructions"
Risk Score: 95.0 / 100.0
Policy Decision: BLOCK (Policy Rule: RULE-090-PROMPT-INJECTION-QUARANTINE)`}
            </pre>
          </Card>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Alerts */}
          <Card title="System Alerts" subtitle="Severity-graded operational notifications">
            <Alert type="info" title="System Notice">
              Continuous monitoring active across 3 connected ATS webhooks.
            </Alert>
            <Alert type="success" title="Policy Authorization Succeeded">
              Automated quarantine successfully enforced for Scan ID SCAN-99201.
            </Alert>
            <Alert type="warning" title="SSRF Interception Warning">
              Outbound fetch to private subnet 169.254.169.254 was blocked by SecuroxiSSRFGuard.
            </Alert>
            <Alert type="danger" title="Emergency Threat Blocked">
              Direct prompt injection attempt detected inside untrusted resume payload.
            </Alert>
          </Card>

          {/* States */}
          <Card title="Component States Showcase" subtitle="Loading, Empty, and Error UI primitives">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
              <LoadingState message="Scanning resume payload..." />
              <EmptyState title="No Active Incidents" description="All system security metrics within normal baseline limits." />
              <ErrorState message="Connection timeout to PostgreSQL audit database." onRetry={() => alert('Retrying...')} />
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
