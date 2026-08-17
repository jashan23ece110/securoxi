import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
        source: 'Scan Console Upload',
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
          description: 'Autonomous Candidate Evaluator',
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
      {/* 1. Page Header */}
      <PageHeader
        title="Security Brain — AI Reasoning & Attack Graphs"
        subtitle="Forensic signal correlation, threat attack graph visualization, and deterministic policy enforcement"
        breadcrumbs={[{ label: 'SECURITY' }, { label: 'SECURITY BRAIN' }]}
        badge={<Badge variant="info">AI Reasoning Engine Live</Badge>}
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button variant="secondary" size="sm" onClick={fetchData} icon={<RefreshCw size={13} />}>
              Refresh Telemetry
            </Button>
            <Button variant="primary" size="sm" onClick={() => navigate('/policies')} icon={<Sliders size={13} />}>
              Policy Engine Rules
            </Button>
          </div>
        }
      />

      {/* 2. Core Forensic Flow Stepper */}
      <Card style={{ marginBottom: '18px', padding: '12px 18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px', overflowX: 'auto' }}>
          {[
            { step: '1. SIGNAL', label: 'Payload', active: true, color: 'var(--accent-cyan)' },
            { step: '2. FORENSICS', label: 'Spans', active: true, color: 'var(--accent-cyan)' },
            { step: '3. DETECTION', label: 'Detectors', active: true, color: 'var(--accent-cyan)' },
            { step: '4. ATTACK GRAPH', label: 'Graph Model', active: true, color: 'var(--accent-cyan)' },
            { step: '5. AI REASONING', label: 'Advisory Note', active: true, color: 'var(--status-suspicious)' },
            { step: '6. POLICY ENGINE', label: 'Rule Enforced', active: true, color: 'var(--status-highrisk)' },
            { step: '7. AUDIT TRAIL', label: 'Immutable Log', active: true, color: 'var(--status-safe)' },
          ].map((s, idx, arr) => (
            <React.Fragment key={s.step}>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  padding: '6px 10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--bg-app)',
                  border: `1px solid ${s.color}40`,
                  minWidth: '100px',
                  textAlign: 'center',
                }}
              >
                <span style={{ fontSize: '0.6875rem', fontWeight: 800, color: s.color }}>{s.step}</span>
                <span style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>{s.label}</span>
              </div>
              {idx < arr.length - 1 && <span style={{ color: 'var(--border-strong)', fontSize: '0.75rem' }}>→</span>}
            </React.Fragment>
          ))}
        </div>
      </Card>

      {/* 3. Three-Column Workspace */}
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr 380px', gap: '16px', alignItems: 'start' }}>
        {/* LEFT COLUMN: Threat & Event Selection Stream */}
        <Card
          title="Correlated Findings"
          subtitle={`${threatStream.length} active telemetry events`}
          style={{ height: '700px', display: 'flex', flexDirection: 'column' }}
        >
          {/* Search Input */}
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

          {/* List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', flex: 1 }}>
            {threatStream.length === 0 ? (
              <EmptyState
                title="No Threat Telemetry"
                description="Upload a document in Scan Console to trigger Security Brain correlation."
              />
            ) : (
              threatStream.map((item) => {
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
              })
            )}
          </div>
        </Card>

        {/* CENTER COLUMN: Attack Graph & Workspace Canvas */}
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
                    aria-label="Reset View"
                    size="xs"
                    onClick={() => setZoomLevel(1)}
                  />
                </div>
              }
              style={{ minHeight: '440px', position: 'relative', overflow: 'hidden' }}
            >
              {/* Interactive SVG Attack Graph */}
              <div
                style={{
                  height: '340px',
                  width: '100%',
                  backgroundColor: '#040711',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-lg)',
                  position: 'relative',
                  overflow: 'hidden',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg
                  width="860"
                  height="300"
                  style={{
                    transform: `scale(${zoomLevel})`,
                    transition: 'transform var(--transition-fast)',
                  }}
                >
                  <defs>
                    <marker
                      id="arrow"
                      viewBox="0 0 10 10"
                      refX="8"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
                    </marker>
                  </defs>

                  {/* Edges */}
                  {graphEdges.map((edge, idx) => {
                    const fromNode = graphNodes.find((n) => n.id === edge.from);
                    const toNode = graphNodes.find((n) => n.id === edge.to);
                    if (!fromNode || !toNode) return null;

                    return (
                      <g key={idx}>
                        <line
                          x1={fromNode.x + 50}
                          y1={fromNode.y + 25}
                          x2={toNode.x}
                          y2={toNode.y + 25}
                          stroke={edge.color}
                          strokeWidth="2"
                          strokeDasharray="4 2"
                          markerEnd="url(#arrow)"
                        />
                        <text
                          x={(fromNode.x + toNode.x) / 2 + 20}
                          y={(fromNode.y + toNode.y) / 2 + 16}
                          fill="var(--text-muted)"
                          fontSize="9"
                          textAnchor="middle"
                          fontFamily="var(--font-sans)"
                        >
                          {edge.label}
                        </text>
                      </g>
                    );
                  })}

                  {/* Nodes */}
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
                          width="110"
                          height="50"
                          rx="6"
                          fill="var(--bg-surface-elevated)"
                          stroke={isSelected ? 'var(--accent-cyan)' : node.statusColor}
                          strokeWidth={isSelected ? 2 : 1}
                          filter="drop-shadow(0 2px 4px rgba(0,0,0,0.5))"
                        />
                        <text
                          x="55"
                          y="18"
                          fill={node.statusColor}
                          fontSize="9"
                          fontWeight="700"
                          textAnchor="middle"
                          letterSpacing="0.05em"
                        >
                          {node.label}
                        </text>
                        <text
                          x="55"
                          y="34"
                          fill="var(--text-primary)"
                          fontSize="10"
                          fontWeight="600"
                          textAnchor="middle"
                        >
                          {node.title.length > 14 ? `${node.title.substring(0, 12)}...` : node.title}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>

              {/* Node Quick Inspector Card if selected */}
              {selectedNode && (
                <div
                  style={{
                    marginTop: '12px',
                    padding: '10px 14px',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-md)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Badge variant="info">{selectedNode.label}</Badge>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {selectedNode.title}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      • {selectedNode.description}
                    </span>
                  </div>
                  <Button variant="ghost" size="xs" onClick={() => setSelectedNode(null)}>
                    Dismiss
                  </Button>
                </div>
              )}
            </Card>
          ) : (
            <Card>
              <EmptyState
                title="No Threat Selected"
                description="Select an incident or scan finding from the left stream to inspect the attack graph."
              />
            </Card>
          )}

          {/* Bottom Tabs: Graph Timeline & Provenance Trail */}
          {activeItem && (
            <Card title="Attack Execution & Policy Provenance Trail" subtitle="Deterministic sequence of security events">
              <Timeline
                items={[
                  {
                    id: 1,
                    title: `Payload Ingested: ${activeItem.asset}`,
                    timestamp: new Date(activeItem.timestamp).toLocaleTimeString(),
                    description: `Origin: ${activeItem.source} • Transmitted to Security Brain ingestion pipeline.`,
                    statusColor: 'var(--accent-cyan)',
                  },
                  {
                    id: 2,
                    title: `Deterministic Forensic Parser Intercept: ${activeItem.title}`,
                    timestamp: new Date(activeItem.timestamp).toLocaleTimeString(),
                    description: `Scored document risk at ${activeItem.riskScore}/100. Extracted malicious prompt injection pattern.`,
                    statusColor: 'var(--status-highrisk)',
                    badge: <SeverityBadge severity={activeItem.severity} />,
                  },
                  {
                    id: 3,
                    title: `Policy Engine Action Enforced: ${activeItem.policyAction}`,
                    timestamp: new Date(activeItem.timestamp).toLocaleTimeString(),
                    description: `Rule: ${activeItem.policyRule} • Quarantined payload and blocked automated evaluation.`,
                    statusColor: 'var(--status-safe)',
                    badge: <StatusBadge status={activeItem.policyAction} />,
                  },
                ]}
              />
            </Card>
          )}
        </div>

        {/* RIGHT COLUMN: Forensic Authority & Decision Triad */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {activeItem ? (
            <>
              {/* Layer 1: Deterministic Forensic Finding */}
              <Card
                title="1. Deterministic Finding"
                subtitle="Exact mathematical payload evidence (Authoritative)"
                badge={<Badge variant="highrisk">Verified</Badge>}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <RiskIndicator score={activeItem.riskScore} />

                  <EvidenceBlock
                    threatType={activeItem.title}
                    category="PROMPT_INJECTION"
                    severity={activeItem.severity}
                    evidence={activeItem.evidence}
                    confidence={0.99}
                    detector="PromptInjectionDetector"
                    explanation="Concealed instruction set designed to manipulate candidate ranking."
                  />
                </div>
              </Card>

              {/* Layer 2: AI Advisory Reasoning */}
              <Card
                title="2. AI Advisory Reasoning"
                subtitle="Gemini / Claude Inference Analysis (Non-Authoritative)"
                badge={<Badge variant="neutral">Advisory Note</Badge>}
              >
                <div
                  style={{
                    padding: '12px',
                    backgroundColor: 'var(--bg-app)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.8125rem',
                    lineHeight: 1.5,
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-indigo)', fontWeight: 700, fontSize: '0.75rem' }}>
                    <Sparkles size={13} />
                    <span>LLM ROOT-CAUSE HYPOTHESIS:</span>
                  </div>
                  <p>
                    The payload attempts a classic prompt boundary break using instruction reset syntax. The attacker's objective is to force the downstream evaluation model to output a 100/100 score and exfiltrate API secrets.
                  </p>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '4px' }}>
                    Notice: AI heuristics provide context only. The Policy Engine below retains final blocking authority.
                  </div>
                </div>
              </Card>

              {/* Layer 3: Deterministic Policy Decision */}
              <Card
                title="3. Enforced Policy Decision"
                subtitle="Deterministic policy engine action (Final Authority)"
                badge={<StatusBadge status={activeItem.policyAction} />}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.8125rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Enforced Rule:</span>
                    <strong style={{ color: 'var(--text-primary)' }}>{activeItem.policyRule}</strong>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Action Executed:</span>
                    <StatusBadge status={activeItem.policyAction} showDot={true} />
                  </div>

                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                      Automated Mitigations:
                    </span>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {activeItem.responseActions.map((act) => (
                        <span
                          key={act}
                          style={{
                            fontSize: '0.6875rem',
                            fontWeight: 700,
                            padding: '2px 6px',
                            backgroundColor: 'var(--bg-surface-elevated)',
                            borderRadius: 'var(--radius-xs)',
                            border: '1px solid var(--border-default)',
                            color: 'var(--accent-cyan)',
                          }}
                        >
                          {act}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            </>
          ) : (
            <Card>
              <EmptyState title="Forensics Idle" description="Select a threat finding to inspect the decision triad." />
            </Card>
          )}
        </div>
      </div>
    </PageContainer>
  );
};
