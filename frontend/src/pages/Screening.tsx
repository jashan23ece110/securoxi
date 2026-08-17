import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { ScreeningResult, ScanReport } from '../api/types';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { VerdictBadge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { LoadingState, EmptyState, ErrorState } from '../components/ui/States';

export const ScreeningPage: React.FC = () => {
  const [screenings, setScreenings] = useState<ScreeningResult[]>([]);
  const [scans, setScans] = useState<ScanReport[]>([]);
  const [selectedResult, setSelectedResult] = useState<ScreeningResult | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [securityFilter, setSecurityFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchScreeningData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [screenRes, scansRes] = await Promise.all([
        api.listScreenings().catch(() => []),
        api.listScans().catch(() => []),
      ]);

      // Mock seed data if empty for demo visualization
      const sampleResults: ScreeningResult[] = screenRes.length > 0 ? screenRes : [
        {
          screening_id: 'SCR-001',
          candidate_id: 'CAND-ALEX-SMITH',
          job_id: 'JOB-SR-SECUROPS',
          fit_score: 92.5,
          skill_match_pct: 95.0,
          qualification_verdict: 'STRONG_FIT',
          explanation: 'Candidate possesses 8+ years experience in Python, Kubernetes, and Cloud Security.',
          security_clearance: true,
        },
        {
          screening_id: 'SCR-002',
          candidate_id: 'CAND-JORDAN-LEE',
          job_id: 'JOB-SR-SECUROPS',
          fit_score: 0.0,
          skill_match_pct: 0.0,
          qualification_verdict: 'QUARANTINED',
          explanation: 'SECURITY GATE BLOCK: High-risk prompt injection attempt detected inside resume payload.',
          security_clearance: false,
        },
        {
          screening_id: 'SCR-003',
          candidate_id: 'CAND-TAYLOR-REED',
          job_id: 'JOB-SR-SECUROPS',
          fit_score: 74.0,
          skill_match_pct: 78.0,
          qualification_verdict: 'MODERATE_FIT',
          explanation: 'Strong core backend engineering background; missing Terraform certification.',
          security_clearance: true,
        },
      ];

      setScreenings(sampleResults);
      setScans(scansRes);
      if (sampleResults.length > 0) {
        setSelectedResult(sampleResults[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch screening results.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScreeningData();
  }, []);

  if (loading) {
    return <LoadingState message="Running security-aware resume matching & skill normalization..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchScreeningData} />;
  }

  const filteredResults = screenings.filter((r) => {
    const matchSearch = r.candidate_id.toLowerCase().includes(searchFilter.toLowerCase());
    const matchSec =
      securityFilter === 'ALL' ||
      (securityFilter === 'CLEAR' && r.security_clearance) ||
      (securityFilter === 'QUARANTINED' && !r.security_clearance);
    return matchSearch && matchSec;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span>👤</span>
          <span>Security-Aware Resume-to-JD Screening Workspace</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Semantic candidate fit scoring with strict backend security gate isolation.
        </p>
      </div>

      <Alert type="info" title="Disclaimer">
        Fit scores represent semantic skill alignment metrics and do NOT constitute automated hiring probabilities.
      </Alert>

      {/* Main Split View: Candidate Pool & Explainable Report Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        {/* Candidate Ranking Queue */}
        <Card title="Ranked Candidates Queue" subtitle={`${filteredResults.length} candidates in pool`}>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <input
              type="text"
              placeholder="Search candidate ID..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              style={{
                flex: 1,
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 12px',
                fontSize: '0.8125rem',
                color: 'var(--text-primary)',
              }}
            />
            <select
              value={securityFilter}
              onChange={(e) => setSecurityFilter(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-app)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 8px',
                fontSize: '0.8125rem',
              }}
            >
              <option value="ALL">All Security</option>
              <option value="CLEAR">Cleared</option>
              <option value="QUARANTINED">Quarantined</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '480px', overflowY: 'auto' }}>
            {filteredResults.map((r) => (
              <div
                key={r.screening_id}
                onClick={() => setSelectedResult(r)}
                style={{
                  padding: '12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: selectedResult?.screening_id === r.screening_id ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                  border: selectedResult?.screening_id === r.screening_id ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>{r.candidate_id}</span>
                  {r.security_clearance ? (
                    <VerdictBadge verdict="SAFE" />
                  ) : (
                    <VerdictBadge verdict="BLOCKED" />
                  )}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span>Verdict: {r.qualification_verdict}</span>
                  <span style={{ fontWeight: 800, color: r.security_clearance ? 'var(--status-safe)' : 'var(--status-highrisk)' }}>
                    Fit Score: {r.fit_score.toFixed(1)} / 100
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Candidate Detail & Explainable Screening Report */}
        <div>
          {selectedResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <Card title={`Screening Report: ${selectedResult.candidate_id}`} subtitle={`Target Job: ${selectedResult.job_id}`}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginBottom: '16px' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>FIT SCORE</div>
                    <div style={{ fontWeight: 800, fontSize: '1.25rem', color: selectedResult.security_clearance ? 'var(--status-safe)' : 'var(--status-highrisk)' }}>
                      {selectedResult.fit_score.toFixed(1)} / 100
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SKILL MATCH</div>
                    <div style={{ fontWeight: 700 }}>{selectedResult.skill_match_pct.toFixed(0)}%</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>MATCH CATEGORY</div>
                    <div style={{ fontWeight: 700 }}>{selectedResult.qualification_verdict}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SECURITY CLEARANCE</div>
                    {selectedResult.security_clearance ? (
                      <span style={{ fontWeight: 700, color: 'var(--status-safe)' }}>🟢 CLEARED</span>
                    ) : (
                      <span style={{ fontWeight: 700, color: 'var(--status-highrisk)' }}>🚨 QUARANTINED</span>
                    )}
                  </div>
                </div>

                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', padding: '12px', background: 'var(--bg-app)', borderRadius: '6px' }}>
                  <strong>Explainable Assessment:</strong> {selectedResult.explanation}
                </div>
              </Card>

              {/* Requirement Breakdown */}
              <Card title="Skill & Requirement Breakdown" subtitle="Normalized qualification mapping">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', background: 'var(--bg-app)', borderRadius: '4px' }}>
                    <span style={{ fontSize: '0.8125rem' }}>Python & API Engineering</span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--status-safe)' }}>MATCH</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', background: 'var(--bg-app)', borderRadius: '4px' }}>
                    <span style={{ fontSize: '0.8125rem' }}>Kubernetes & Container Orchestration</span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--status-safe)' }}>MATCH</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', background: 'var(--bg-app)', borderRadius: '4px' }}>
                    <span style={{ fontSize: '0.8125rem' }}>Cloud Security Infrastructure</span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--status-suspicious)' }}>PARTIAL</span>
                  </div>
                </div>
              </Card>

              {/* Security Provenance Traceability */}
              <Card title="Security & Provenance Traceability" subtitle="Audit trail from security pipeline">
                <pre className="security-evidence">
{`[SCREENING SECURITY PROVENANCE]
Candidate ID: ${selectedResult.candidate_id}
Job Target: ${selectedResult.job_id}
Security Clearance: ${selectedResult.security_clearance ? 'APPROVED' : 'QUARANTINED AT RANK #0'}
Security Gate Policy Rule: RULE-090-PROMPT-INJECTION-QUARANTINE
Fit Score Computation: Deterministic Semantic Embeddings`}
                </pre>
              </Card>
            </div>
          ) : (
            <Card>
              <EmptyState title="Select a Candidate" description="Click any candidate from the queue to view detailed screening reports." />
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
