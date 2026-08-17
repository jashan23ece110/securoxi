import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import { Incident, ScanReport } from '../api/types';
import {
  Card,
  Button,
  IconButton,
  StatusBadge,
  SeverityBadge,
  VerdictBadge,
  LoadingState,
  EmptyState,
  ErrorState,
  EvidenceBlock,
  RiskIndicator,
  Timeline,
  Tabs,
  Badge,
  Alert,
} from '../components/ui';
import { PageHeader, PageToolbar, PageContainer } from '../components/layout';
import {
  Brain,
  ShieldAlert,
  ShieldCheck,
  Zap,
  Terminal,
  Cpu,
  Layers,
  ArrowRight,
  RefreshCw,
  Search,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Target,
  FileCode,
  Sliders,
  Sparkles,
  ExternalLink,
  Compass,
  Activity,
  CheckCircle2,
  FileText,
} from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  type: 'ACTOR' | 'ARTIFACT' | 'SIGNAL' | 'TECHNIQUE' | 'TARGET' | 'IMPACT';
  title: string;
  description: string;
  statusColor: string;
  x: number;
  y: number;
}

interface GraphEdge {
  from: string;
  to: string;
  label: string;
  color: string;
}

export const SecurityBrainPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const initialScanId = searchParams.get('scan_id');
  const initialIncidentId = searchParams.get('incident_id');
  const initialFindingId = searchParams.get('finding_id');
  const initialMode = (searchParams.get('mode') as 'guided' | 'advanced') || 'guided';

  const [investigationMode, setInvestigationMode] = useState<'guided' | 'advanced'>(initialMode);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [scans, setScans] = useState<ScanReport[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [selectedScan, setSelectedScan] = useState<ScanReport | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [searchFilter, setSearchFilter] = useState('');
  const [activeTab, setActiveTab] = useState<'graph' | 'evidence' | 'timeline'>('graph');

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

      // Deep link selection handling
      if (initialIncidentId) {
        const foundInc = incRes.find((i) => i.incident_id === initialIncidentId);
        if (foundInc) {
          setSelectedIncident(foundInc);
          setSelectedScan(null);
          return;
        }
      }

      if (initialScanId) {
        const foundScan = scansRes.find((s) => s.scan_id === initialScanId);
        if (foundScan) {
          setSelectedScan(foundScan);
          setSelectedIncident(null);
          return;
        }
      }

      if (incRes.length > 0) {
        setSelectedIncident(incRes[0]);
      } else if (scansRes.length > 0) {
        setSelectedScan(scansRes[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to connect to Security Brain telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filtered threat stream
  const threatStream = [
    ...incidents.map((inc) => ({
      id: inc.incident_id,
      title: inc.attack_type,
      subtitle: inc.affected_asset,
      severity: inc.severity,
      riskScore: inc.risk_score,
      timestamp: inc.created_at,
      type: 'INCIDENT' as const,
      raw: inc,
    })),
    ...scans
      .filter((s) => s.verdict === 'HIGH_RISK' || s.verdict === 'CRITICAL' || s.verdict === 'BLOCKED' || (s.findings && s.findings.length > 0))
      .map((s) => ({
        id: s.scan_id,
        title: s.findings?.[0]?.threat_type || 'CONCEALED_OVERRIDE',
        subtitle: s.filename,
        severity: s.findings?.[0]?.severity || (s.verdict === 'CRITICAL' ? 'CRITICAL' : 'HIGH'),
        riskScore: s.risk_score,
        timestamp: s.created_at,
        type: 'SCAN' as const,
        raw: s,
      })),
  ].filter(
    (item) =>
      item.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
      item.subtitle.toLowerCase().includes(searchFilter.toLowerCase()) ||
      item.id.toLowerCase().includes(searchFilter.toLowerCase())
  );

  // Active item representation
  const activeItem = selectedIncident
    ? {
        id: selectedIncident.incident_id,
        title: selectedIncident.attack_type,
        asset: selectedIncident.affected_asset,
        severity: selectedIncident.severity,
        riskScore: selectedIncident.risk_score,
        source: selectedIncident.source || 'External ATS Webhook',
        evidence: selectedIncident.evidence || 'Indirect prompt injection concealed in document body.',
        policyRule: selectedIncident.policy_decision?.rule_name || 'RULE-100-HIGH-RISK-BLOCK',
        policyAction: selectedIncident.policy_decision?.action || 'BLOCKED',
        responseActions: selectedIncident.response_actions || ['QUARANTINE_PAYLOAD', 'DISPATCH_SIEM_EVENT'],
        timestamp: selectedIncident.created_at,
        findings: [
          {
            threat_type: selectedIncident.attack_type,
            category: 'ADVERSARIAL_INJECTION',
            severity: selectedIncident.severity,
            confidence: 0.99,
            evidence: selectedIncident.evidence,
            description: 'Concealed instruction set designed to manipulate candidate ranking.',
          },
        ],
      }
    : selectedScan
    ? {
        id: selectedScan.scan_id,
        title: selectedScan.findings?.[0]?.threat_type || 'CONCEALED_INSTRUCTION',
        asset: selectedScan.filename,
        severity: selectedScan.findings?.[0]?.severity || (selectedScan.verdict === 'CRITICAL' ? 'CRITICAL' : 'HIGH'),
        riskScore: selectedScan.risk_score,
        source: 'Scan Console Ingress',
        evidence: selectedScan.findings?.[0]?.evidence || selectedScan.summary || 'Adversarial override detected.',
        policyRule: 'RULE-100-DETERMINISTIC-QUARANTINE',
        policyAction: selectedScan.verdict,
        responseActions: ['QUARANTINE_DOCUMENT', 'AUDIT_LOG_RECORD'],
        timestamp: selectedScan.created_at,
        findings: selectedScan.findings || [],
      }
    : null;

  // Construct Attack Graph Nodes & Edges from active item
  const graphNodes: GraphNode[] = activeItem
    ? [
        {
          id: 'node-actor',
          label: 'ACTOR',
          type: 'ACTOR',
          title: 'Untrusted Origin',
          description: activeItem.source,
          statusColor: 'var(--text-secondary)',
          x: 60,
          y: 120,
        },
        {
          id: 'node-artifact',
          label: 'ARTIFACT',
          type: 'ARTIFACT',
          title: 'Payload Document',
          description: activeItem.asset,
          statusColor: 'var(--accent-cyan)',
          x: 230,
          y: 120,
        },
        {
          id: 'node-signal',
          label: 'SIGNAL',
          type: 'SIGNAL',
          title: 'Forensic Anomaly',
          description: 'Concealed Layout / Micro-Text',
          statusColor: 'var(--status-suspicious)',
          x: 400,
          y: 50,
        },
        {
          id: 'node-technique',
          label: 'TECHNIQUE',
          type: 'TECHNIQUE',
          title: activeItem.title,
          description: `Severity: ${activeItem.severity}`,
          statusColor: 'var(--status-highrisk)',
          x: 400,
          y: 190,
        },
        {
          id: 'node-target',
          label: 'TARGET',
          type: 'TARGET',
          title: 'Screening LLM Agent',
          description: 'Autonomous Evaluator',
          statusColor: 'var(--accent-indigo)',
          x: 580,
          y: 120,
        },
        {
          id: 'node-impact',
          label: 'IMPACT',
          type: 'IMPACT',
          title: 'Policy Intercepted',
          description: `Action: ${activeItem.policyAction}`,
          statusColor: 'var(--status-safe)',
          x: 750,
          y: 120,
        },
      ]
    : [];

  const graphEdges: GraphEdge[] = [
    { from: 'node-actor', to: 'node-artifact', label: 'Transmits', color: 'var(--border-strong)' },
    { from: 'node-artifact', to: 'node-signal', label: 'Contains', color: 'var(--status-suspicious)' },
    { from: 'node-artifact', to: 'node-technique', label: 'Executes', color: 'var(--status-highrisk)' },
    { from: 'node-signal', to: 'node-target', label: 'Bypasses Filter', color: 'var(--border-strong)' },
    { from: 'node-technique', to: 'node-target', label: 'Hijacks Prompt', color: 'var(--status-highrisk)' },
    { from: 'node-target', to: 'node-impact', label: 'Mitigated By', color: 'var(--status-safe)' },
  ];

  if (loading) {
    return (
      <PageContainer>
        <LoadingState
          message="Synthesizing Security Brain Attack Graphs & Reasoning Telemetry..."
          subMessage="Correlating multi-stage detection vectors with deterministic policy engine"
        />
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <ErrorState
          title="Failed to Load Security Brain"
          message={error}
          onRetry={fetchData}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      {/* 1. Page Header & Mode Switcher */}
      <PageHeader
        title="Security Brain — Threat Causality & Investigation"
        subtitle="Forensic signal correlation, attack graph visualization, and deterministic policy enforcement"
        breadcrumbs={[{ label: 'SECURITY' }, { label: 'SECURITY BRAIN' }]}
        badge={<Badge variant="info">AI Reasoning Engine Live</Badge>}
        actions={
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {/* Mode Switcher */}
            <div
              style={{
                display: 'flex',
                backgroundColor: 'var(--bg-input)',
                padding: '2px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-default)',
              }}
            >
              <button
                onClick={() => setInvestigationMode('guided')}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-sm)',
                  border: 'none',
                  backgroundColor: investigationMode === 'guided' ? 'var(--accent-cyan)' : 'transparent',
                  color: investigationMode === 'guided' ? '#040711' : 'var(--text-secondary)',
                  fontWeight: 700,
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                }}
              >
                Guided Mode
              </button>
              <button
                onClick={() => setInvestigationMode('advanced')}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-sm)',
                  border: 'none',
                  backgroundColor: investigationMode === 'advanced' ? 'var(--accent-cyan)' : 'transparent',
                  color: investigationMode === 'advanced' ? '#040711' : 'var(--text-secondary)',
                  fontWeight: 700,
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                }}
              >
                Advanced Graph
              </button>
            </div>

            <Button variant="secondary" size="sm" onClick={fetchData} icon={<RefreshCw size={13} />}>
              Refresh
            </Button>
            <Button variant="primary" size="sm" onClick={() => navigate('/policies')} icon={<Sliders size={13} />}>
              Policies
            </Button>
          </div>
        }
      />

      {/* 2. Persistent Investigation Context Bar */}
      {activeItem && (
        <div
          style={{
            padding: '12px 18px',
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-default)',
            marginBottom: '16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'block' }}>INVESTIGATING THREAT</span>
              <strong style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{activeItem.title}</strong>
            </div>
            <div style={{ height: '24px', width: '1px', backgroundColor: 'var(--border-subtle)' }} />
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'block' }}>AFFECTED ASSET</span>
              <span style={{ fontSize: '0.8125rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>{activeItem.asset}</span>
            </div>
            <div style={{ height: '24px', width: '1px', backgroundColor: 'var(--border-subtle)' }} />
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'block' }}>INGRESS ORIGIN</span>
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{activeItem.source}</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <SeverityBadge severity={activeItem.severity} />
            <span style={{ fontSize: '0.8125rem', fontWeight: 800, color: activeItem.riskScore >= 70 ? 'var(--status-highrisk)' : 'var(--status-safe)' }}>
              Risk: {activeItem.riskScore}/100
            </span>
          </div>
        </div>
      )}

      {/* 3. GUIDED INVESTIGATION MODE (Default for Security Users) */}
      {investigationMode === 'guided' && activeItem && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Causal Step 1: Observed Forensic Evidence */}
          <Card
            title="1. Empirical Forensic Evidence"
            subtitle="Raw unmanipulated text payload and layout anomaly detected by parser engine"
            badge={<Badge variant="safe">Observed Fact</Badge>}
            action={
              <Button
                variant="secondary"
                size="xs"
                onClick={() => navigate(`/investigate/${activeItem.id}`)}
                icon={<FileText size={12} />}
              >
                Inspect on Document Canvas
              </Button>
            }
          >
            <pre
              className="security-evidence"
              style={{
                margin: 0,
                padding: '12px 14px',
                fontSize: '0.8125rem',
                backgroundColor: '#040711',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                borderRadius: 'var(--radius-md)',
                color: '#38bdf8',
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {activeItem.evidence}
            </pre>
          </Card>

          {/* Causal Step 2 & 3 Grid: AI Advisory vs Deterministic Policy Authority */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* AI Advisory */}
            <Card
              title="2. AI Advisory Interpretation"
              subtitle="Probabilistic reasoning note generated by LLM evaluation layer"
              badge={<Badge variant="info">Advisory Only</Badge>}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  The extracted evidence exhibits strong structural patterns consistent with an indirect prompt injection attack.
                  The author attempts to override system prompt instructions by asserting a hard rating of 100/100 to bypass ATS keyword filtering.
                </p>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
                  ⚠️ <em>Notice: AI Advisory provides contextual explanation only and cannot override deterministic policy rules.</em>
                </div>
              </div>
            </Card>

            {/* Policy Authority */}
            <Card
              title="3. Policy Authority & Decision"
              subtitle="Authoritative deterministic enforcement by SECUROXI Policy Engine"
              badge={<Badge variant="critical">Enforced Decision</Badge>}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Evaluated Policy Rule:</span>
                  <code style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontWeight: 700 }}>{activeItem.policyRule}</code>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Security Clearance Gate:</span>
                  <Badge variant="blocked">{activeItem.policyAction}</Badge>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Response Playbooks:</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--status-highrisk)', fontWeight: 700 }}>
                    {activeItem.responseActions.join(', ')}
                  </span>
                </div>
              </div>
            </Card>
          </div>

          {/* Action Footer */}
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '8px' }}>
            <Button
              variant="secondary"
              onClick={() => navigate(`/ask?q=What%20evidence%20supports%20threat%20${encodeURIComponent(activeItem.title)}%3F`)}
              icon={<Sparkles size={14} />}
            >
              Ask SECUROXI About Threat
            </Button>
            <Button
              variant="primary"
              onClick={() => navigate('/incidents')}
              icon={<ShieldAlert size={14} />}
            >
              View Linked Incident
            </Button>
          </div>
        </div>
      )}

      {/* 4. ADVANCED SOC INVESTIGATION MODE (Full Interactive Graph) */}
      {investigationMode === 'advanced' && (
        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr 380px', gap: '16px', alignItems: 'start' }}>
          {/* LEFT: Threat & Event Selection Stream */}
          <Card
            title="Correlated Findings"
            subtitle={`${threatStream.length} active telemetry events`}
            style={{ height: '700px', display: 'flex', flexDirection: 'column' }}
          >
            <div style={{ marginBottom: '12px' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 10px',
                  backgroundColor: 'var(--bg-app)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                }}
              >
                <Search size={13} style={{ color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Filter threats & vectors..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-primary)',
                    fontSize: '0.75rem',
                    outline: 'none',
                    width: '100%',
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', flex: 1 }}>
              {threatStream.map((item) => {
                const isSelected =
                  (item.type === 'INCIDENT' && selectedIncident?.incident_id === item.id) ||
                  (item.type === 'SCAN' && selectedScan?.scan_id === item.id);

                return (
                  <div
                    key={item.id}
                    onClick={() => {
                      if (item.type === 'INCIDENT') {
                        setSelectedIncident(item.raw as Incident);
                        setSelectedScan(null);
                      } else {
                        setSelectedScan(item.raw as ScanReport);
                        setSelectedIncident(null);
                      }
                      setSelectedNode(null);
                    }}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isSelected ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                      border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {item.title}
                      </span>
                      <SeverityBadge severity={item.severity} />
                    </div>

                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
                      {item.subtitle}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                      <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {item.id}
                      </span>
                      <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: item.riskScore >= 70 ? 'var(--status-highrisk)' : 'var(--status-safe)' }}>
                        Risk: {item.riskScore}/100
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* CENTER: Attack Graph Canvas */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {activeItem ? (
              <Card
                title="Threat Attack Graph"
                subtitle={`Visualizing inferred threat causality chain for ${activeItem.id}`}
                action={
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <IconButton
                      icon={<ZoomIn size={14} />}
                      aria-label="Zoom In"
                      size="xs"
                      onClick={() => setZoomLevel((z) => Math.min(1.5, z + 0.1))}
                    />
                    <IconButton
                      icon={<ZoomOut size={14} />}
                      aria-label="Zoom Out"
                      size="xs"
                      onClick={() => setZoomLevel((z) => Math.max(0.7, z - 0.1))}
                    />
                    <IconButton
                      icon={<RotateCcw size={14} />}
                      aria-label="Reset Zoom"
                      size="xs"
                      onClick={() => setZoomLevel(1)}
                    />
                  </div>
                }
              >
                <div
                  style={{
                    height: '380px',
                    backgroundColor: '#02040a',
                    borderRadius: 'var(--radius-md)',
                    position: 'relative',
                    overflow: 'hidden',
                    border: '1px solid var(--border-default)',
                  }}
                >
                  <svg
                    style={{
                      width: '100%',
                      height: '100%',
                      transform: `scale(${zoomLevel})`,
                      transformOrigin: 'center center',
                      transition: 'transform 0.2s ease',
                    }}
                  >
                    <defs>
                      <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--accent-cyan)" opacity="0.8" />
                      </marker>
                    </defs>

                    {graphEdges.map((e, idx) => {
                      const fromNode = graphNodes.find((n) => n.id === e.from);
                      const toNode = graphNodes.find((n) => n.id === e.to);
                      if (!fromNode || !toNode) return null;
                      return (
                        <g key={idx}>
                          <line
                            x1={fromNode.x + 60}
                            y1={fromNode.y + 25}
                            x2={toNode.x + 60}
                            y2={toNode.y + 25}
                            stroke={e.color}
                            strokeWidth="2"
                            strokeDasharray="4 2"
                            markerEnd="url(#arrow)"
                          />
                        </g>
                      );
                    })}

                    {graphNodes.map((node) => {
                      const isSelected = selectedNode?.id === node.id;
                      return (
                        <g
                          key={node.id}
                          transform={`translate(${node.x}, ${node.y})`}
                          onClick={() => setSelectedNode(node)}
                          style={{ cursor: 'pointer' }}
                        >
                          <rect
                            width="120"
                            height="50"
                            rx="6"
                            fill="#0c101d"
                            stroke={isSelected ? 'var(--accent-cyan)' : node.statusColor}
                            strokeWidth={isSelected ? '2.5' : '1.5'}
                          />
                          <text x="10" y="18" fill="var(--text-muted)" fontSize="9" fontWeight="800">
                            {node.label}
                          </text>
                          <text x="10" y="34" fill="var(--text-primary)" fontSize="11" fontWeight="700">
                            {node.title.length > 14 ? `${node.title.slice(0, 12)}...` : node.title}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                </div>
              </Card>
            ) : (
              <EmptyState title="No Active Threat Selected" description="Choose a threat from the list to visualize." />
            )}
          </div>

          {/* RIGHT: Node Inspector & Decision Panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <Card
              title={selectedNode ? `Node: ${selectedNode.title}` : 'Decision Telemetry'}
              subtitle={selectedNode ? selectedNode.description : 'Authoritative Policy Decision'}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Policy Rule:</span>
                  <code style={{ fontSize: '0.75rem', color: 'var(--text-primary)' }}>{activeItem?.policyRule}</code>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Action:</span>
                  <Badge variant="blocked">{activeItem?.policyAction}</Badge>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </PageContainer>
  );
};
