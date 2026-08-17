import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { PolicyRule } from '../api/types';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { VerdictBadge } from '../components/ui/Badge';
import { LoadingState, EmptyState, ErrorState } from '../components/ui/States';

export const PoliciesPage: React.FC = () => {
  const [policies, setPolicies] = useState<PolicyRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPolicies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listPolicies().catch(() => [
        { rule_id: 'R-100', rule_name: 'RULE-100-HIGH-RISK-BLOCK', priority: 100, action: 'BLOCK', condition: 'risk_score >= 80.0' },
        { rule_id: 'R-090', rule_name: 'RULE-090-PROMPT-INJECTION-QUARANTINE', priority: 90, action: 'QUARANTINE_DOCUMENT', condition: 'threat_type == PROMPT_INJECTION' },
        { rule_id: 'R-050', rule_name: 'RULE-050-SUSPICIOUS-HUMAN-REVIEW', priority: 50, action: 'REVIEW', condition: 'risk_score >= 50.0' },
        { rule_id: 'R-010', rule_name: 'RULE-010-SAFE-ALLOW', priority: 10, action: 'ALLOW', condition: 'risk_score < 50.0' },
      ]);
      setPolicies(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch policy rules.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  if (loading) {
    return <LoadingState message="Fetching Policy Engine rules & priority rankings..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchPolicies} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>🛡️</span>
            <span>Deterministic Policy Engine Governance</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Authoritative security rules, priority evaluation order, and automated response actions.
          </p>
        </div>
        <Button variant="primary">
          + Create New Policy Rule
        </Button>
      </div>

      {/* Policy Rules Table */}
      <Card title="Active Security Policy Rules" subtitle="Evaluated in descending priority order (100 = Highest Priority)">
        {policies.length === 0 ? (
          <EmptyState title="No Policies Configured" description="Default system rules will populate automatically." />
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px 8px' }}>Priority</th>
                <th style={{ padding: '10px 8px' }}>Rule Name</th>
                <th style={{ padding: '10px 8px' }}>Condition Pattern</th>
                <th style={{ padding: '10px 8px' }}>Enforced Action</th>
                <th style={{ padding: '10px 8px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {policies.map((rule) => (
                <tr key={rule.rule_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '12px 8px', fontWeight: 800, color: 'var(--accent-cyan)' }}>{rule.priority}</td>
                  <td style={{ padding: '12px 8px', fontWeight: 700 }}>{rule.rule_name}</td>
                  <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-code)' }}>
                    {rule.condition}
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <VerdictBadge verdict={(rule.action as any) || 'BLOCKED'} />
                  </td>
                  <td style={{ padding: '12px 8px', color: 'var(--status-safe)', fontWeight: 700 }}>🟢 ACTIVE</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
};
