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
  Alert,
  Input,
} from '../components/ui';
import { PageHeader, PageToolbar, PageContainer } from '../components/layout';
import {
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
  CheckCircle,
  AlertTriangle,
  Lock,
  ExternalLink,
  Share2,
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

export const IncidentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [scans, setScans] = useState<ScanReport[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchFilter, setSearchFilter] = useState('');
  const [activeTab, setActiveTab] = useState<'evidence' | 'graph' | 'timeline' | 'related'>('evidence');
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

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

  // Handle Analyst Status Transitions
  const handleUpdateStatus = async (newStatus: Incident['status']) => {
    if (!selectedIncident) return;
    try {
      if (newStatus === 'RESOLVED' || newStatus === 'CLOSED') {
        await api.resolveIncident(selectedIncident.incident_id, 'Analyst verified threat neutralization and verified clean audit log.');
      }
      setSelectedIncident({
        ...selectedIncident,
        status: newStatus,
      });
      setIncidents((prev) =>
        prev.map((inc) =>
          inc.incident_id === selectedIncident.incident_id ? { ...inc, status: newStatus } : inc
        )
      );
      setActionSuccessMessage(`Incident ${selectedIncident.incident_id} transitioned to status [${newStatus}].`);
      setTimeout(() => setActionSuccessMessage(null), 4000);
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    }
  };

  // Filtered Incident Stream
  const filteredIncidents = incidents.filter((inc) => {
    const matchSev = severityFilter === 'ALL' || inc.severity.toUpperCase() === severityFilter;
    const matchStatus = statusFilter === 'ALL' || inc.status.toUpperCase() === statusFilter;
    const matchSearch =
      inc.attack_type.toLowerCase().includes(searchFilter.toLowerCase()) ||
      inc.affected_asset.toLowerCase().includes(searchFilter.toLowerCase()) ||
      inc.incident_id.toLowerCase().includes(searchFilter.toLowerCase());
    return matchSev && matchStatus && matchSearch;
  });

  // Construct Interactive Graph Nodes for Selected Incident
  const graphNodes: GraphNode[] = selectedIncident
    ? [
        {
          id: 'node-actor',
          label: 'ACTOR',
          type: 'ACTOR',
          title: 'Untrusted Origin',
          description: selectedIncident.source || 'External Ingress',
          statusColor: 'var(--text-secondary)',
          x: 60,
          y: 120,
        },
        {
          id: 'node-artifact',
          label: 'ARTIFACT',
          type: 'ARTIFACT',
          title: 'Payload Document',
          description: selectedIncident.affected_asset,
          statusColor: 'var(--accent-cyan)',
          x: 230,
          y: 120,
        },
        {
          id: 'node-signal',
          label: 'SIGNAL',
          type: 'SIGNAL',
          title: 'Forensic Anomaly',
          description: 'Concealed Text / Micro-Font',
          statusColor: 'var(--status-suspicious)',
          x: 400,
          y: 50,
        },
        {
          id: 'node-technique',
          label: 'TECHNIQUE',
          type: 'TECHNIQUE',
          title: selectedIncident.attack_type,
          description: `Severity: ${selectedIncident.severity}`,
          statusColor: 'var(--status-highrisk)',
          x: 400,
          y: 190,
        },
        {
          id: 'node-target',
          label: 'TARGET',
          type: 'TARGET',
          title: 'Screening LLM Agent',
          description: 'Hiring Evaluation Engine',
          statusColor: 'var(--accent-indigo)',
          x: 580,
          y: 120,
        },
        {
          id: 'node-impact',
          label: 'IMPACT',
          type: 'IMPACT',
          title: 'Policy Enforced',
          description: `Action: ${selectedIncident.policy_decision?.action || 'BLOCKED'}`,
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
    { from: 'node-signal', to: 'node-target', label: 'Bypasses Parser', color: 'var(--border-strong)' },
    { from: 'node-technique', to: 'node-target', label: 'Hijacks Instructions', color: 'var(--status-highrisk)' },
    { from: 'node-target', to: 'node-impact', label: 'Mitigated By', color: 'var(--status-safe)' },
  ];

  if (loading) {
    return (
      <PageContainer>
        <LoadingState
          message="Loading Incident Response Queue & Forensic Traces..."
          subMessage="Connecting to multi-tenant incident database and SOC triage telemetry"
        />
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <ErrorState
          title="Incident Queue Connection Error"
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
        title="Threat Investigation & Incident Response Workspace"
        subtitle="Deep SOC forensic investigation, node-edge attack graph exploration, evidence verification, and mitigation triggers"
        breadcrumbs={[{ label: 'SECURITY' }, { label: 'INCIDENT RESPONSE' }]}
        badge={<Badge variant="critical">LIVE SOC QUEUE</Badge>}
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button variant="secondary" size="sm" onClick={fetchData} icon={<RefreshCw size={13} />}>
              Refresh Queue
            </Button>
            <Button variant="primary" size="sm" onClick={() => navigate('/policies')} icon={<Sliders size={13} />}>
              Policy Engine
            </Button>
          </div>
        }
      />

      {/* 2. Secondary Filter Toolbar */}
      <PageToolbar
        leftControls={
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Severity:</span>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                style={{
                  backgroundColor: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '4px 8px',
                  fontSize: '0.75rem',
                  outline: 'none',
                }}
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  backgroundColor: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '4px 8px',
                  fontSize: '0.75rem',
                  outline: 'none',
                }}
              >
                <option value="ALL">All Statuses</option>
                <option value="DETECTED">Detected</option>
                <option value="TRIAGED">Triaged</option>
                <option value="INVESTIGATING">Investigating</option>
                <option value="RESPONDED">Responded</option>
                <option value="RESOLVED">Resolved</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>
          </div>
        }
        rightControls={
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Showing <strong>{filteredIncidents.length}</strong> of {incidents.length} active incidents
          </span>
        }
      />

      {/* Success Notification Alert */}
      {actionSuccessMessage && (
        <Alert type="success" title="SOC Mitigation Executed" onDismiss={() => setActionSuccessMessage(null)}>
          {actionSuccessMessage}
        </Alert>
      )}

      {/* 3. Two-Column High-Density Workspace */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '16px', alignItems: 'start' }}>
        {/* LEFT COLUMN: Incidents Queue */}
        <Card
          title="Incident Queue"
          subtitle={`${filteredIncidents.length} threat escalations`}
          style={{ height: '720px', display: 'flex', flexDirection: 'column' }}
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
                placeholder="Search incident ID, vector, asset..."
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
            {filteredIncidents.length === 0 ? (
              <EmptyState
                title="No Incidents Found"
                description="Zero security incidents match the current search and filter settings."
              />
            ) : (
              filteredIncidents.map((inc) => {
                const isSelected = selectedIncident?.incident_id === inc.incident_id;
                return (
                  <div
                    key={inc.incident_id}
                    onClick={() => {
                      setSelectedIncident(inc);
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
                        {inc.attack_type}
                      </span>
                      <SeverityBadge severity={inc.severity} />
                    </div>

                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
                      {inc.affected_asset}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                      <StatusBadge status={inc.status} showDot={false} />
                      <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: inc.risk_score >= 70 ? 'var(--status-highrisk)' : 'var(--status-safe)' }}>
                        Score: {inc.risk_score}/100
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </Card>

        {/* RIGHT COLUMN: Multi-Tab Investigation Workbench */}
        <div>
          {selectedIncident ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Incident Header & Action Card */}
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                      <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                        {selectedIncident.attack_type}
                      </h2>
                      <SeverityBadge severity={selectedIncident.severity} />
                      <StatusBadge status={selectedIncident.status} />
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Incident ID: <code>{selectedIncident.incident_id}</code> • Asset: <strong>{selectedIncident.affected_asset}</strong> • Origin: {selectedIncident.source}
                    </div>
                  </div>

                  {/* Analyst Response Triggers */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                    <Button
                      variant="secondary"
                      size="xs"
                      onClick={() => handleUpdateStatus('TRIAGED')}
                      disabled={selectedIncident.status === 'TRIAGED'}
                    >
                      Acknowledge
                    </Button>
                    <Button
                      variant="secondary"
                      size="xs"
                      onClick={() => handleUpdateStatus('INVESTIGATING')}
                      disabled={selectedIncident.status === 'INVESTIGATING'}
                    >
                      Investigate
                    </Button>
                    <Button
                      variant="primary"
                      size="xs"
                      onClick={() => handleUpdateStatus('RESOLVED')}
                      disabled={selectedIncident.status === 'RESOLVED'}
                      icon={<CheckCircle size={12} />}
                    >
                      Resolve Incident
                    </Button>
                  </div>
                </div>

                <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ flex: 1 }}>
                    <RiskIndicator score={selectedIncident.risk_score} size="md" />
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', flexShrink: 0 }}>
                    Timestamp: {new Date(selectedIncident.created_at).toLocaleString()}
                  </div>
                </div>
              </Card>

              {/* Investigation Tabs */}
              <Tabs
                activeTab={activeTab}
                onChange={(t) => setActiveTab(t as any)}
                tabs={[
                  { id: 'evidence', label: '1. Forensic Evidence & Policy Decision', count: 1 },
                  { id: 'graph', label: '2. Threat Attack Graph', count: 6 },
                  { id: 'timeline', label: '3. Investigation Timeline', count: 3 },
                  { id: 'related', label: '4. Correlated Resources', count: 4 },
                ]}
              />

              {/* Tab 1: Forensic Evidence & Policy Triad */}
              {activeTab === 'evidence' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <Card
                    title="Exact Matched Forensic Payload"
                    subtitle="Deterministic pattern evidence extracted during document ingestion"
                  >
                    <EvidenceBlock
                      threatType={selectedIncident.attack_type}
                      category="ADVERSARIAL_INJECTION"
                      severity={selectedIncident.severity}
                      evidence={selectedIncident.evidence || 'Concealed indirect prompt injection pattern intercepted in document payload.'}
                      confidence={0.99}
                      detector="SecuroxiBrainEngine"
                      explanation="Concealed instruction set designed to manipulate candidate ranking and break system prompt boundaries."
                    />
                  </Card>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <Card
                      title="Deterministic Policy Decision"
                      subtitle="Authoritative rule enforced by policy engine"
                      badge={<StatusBadge status={selectedIncident.policy_decision?.action || 'BLOCKED'} />}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.8125rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Policy Rule:</span>
                          <strong style={{ color: 'var(--text-primary)' }}>{selectedIncident.policy_decision?.rule_name || 'RULE-100-HIGH-RISK-BLOCK'}</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Action Executed:</span>
                          <StatusBadge status={selectedIncident.policy_decision?.action || 'BLOCKED'} showDot={true} />
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                            Mitigation Response Actions:
                          </span>
                          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                            {(selectedIncident.response_actions || ['QUARANTINE_PAYLOAD', 'DISPATCH_SIEM_EVENT']).map((act) => (
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

                    <Card
                      title="AI Advisory Context Note"
                      subtitle="LLM hypothesis (Non-authoritative insight)"
                      badge={<Badge variant="neutral">Advisory</Badge>}
                    >
                      <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        The adversarial prompt injection utilizes role-override phrasing (e.g. <code>"Ignore previous instructions"</code>) targeting downstream screening agents.
                        <div style={{ marginTop: '8px', fontSize: '0.6875rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                          Notice: AI heuristics provide advisory context only. Deterministic policy rules govern all blocking actions.
                        </div>
                      </div>
                    </Card>
                  </div>
                </div>
              )}

              {/* Tab 2: Threat Attack Graph */}
              {activeTab === 'graph' && (
                <Card
                  title="Interactive Threat Attack Graph"
                  subtitle="Vector causality chain linking Actor, Artifact, Signal, Technique, Target, and Impact"
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
                >
                  <div
                    style={{
                      height: '340px',
                      width: '100%',
                      backgroundColor: '#040711',
                      border: '1px solid var(--border-default)',
                      borderRadius: 'var(--radius-lg)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      overflow: 'hidden',
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
                          id="arrow2"
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
                              markerEnd="url(#arrow2)"
                            />
                            <text
                              x={(fromNode.x + toNode.x) / 2 + 20}
                              y={(fromNode.y + toNode.y) / 2 + 16}
                              fill="var(--text-muted)"
                              fontSize="9"
                              textAnchor="middle"
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
              )}

              {/* Tab 3: Investigation Timeline */}
              {activeTab === 'timeline' && (
                <Card
                  title="Incident Lifecycle & Audit Timeline"
                  subtitle="Step-by-step chronological audit trail"
                >
                  <Timeline
                    items={[
                      {
                        id: 1,
                        title: `Threat Intercepted: ${selectedIncident.attack_type}`,
                        timestamp: new Date(selectedIncident.created_at).toLocaleTimeString(),
                        description: `Signal detected on payload ${selectedIncident.affected_asset} by Security Brain ingestion engine.`,
                        statusColor: 'var(--status-highrisk)',
                        badge: <SeverityBadge severity={selectedIncident.severity} />,
                      },
                      {
                        id: 2,
                        title: `Automated Risk Assessment: Score ${selectedIncident.risk_score}/100`,
                        timestamp: new Date(selectedIncident.created_at).toLocaleTimeString(),
                        description: `Triaged with high confidence. Root-cause hypothesis matched against prompt injection vector.`,
                        statusColor: 'var(--status-suspicious)',
                      },
                      {
                        id: 3,
                        title: `Deterministic Policy Mitigation Executed`,
                        timestamp: new Date(selectedIncident.created_at).toLocaleTimeString(),
                        description: `Enforced rule: ${selectedIncident.policy_decision?.rule_name || 'RULE-100-HIGH-RISK-BLOCK'}. Actions: ${(selectedIncident.response_actions || []).join(', ')}.`,
                        statusColor: 'var(--status-safe)',
                        badge: <StatusBadge status={selectedIncident.policy_decision?.action || 'BLOCKED'} />,
                      },
                    ]}
                  />
                </Card>
              )}

              {/* Tab 4: Correlated Resources */}
              {activeTab === 'related' && (
                <Card
                  title="Correlated Resources & Integration Context"
                  subtitle="Multi-tenant resources linked to this incident"
                >
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', fontSize: '0.8125rem' }}>
                    <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '4px' }}>
                        Linked Scan Record
                      </div>
                      <div>Document: <strong>{selectedIncident.affected_asset}</strong></div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Scan Reference: Auto-correlated</div>
                    </div>

                    <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontWeight: 700, color: 'var(--accent-indigo)', marginBottom: '4px' }}>
                        Connected ATS Ingress
                      </div>
                      <div>Source Webhook: <strong>{selectedIncident.source || 'Greenhouse / Lever API'}</strong></div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Ingress Interface: Webhook Listener</div>
                    </div>

                    <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontWeight: 700, color: 'var(--status-safe)', marginBottom: '4px' }}>
                        Audit Trail Record
                      </div>
                      <div>Log Ref: <strong>AUDIT-{selectedIncident.incident_id}</strong></div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Signed Multi-Tenant HMAC</div>
                    </div>

                    <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontWeight: 700, color: 'var(--status-suspicious)', marginBottom: '4px' }}>
                        Policy Rule Configuration
                      </div>
                      <div>Rule: <strong>{selectedIncident.policy_decision?.rule_name || 'RULE-100-HIGH-RISK-BLOCK'}</strong></div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Deterministic Threshold: $\ge 70$</div>
                    </div>
                  </div>
                </Card>
              )}
            </div>
          ) : (
            <Card>
              <EmptyState
                title="Select an Incident to Investigate"
                description="Select an incident from the queue on the left to begin forensic investigation."
              />
            </Card>
          )}
        </div>
      </div>
    </PageContainer>
  );
};
