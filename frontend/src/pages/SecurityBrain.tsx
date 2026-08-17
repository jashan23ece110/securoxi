import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Incident, ScanReport } from '../api/types';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { VerdictBadge } from '../components/ui/Badge';
import { LoadingState, EmptyState, ErrorState } from '../components/ui/States';

export const SecurityBrainPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [scans, setScans] = useState<ScanReport[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [selectedScan, setSelectedScan] = useState<ScanReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [incRes, scansRes] = await Promise.all([
        api.listIncidents().catch(() => []),
        api.listScans().catch(() => []),
      ]);

      setIncidents(incRes);
      setScans(scansRes);
      if (incRes.length > 0) {
        setSelectedIncident(incRes[0]);
      } else if (scansRes.length > 0) {
        setSelectedScan(scansRes[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to connect to Security Brain API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return <LoadingState message="Loading Security Brain reasoning telemetry & attack graphs..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span>🧠</span>
          <span>Security Brain Investigation Workspace</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Correlation pipeline, attack graph visualization, AI reasoning vs. deterministic policy authority.
        </p>
      </div>

      {/* Security Pipeline Stages Bar */}
      <Card>
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '12px' }}>
          SECURITY BRAIN CORRELATION PIPELINE
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap', fontSize: '0.75rem', fontWeight: 700 }}>
          <div style={{ padding: '6px 12px', background: 'var(--bg-surface-elevated)', borderRadius: '6px', color: 'var(--accent-cyan)' }}>1. SIGNAL</div>
          <span>→</span>
          <div style={{ padding: '6px 12px', background: 'var(--bg-surface-elevated)', borderRadius: '6px', color: 'var(--accent-cyan)' }}>2. FORENSICS</div>
          <span>→</span>
          <div style={{ padding: '6px 12px', background: 'var(--bg-surface-elevated)', borderRadius: '6px', color: 'var(--accent-cyan)' }}>3. DETECTION</div>
          <span>→</span>
          <div style={{ padding: '6px 12px', background: 'var(--bg-surface-elevated)', borderRadius: '6px', color: 'var(--accent-cyan)' }}>4. ATTACK GRAPH</div>
          <span>→</span>
          <div style={{ padding: '6px 12px', background: 'var(--bg-surface-elevated)', borderRadius: '6px', color: 'var(--status-suspicious)' }}>5. AI REASONING</div>
          <span>→</span>
          <div style={{ padding: '6px 12px', background: 'var(--bg-surface-elevated)', borderRadius: '6px', color: 'var(--status-highrisk)' }}>6. POLICY DECISION</div>
          <span>→</span>
          <div style={{ padding: '6px 12px', background: 'var(--bg-surface-elevated)', borderRadius: '6px', color: 'var(--status-safe)' }}>7. ACTION & AUDIT</div>
        </div>
      </Card>

      {/* Main Investigation Split View */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        {/* Event / Incident Selector List */}
        <Card title="Correlated Incidents & Events" subtitle="Select security finding to inspect graph & evidence">
          {incidents.length === 0 && scans.length === 0 ? (
            <EmptyState title="No Security Brain Telemetry" description="Run a document scan to generate Security Brain telemetry." />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '480px', overflowY: 'auto' }}>
              {incidents.map((inc) => (
                <div
                  key={inc.incident_id}
                  onClick={() => {
                    setSelectedIncident(inc);
                    setSelectedScan(null);
                  }}
                  style={{
                    padding: '12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: selectedIncident?.incident_id === inc.incident_id ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                    border: selectedIncident?.incident_id === inc.incident_id ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>{inc.attack_type}</span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--status-highrisk)' }}>Risk {inc.risk_score}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Asset: {inc.affected_asset}</div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Selected Incident Telemetry & Graph Representation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {selectedIncident ? (
            <>
              {/* Attack Graph Node Representation */}
              <Card title="Threat Attack Graph" subtitle="Inferred threat actor, artifact, signal, technique, and target relationships">
                <div style={{ background: '#040711', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-lg)', padding: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', textAlign: 'center' }}>
                    {/* Node 1: Actor */}
                    <div style={{ padding: '12px', background: 'var(--bg-surface-elevated)', borderRadius: '8px', border: '1px solid var(--border-default)' }}>
                      <div style={{ fontSize: '20px' }}>👤</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>UNTRUSTED SENDER</div>
                      <div style={{ fontSize: '0.8125rem', fontWeight: 600 }}>{selectedIncident.source}</div>
                    </div>

                    <div style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>──(Submits Payload)──▶</div>

                    {/* Node 2: Artifact */}
                    <div style={{ padding: '12px', background: 'var(--bg-surface-elevated)', borderRadius: '8px', border: '1px solid var(--accent-cyan)' }}>
                      <div style={{ fontSize: '20px' }}>📄</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>ARTIFACT</div>
                      <div style={{ fontSize: '0.8125rem', fontWeight: 600 }}>{selectedIncident.affected_asset}</div>
                    </div>

                    <div style={{ color: 'var(--status-highrisk)', fontWeight: 700 }}>──(Triggers Technique)──▶</div>

                    {/* Node 3: Technique */}
                    <div style={{ padding: '12px', background: 'var(--bg-surface-elevated)', borderRadius: '8px', border: '1px solid var(--status-highrisk)' }}>
                      <div style={{ fontSize: '20px' }}>⚡</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--status-highrisk)' }}>TECHNIQUE</div>
                      <div style={{ fontSize: '0.8125rem', fontWeight: 600 }}>{selectedIncident.attack_type}</div>
                    </div>
                  </div>
                </div>
              </Card>

              {/* AI Reasoning vs. Policy Authority Distinction */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <Card title="AI Advisory Reasoning" subtitle="LLM model recommendation (Non-Authoritative)">
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', padding: '12px', background: 'var(--bg-app)', borderRadius: '6px' }}>
                    {selectedIncident.evidence || 'LLM recommendation logged as advisory note.'}
                  </div>
                </Card>

                <Card title="Deterministic Policy Engine" subtitle="Authoritative decision rule (Enforced)">
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: 700 }}>Enforced Action:</span>
                      <VerdictBadge verdict={(selectedIncident.policy_decision?.action as any) || 'BLOCKED'} />
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Policy Rule: {selectedIncident.policy_decision?.rule_name || 'RULE-100-HIGH-RISK-BLOCK'}
                    </div>
                  </div>
                </Card>
              </div>

              {/* Security Evidence Box */}
              <Card title="Forensic Evidence Traceability" subtitle="Matched pattern strings & evidence snippets">
                <pre className="security-evidence">
{`[INCIDENT FORENSIC TRACE]
ID: ${selectedIncident.incident_id}
Asset: ${selectedIncident.affected_asset}
Severity: ${selectedIncident.severity}
Risk Score: ${selectedIncident.risk_score} / 100.0
Evidence Snippet: ${selectedIncident.evidence}
Response Actions Enforced: ${selectedIncident.response_actions.join(', ')}`}
                </pre>
              </Card>
            </>
          ) : (
            <Card>
              <EmptyState title="Select an Event" description="Click any correlated incident or scan on the left to view threat attack graphs." />
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
