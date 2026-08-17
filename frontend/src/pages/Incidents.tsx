import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Incident, ScanReport } from '../api/types';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { VerdictBadge } from '../components/ui/Badge';
import { LoadingState, EmptyState, ErrorState } from '../components/ui/States';

export const IncidentsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [scans, setScans] = useState<ScanReport[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>('technique');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
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
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch security incidents.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return <LoadingState message="Fetching active security incidents & evidence traces..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  // Apply Filters
  const filteredIncidents = incidents.filter((inc) => {
    const matchSev = severityFilter === 'ALL' || inc.severity.toUpperCase() === severityFilter;
    const matchStatus = statusFilter === 'ALL' || inc.status.toUpperCase() === statusFilter;
    return matchSev && matchStatus;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span>🚨</span>
          <span>Threat Investigation & Incident Response Workspace</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Deep SOC forensic investigation, node-edge attack graph exploration, and evidence verification.
        </p>
      </div>

      {/* Filters Bar */}
      <Card>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-app)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 12px',
                fontSize: '0.8125rem',
              }}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-app)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 12px',
                fontSize: '0.8125rem',
              }}
            >
              <option value="ALL">All Statuses</option>
              <option value="DETECTED">Detected</option>
              <option value="INVESTIGATING">Investigating</option>
              <option value="RESPONDED">Responded</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Split Investigation Workspace */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        {/* Incident List */}
        <Card title="Incidents Queue" subtitle={`${filteredIncidents.length} incidents match filters`}>
          {filteredIncidents.length === 0 ? (
            <EmptyState title="No Matching Incidents" description="No security incidents match the current severity and status filters." />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '520px', overflowY: 'auto' }}>
              {filteredIncidents.map((inc) => (
                <div
                  key={inc.incident_id}
                  onClick={() => setSelectedIncident(inc)}
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
                    <VerdictBadge verdict={inc.severity === 'CRITICAL' ? 'CRITICAL' : 'HIGH_RISK'} />
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: {inc.incident_id} • Score: {inc.risk_score}/100</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Asset: {inc.affected_asset}</div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Incident Detail Inspector */}
        <div>
          {selectedIncident ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Header Info */}
              <Card title={`Incident: ${selectedIncident.incident_id}`} subtitle={`Target: ${selectedIncident.affected_asset}`}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ATTACK TYPE</div>
                    <div style={{ fontWeight: 700, color: 'var(--status-highrisk)' }}>{selectedIncident.attack_type}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SEVERITY</div>
                    <div style={{ fontWeight: 700 }}>{selectedIncident.severity}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>RISK SCORE</div>
                    <div style={{ fontWeight: 800, color: 'var(--status-highrisk)' }}>{selectedIncident.risk_score} / 100</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>STATUS</div>
                    <div style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{selectedIncident.status}</div>
                  </div>
                </div>
              </Card>

              {/* Interactive Attack Graph */}
              <Card title="Interactive Attack Graph" subtitle="Click nodes to inspect relationship metadata">
                <div style={{ background: '#040711', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-lg)', padding: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
                    <button
                      onClick={() => setSelectedNode('actor')}
                      style={{
                        padding: '12px',
                        background: selectedNode === 'actor' ? 'var(--accent-indigo)' : 'var(--bg-surface-elevated)',
                        color: '#FFF',
                        border: '1px solid var(--border-default)',
                        borderRadius: '8px',
                        cursor: 'pointer',
                      }}
                    >
                      👤 Actor ({selectedIncident.source})
                    </button>

                    <div style={{ color: 'var(--accent-cyan)' }}>──▶</div>

                    <button
                      onClick={() => setSelectedNode('artifact')}
                      style={{
                        padding: '12px',
                        background: selectedNode === 'artifact' ? 'var(--accent-indigo)' : 'var(--bg-surface-elevated)',
                        color: '#FFF',
                        border: '1px solid var(--border-default)',
                        borderRadius: '8px',
                        cursor: 'pointer',
                      }}
                    >
                      📄 Payload ({selectedIncident.affected_asset})
                    </button>

                    <div style={{ color: 'var(--status-highrisk)' }}>──▶</div>

                    <button
                      onClick={() => setSelectedNode('technique')}
                      style={{
                        padding: '12px',
                        background: selectedNode === 'technique' ? 'var(--status-highrisk)' : 'var(--bg-surface-elevated)',
                        color: '#FFF',
                        border: '1px solid var(--border-default)',
                        borderRadius: '8px',
                        cursor: 'pointer',
                      }}
                    >
                      ⚡ Technique ({selectedIncident.attack_type})
                    </button>
                  </div>

                  {/* Selected Node Metadata */}
                  <div style={{ marginTop: '20px', padding: '12px', background: 'var(--bg-surface)', borderRadius: '6px', fontSize: '0.8125rem' }}>
                    <strong>Selected Node Inspection ({selectedNode?.toUpperCase()}):</strong>
                    <div style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
                      {selectedNode === 'actor' && `Source Client: ${selectedIncident.source} • Ingress Interface: HTTP REST API`}
                      {selectedNode === 'artifact' && `Target File: ${selectedIncident.affected_asset} • Type: PDF Document Payload`}
                      {selectedNode === 'technique' && `Vector: ${selectedIncident.attack_type} • Risk Level: ${selectedIncident.risk_score} (HIGH)`}
                    </div>
                  </div>
                </div>
              </Card>

              {/* Evidence Viewer */}
              <Card title="Forensic Evidence Viewer" subtitle="Exact matched patterns & detector findings">
                <pre className="security-evidence">
{`[FORENSIC EVIDENCE DETAILS]
Incident ID: ${selectedIncident.incident_id}
Asset: ${selectedIncident.affected_asset}
Detector: SecuroxiBrainEngine (Rule: ${selectedIncident.policy_decision?.rule_name || 'RULE-100-HIGH-RISK-BLOCK'})
Matched Evidence: ${selectedIncident.evidence}
Response Enforced: ${selectedIncident.response_actions.join(', ')}`}
                </pre>
              </Card>

              {/* Investigation Timeline */}
              <Card title="Incident Investigation Timeline" subtitle="Lifecycle timestamps & policy responses">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ fontSize: '0.8125rem' }}>
                    <span style={{ color: 'var(--status-highrisk)', fontWeight: 700 }}>[DETECTED]</span> Threat signal intercepted by Security Brain.
                  </div>
                  <div style={{ fontSize: '0.8125rem' }}>
                    <span style={{ color: 'var(--status-suspicious)', fontWeight: 700 }}>[TRIAGED]</span> Risk score evaluated at {selectedIncident.risk_score}/100.
                  </div>
                  <div style={{ fontSize: '0.8125rem' }}>
                    <span style={{ color: 'var(--status-safe)', fontWeight: 700 }}>[RESPONDED]</span> Enforced policy actions: {selectedIncident.response_actions.join(', ')}.
                  </div>
                </div>
              </Card>
            </div>
          ) : (
            <Card>
              <EmptyState title="Select an Incident" description="Select an incident from the queue on the left to start forensic investigation." />
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
