import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { ScanReport } from '../api/types';
import {
  Card,
  Button,
  IconButton,
  Badge,
  VerdictBadge,
  SeverityBadge,
  Alert,
  LoadingState,
  EmptyState,
  ErrorState,
} from '../components/ui';
import { ForensicDocumentViewer } from '../components/forensics';
import { PageHeader, PageContainer } from '../components/layout';
import {
  ShieldAlert,
  ShieldCheck,
  Brain,
  FileText,
  Search,
  Copy,
  Check,
  Crosshair,
  ArrowLeft,
  ArrowRight,
  ExternalLink,
  RotateCw,
  AlertTriangle,
  Folder,
  Layers,
} from 'lucide-react';
import { parseFindingCoordinates, ParsedForensicFinding } from '../utils/coordinateTransform';

export const InvestigationPage: React.FC = () => {
  const { scanId } = useParams<{ scanId?: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const activeScanId = scanId || searchParams.get('scan_id') || '';
  const initialFindingId = searchParams.get('finding_id');

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [scan, setScan] = useState<ScanReport | null>(null);
  const [selectedFindingIndex, setSelectedFindingIndex] = useState<number>(0);
  const [copied, setCopied] = useState<boolean>(false);
  const [documentSearch, setDocumentSearch] = useState<string>('');

  // Fetch scan details from backend
  useEffect(() => {
    let isMounted = true;
    const fetchScan = async () => {
      setLoading(true);
      setError(null);
      try {
        if (activeScanId) {
          const res = await api.getScan(activeScanId);
          if (isMounted) setScan(res);
        } else {
          // Fetch most recent scan as default
          const list = await api.listScans();
          if (isMounted && list.length > 0) {
            setScan(list[0]);
          }
        }
      } catch (err: any) {
        if (isMounted) setError(err.message || 'Failed to load document security report.');
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchScan();
    return () => {
      isMounted = false;
    };
  }, [activeScanId]);

  const findings: ParsedForensicFinding[] = useMemo(() => {
    if (!scan || !scan.findings) return [];
    return scan.findings.map((f, i) => parseFindingCoordinates(f, i));
  }, [scan]);

  // Set selected finding from URL query param if present
  useEffect(() => {
    if (findings.length > 0 && initialFindingId) {
      const idx = findings.findIndex((f) => f.id === initialFindingId);
      if (idx >= 0) setSelectedFindingIndex(idx);
    }
  }, [findings, initialFindingId]);

  const activeFinding = findings[selectedFindingIndex] || null;

  const handleCopyEvidence = () => {
    if (!activeFinding) return;
    navigator.clipboard.writeText(
      `[SECUROXI FORENSIC EVIDENCE]\nDocument: ${scan?.filename}\nFinding: ${activeFinding.title} (${activeFinding.severity})\nPage: ${activeFinding.page}\nSource: ${activeFinding.source}\nEvidence: ${activeFinding.evidence}\nCoordinates: [${activeFinding.bbox.x0}, ${activeFinding.bbox.y0}, ${activeFinding.bbox.x1}, ${activeFinding.bbox.y1}]`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenSecurityBrain = () => {
    if (!scan) return;
    const q = new URLSearchParams({
      scan_id: scan.scan_id,
      ...(activeFinding ? { finding_id: activeFinding.id } : {}),
    });
    navigate(`/security-brain?${q.toString()}`);
  };

  if (loading) {
    return (
      <PageContainer>
        <LoadingState message="Loading document forensic intelligence report..." />
      </PageContainer>
    );
  }

  if (error || !scan) {
    return (
      <PageContainer>
        <ErrorState
          title="Investigation Data Unavailable"
          message={error || 'No document security report could be found for the specified identifier.'}
          onRetry={() => window.location.reload()}
        />
      </PageContainer>
    );
  }

  const isUninspectable = (scan.verdict as string) === 'UNINSPECTABLE';

  return (
    <PageContainer>
      {/* 1. Header Bar with Document Metadata & Primary Actions */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 20px',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-default)',
          marginBottom: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <button
            onClick={() => navigate(-1)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <ArrowLeft size={18} />
          </button>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                {scan.filename}
              </h1>
              <Badge variant="neutral">{scan.document_type}</Badge>
              <VerdictBadge verdict={scan.verdict} />
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '3px' }}>
              Scan ID: <code>{scan.scan_id}</code> • Analyzed {new Date(scan.created_at).toLocaleString()}
              {findings.length > 0 && ` • ${findings.length} forensic finding${findings.length > 1 ? 's' : ''}`}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ textAlign: 'right', marginRight: '8px' }}>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>THREAT RISK GAUGE</div>
            <div
              style={{
                fontSize: '1.125rem',
                fontWeight: 900,
                color: scan.risk_score >= 80 ? 'var(--status-highrisk)' : scan.risk_score >= 40 ? 'var(--status-warning)' : 'var(--status-safe)',
              }}
            >
              {scan.risk_score} / 100
            </div>
          </div>

          <Button variant="secondary" size="sm" onClick={handleCopyEvidence} icon={copied ? <Check size={14} /> : <Copy size={14} />}>
            {copied ? 'Copied' : 'Copy Evidence'}
          </Button>

          <Button variant="primary" size="sm" onClick={handleOpenSecurityBrain} icon={<Brain size={14} />}>
            Security Brain
          </Button>
        </div>
      </div>

      {/* 2. UNINSPECTABLE Warning Banner */}
      {isUninspectable && (
        <div style={{ marginBottom: '16px' }}>
          <Alert type="danger" title="DOCUMENT NOT FULLY INSPECTABLE (UNINSPECTABLE != SAFE)">
            SECUROXI could not extract a verifiable text layer or complete OCR raster evaluation on this document.
            Per security policy invariants, uninspectable files are quarantined and must never be treated as safe.
          </Alert>
        </div>
      )}

      {/* 3. Main Split Forensic Workspace */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 380px',
          gap: '16px',
          minHeight: '620px',
        }}
      >
        {/* Left: Document Viewport & Interactive Findings */}
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-default)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Finding Stepper Bar */}
          <div
            style={{
              padding: '10px 16px',
              backgroundColor: 'var(--bg-app)',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-muted)' }}>
                FINDINGS ({findings.length}):
              </span>
              <div style={{ display: 'flex', gap: '6px', overflowX: 'auto' }}>
                {findings.map((f, idx) => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedFindingIndex(idx)}
                    style={{
                      padding: '4px 8px',
                      borderRadius: 'var(--radius-xs)',
                      border: `1px solid ${idx === selectedFindingIndex ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                      backgroundColor: idx === selectedFindingIndex ? 'rgba(56, 189, 248, 0.12)' : 'var(--bg-surface)',
                      color: idx === selectedFindingIndex ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                      fontSize: '0.6875rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <span>{idx + 1}.</span>
                    <span>{f.category}</span>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '4px' }}>
              <IconButton
                icon={<ArrowLeft size={14} />}
                size="xs"
                aria-label="Previous Finding"
                disabled={findings.length <= 1 || selectedFindingIndex <= 0}
                onClick={() => setSelectedFindingIndex((p) => Math.max(p - 1, 0))}
              />
              <IconButton
                icon={<ArrowRight size={14} />}
                size="xs"
                aria-label="Next Finding"
                disabled={findings.length <= 1 || selectedFindingIndex >= findings.length - 1}
                onClick={() => setSelectedFindingIndex((p) => Math.min(p + 1, findings.length - 1))}
              />
            </div>
          </div>

          {/* Document Content Viewport */}
          <div
            style={{
              flex: 1,
              padding: '20px',
              overflowY: 'auto',
              display: 'flex',
              justifyContent: 'center',
              backgroundColor: '#070a14',
            }}
          >
            <div
              style={{
                width: '100%',
                maxWidth: '680px',
                backgroundColor: '#0c101d',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-default)',
                padding: '24px',
                color: 'var(--text-primary)',
                fontSize: '0.875rem',
                lineHeight: 1.6,
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
              }}
            >
              <div
                style={{
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '12px',
                  marginBottom: '16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  DOCUMENT REPRESENTATION — {scan.document_type} (Page {activeFinding ? activeFinding.page : 1})
                </div>
                {activeFinding && (
                  <Badge variant={activeFinding.source === 'OCR' ? 'info' : 'safe'}>
                    {activeFinding.source === 'OCR' ? 'OCR-DERIVED' : 'NATIVE PARSER'}
                  </Badge>
                )}
              </div>

              {activeFinding ? (
                <div>
                  <p style={{ color: 'var(--text-secondary)' }}>
                    Candidate / Document body stream extracted by SECUROXI Layout Engine:
                  </p>

                  <div
                    style={{
                      padding: '16px',
                      backgroundColor: 'rgba(244, 63, 94, 0.06)',
                      border: '1px solid rgba(244, 63, 94, 0.3)',
                      borderRadius: 'var(--radius-sm)',
                      margin: '16px 0',
                    }}
                  >
                    <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--status-highrisk)', marginBottom: '6px' }}>
                      HIGHLIGHTED ADVERSARIAL SECTION (PAGE {activeFinding.page}):
                    </div>
                    <pre
                      style={{
                        margin: 0,
                        fontSize: '0.8125rem',
                        fontFamily: 'monospace',
                        color: 'var(--accent-cyan)',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}
                    >
                      {activeFinding.evidence}
                    </pre>
                  </div>

                  <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    Remaining document paragraphs evaluated cleanly against standard baseline security rules.
                  </p>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                  Zero adversarial findings recorded. Document verified safe under active policies.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Three-Layer Forensic Evidence Panel */}
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-default)',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            overflowY: 'auto',
          }}
        >
          {activeFinding ? (
            <>
              {/* Finding Header */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                  <SeverityBadge severity={activeFinding.severity} />
                  <Badge variant={activeFinding.source === 'OCR' ? 'info' : 'safe'}>
                    {activeFinding.source === 'OCR' ? 'OCR-DERIVED' : 'NATIVE'}
                  </Badge>
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                  {activeFinding.title}
                </h3>
              </div>

              {/* Layer 1: FORENSIC EVIDENCE */}
              <div
                style={{
                  padding: '12px',
                  backgroundColor: '#040711',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                }}
              >
                <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--accent-cyan)', marginBottom: '6px' }}>
                  1. FORENSIC EVIDENCE (OBSERVED)
                </div>
                <pre
                  style={{
                    margin: 0,
                    padding: '8px 10px',
                    fontSize: '0.75rem',
                    maxHeight: '120px',
                    overflowY: 'auto',
                    backgroundColor: 'rgba(0, 0, 0, 0.6)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-sm)',
                    color: '#38bdf8',
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {activeFinding.evidence}
                </pre>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.6875rem', marginTop: '8px', color: 'var(--text-muted)' }}>
                  <div>Page: <strong style={{ color: 'var(--text-primary)' }}>{activeFinding.page}</strong></div>
                  <div>Source: <strong style={{ color: 'var(--text-primary)' }}>{activeFinding.source}</strong></div>
                  <div style={{ gridColumn: 'span 2' }}>
                    BBox: <code style={{ color: 'var(--accent-cyan)' }}>[{activeFinding.bbox.x0}, {activeFinding.bbox.y0}, {activeFinding.bbox.x1}, {activeFinding.bbox.y1}]</code>
                  </div>
                </div>
              </div>

              {/* Layer 2: AI ADVISORY */}
              <div
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  2. AI ADVISORY (INTERPRETATION)
                </div>
                <div style={{ color: 'var(--text-secondary)', lineHeight: 1.4, fontSize: '0.75rem' }}>
                  {activeFinding.description || 'Adversarial instruction detected attempting to manipulate automated workflow evaluation.'}
                </div>
              </div>

              {/* Layer 3: POLICY AUTHORITY & ENFORCEMENT */}
              <div
                style={{
                  padding: '12px',
                  backgroundColor: activeFinding.severity === 'CRITICAL' || activeFinding.severity === 'HIGH'
                    ? 'rgba(244, 63, 94, 0.08)'
                    : 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${
                    activeFinding.severity === 'CRITICAL' || activeFinding.severity === 'HIGH'
                      ? 'rgba(244, 63, 94, 0.3)'
                      : 'var(--border-subtle)'
                  }`,
                }}
              >
                <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--status-highrisk)', marginBottom: '4px' }}>
                  3. POLICY AUTHORITY & ENFORCEMENT
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Policy: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>RULE-100-HIGH-RISK-BLOCK</strong>
                  </div>
                  <Badge variant={activeFinding.severity === 'CRITICAL' || activeFinding.severity === 'HIGH' ? 'highrisk' : 'review'}>
                    {activeFinding.severity === 'CRITICAL' || activeFinding.severity === 'HIGH' ? 'BLOCK + QUARANTINE' : 'REVIEW REQUIRED'}
                  </Badge>
                </div>
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
              Select a finding to inspect its three-layer forensic breakdown.
            </div>
          )}
        </div>
      </div>
    </PageContainer>
  );
};
