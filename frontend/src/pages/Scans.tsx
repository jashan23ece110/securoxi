import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { ScanReport } from '../api/types';
import {
  Card,
  StatCard,
  Button,
  IconButton,
  StatusBadge,
  SeverityBadge,
  VerdictBadge,
  DataTable,
  Tabs,
  Drawer,
  LoadingState,
  EmptyState,
  ErrorState,
  EvidenceBlock,
  RiskIndicator,
  Alert,
  Badge,
} from '../components/ui';
import { ForensicDocumentViewer } from '../components/forensics';
import { PageHeader, PageToolbar, PageContainer } from '../components/layout';
import {
  FileSearch,
  UploadCloud,
  FileText,
  ShieldAlert,
  ShieldCheck,
  Zap,
  RefreshCw,
  Search,
  Sliders,
  CheckCircle,
  AlertTriangle,
  ExternalLink,
  Layers,
  Cpu,
  Eye,
  EyeOff,
  Clock,
  Sparkles,
  Crosshair,
} from 'lucide-react';

export const ScansPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [scans, setScans] = useState<ScanReport[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedScan, setSelectedScan] = useState<ScanReport | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [scanSuccessMessage, setScanSuccessMessage] = useState<string | null>(null);

  // Forensic Document Viewer states
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [viewerFindingId, setViewerFindingId] = useState<string | null>(null);
  const [pdfBuffer, setPdfBuffer] = useState<ArrayBuffer | null>(null);

  const [activeTab, setActiveTab] = useState<'upload' | 'history' | 'queue'>('history');
  const [searchFilter, setSearchFilter] = useState('');
  const [formatFilter, setFormatFilter] = useState('ALL');
  const [verdictFilter, setVerdictFilter] = useState('ALL');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchScans = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listScans();
      setScans(data);
      if (data.length > 0 && !selectedScan) {
        setSelectedScan(data[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch document scans.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files);
      setSelectedFiles((prev) => [...prev, ...files]);
      setUploadError(null);
      const firstPdf = files.find((f) => f.name.toLowerCase().endsWith('.pdf'));
      if (firstPdf) {
        firstPdf.arrayBuffer().then((buf) => setPdfBuffer(buf)).catch(() => setPdfBuffer(null));
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...files]);
      setUploadError(null);
      const firstPdf = files.find((f) => f.name.toLowerCase().endsWith('.pdf'));
      if (firstPdf) {
        firstPdf.arrayBuffer().then((buf) => setPdfBuffer(buf)).catch(() => setPdfBuffer(null));
      }
    }
  };

  const handleUploadAndScan = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadProgress(20);
    setUploadError(null);

    const progressTimer = setInterval(() => {
      setUploadProgress((p) => (p < 90 ? p + 20 : p));
    }, 150);

    try {
      const newReports: ScanReport[] = [];
      for (const file of selectedFiles) {
        const report = await api.uploadAndScanDocument(file);
        newReports.push(report);
      }
      clearInterval(progressTimer);
      setUploadProgress(100);

      setScans((prev) => [...newReports, ...prev]);
      if (newReports.length > 0) {
        setSelectedScan(newReports[0]);
      }
      setSelectedFiles([]);
      setScanSuccessMessage(`Successfully scanned ${newReports.length} document${newReports.length > 1 ? 's' : ''}.`);
      setTimeout(() => setScanSuccessMessage(null), 5000);
    } catch (err: any) {
      clearInterval(progressTimer);
      setUploadError(err.message || 'Document security scan failed.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // Metrics Aggregation
  const totalScans = scans.length;
  const safeScans = scans.filter((s) => s.verdict === 'SAFE').length;
  const suspiciousScans = scans.filter((s) => s.verdict === 'SUSPICIOUS').length;
  const highRiskScans = scans.filter((s) => s.verdict === 'HIGH_RISK' || s.verdict === 'CRITICAL').length;
  const uninspectableScans = scans.filter((s) => (s.verdict as string) === 'UNINSPECTABLE').length;
  const cleanRate = totalScans > 0 ? Math.round((safeScans / totalScans) * 1000) / 10 : 100;

  // Filtered Scans
  const filteredScans = scans.filter((s) => {
    const matchSearch =
      s.filename.toLowerCase().includes(searchFilter.toLowerCase()) ||
      s.scan_id.toLowerCase().includes(searchFilter.toLowerCase());
    const matchFormat = formatFilter === 'ALL' || s.document_type.toUpperCase() === formatFilter;
    const matchVerdict = verdictFilter === 'ALL' || s.verdict.toUpperCase() === verdictFilter;
    return matchSearch && matchFormat && matchVerdict;
  });

  const scanColumns = [
    { key: 'scan_id', header: 'Scan ID', width: '110px', sortable: true },
    {
      key: 'filename',
      header: 'Document Name',
      sortable: true,
      render: (row: ScanReport) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={14} style={{ color: 'var(--accent-cyan)' }} />
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{row.filename}</span>
        </div>
      ),
    },
    {
      key: 'document_type',
      header: 'Format',
      width: '90px',
      render: (row: ScanReport) => (
        <span style={{ fontSize: '0.6875rem', fontWeight: 700, padding: '2px 6px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', textTransform: 'uppercase' }}>
          {row.document_type}
        </span>
      ),
    },
    {
      key: 'verdict',
      header: 'Verdict',
      width: '130px',
      sortable: true,
      render: (row: ScanReport) => <VerdictBadge verdict={row.verdict} />,
    },
    {
      key: 'risk_score',
      header: 'Risk Score',
      width: '140px',
      sortable: true,
      render: (row: ScanReport) => (
        <div style={{ width: '100%' }}>
          <RiskIndicator score={row.risk_score} size="sm" showLabel={false} />
        </div>
      ),
    },
    {
      key: 'findings_count',
      header: 'Findings',
      width: '90px',
      render: (row: ScanReport) => (
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: row.findings?.length > 0 ? 'var(--status-highrisk)' : 'var(--text-muted)' }}>
          {row.findings?.length || 0}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      width: '110px',
      render: (row: ScanReport) => (
        <Button
          variant="secondary"
          size="xs"
          onClick={() => setSelectedScan(row)}
          icon={<ExternalLink size={12} />}
        >
          Inspect
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <PageContainer>
        <LoadingState
          message="Connecting to Layout-Aware PDF Scanner & Ingestion Pipeline..."
          subMessage="Fetching scan history, OCR quarantine status, and multi-format evidence traces"
        />
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <ErrorState title="Scan Center Connection Interrupted" message={error} onRetry={fetchScans} />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      {/* 1. Page Header */}
      <PageHeader
        title="Document Security & Multi-Format Scan Center"
        subtitle="High-throughput layout parser, OCR image-quarantine pipeline, and deep forensic span extraction"
        breadcrumbs={[{ label: 'DOCUMENTS' }, { label: 'SCAN CONSOLE' }]}
        badge={<Badge variant="safe">Multi-Format Scanner Ready</Badge>}
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button variant="secondary" size="sm" onClick={fetchScans} icon={<RefreshCw size={13} />}>
              Refresh Scans
            </Button>
            <Button variant="primary" size="sm" onClick={() => fileInputRef.current?.click()} icon={<UploadCloud size={14} />}>
              Upload Document
            </Button>
          </div>
        }
      />

      {/* 2. Top Summary KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '14px',
          marginBottom: '18px',
        }}
      >
        <StatCard
          label="Total Documents Evaluated"
          value={totalScans}
          icon={<FileSearch size={18} />}
          subtitle="Multi-format parsed"
        />
        <StatCard
          label="Verified Clean Documents"
          value={safeScans}
          delta={`${cleanRate}% rate`}
          deltaType="positive"
          icon={<ShieldCheck size={18} />}
          statusBadge={<StatusBadge status="SAFE" />}
        />
        <StatCard
          label="Suspicious Text & Styling"
          value={suspiciousScans}
          deltaType="neutral"
          icon={<AlertTriangle size={18} />}
          statusBadge={<StatusBadge status="SUSPICIOUS" />}
        />
        <StatCard
          label="High Risk & Blocked"
          value={highRiskScans}
          deltaType={highRiskScans > 0 ? 'negative' : 'positive'}
          icon={<ShieldAlert size={18} />}
          statusBadge={highRiskScans > 0 ? <StatusBadge status="HIGH_RISK" /> : <StatusBadge status="SAFE" />}
        />
        <StatCard
          label="OCR-Quarantined Files"
          value={uninspectableScans}
          icon={<EyeOff size={18} />}
          subtitle="Uninspectable raster"
          statusBadge={<StatusBadge status="UNINSPECTABLE" />}
        />
      </div>

      {/* Success Notification Alert */}
      {scanSuccessMessage && (
        <Alert type="success" title="Security Scan Completed" onDismiss={() => setScanSuccessMessage(null)}>
          {scanSuccessMessage}
        </Alert>
      )}

      {/* 3. Drag-and-Drop Ingestion Workbench */}
      <Card
        title="Ingest Payload for On-Demand Forensic Analysis"
        subtitle="Supports PDF, DOCX, TXT, HTML, PNG, JPG/JPEG formats & compressed bulk archives"
        style={{ marginBottom: '18px' }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${isDragging ? 'var(--accent-cyan)' : 'var(--border-default)'}`,
              borderRadius: 'var(--radius-lg)',
              padding: '28px',
              textAlign: 'center',
              backgroundColor: isDragging ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            <UploadCloud
              size={36}
              style={{
                color: isDragging ? 'var(--accent-cyan)' : 'var(--text-muted)',
                marginBottom: '8px',
                margin: '0 auto 8px auto',
              }}
            />
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.9375rem', marginBottom: '4px' }}>
              Drag & Drop file payload here, or browse local workspace
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
              Max size: 25MB per document • Bulk archives up to 100MB uncompressed
            </div>

            {/* Supported Formats Pills */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', flexWrap: 'wrap' }}>
              {['PDF', 'DOCX', 'TXT', 'HTML', 'PNG', 'JPG / JPEG', 'ZIP'].map((fmt) => (
                <span
                  key={fmt}
                  style={{
                    fontSize: '0.6875rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-xs)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  {fmt}
                </span>
              ))}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.html,.png,.jpg,.jpeg,.zip"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
          </div>

          {/* Selected Files Stage Bar */}
          {selectedFiles.length > 0 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                padding: '14px 16px',
                backgroundColor: 'var(--bg-surface-elevated)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--accent-cyan)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
                  Selected Payload Queue ({selectedFiles.length} {selectedFiles.length === 1 ? 'file' : 'files'})
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Button variant="ghost" size="xs" onClick={() => setSelectedFiles([])} disabled={isUploading}>
                    Clear All
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    isLoading={isUploading}
                    onClick={handleUploadAndScan}
                    icon={<Zap size={14} />}
                  >
                    {isUploading ? `Scanning (${uploadProgress}%)...` : `Scan ${selectedFiles.length} File${selectedFiles.length > 1 ? 's' : ''}`}
                  </Button>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '180px', overflowY: 'auto' }}>
                {selectedFiles.map((file, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      backgroundColor: 'var(--bg-app)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <FileText size={15} style={{ color: 'var(--accent-cyan)' }} />
                      <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {file.name}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {(file.size / 1024).toFixed(1)} KB
                      </span>
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={() => setSelectedFiles((prev) => prev.filter((_, i) => i !== idx))}
                        disabled={isUploading}
                      >
                        ✕
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {uploadError && <Alert type="danger" title="Scan Ingestion Failure">{uploadError}</Alert>}
        </div>
      </Card>

      {/* 4. Filter Toolbar & Scan History DataTable */}
      <PageToolbar
        leftControls={
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Search size={13} style={{ color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search scans by filename or scan ID..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                style={{
                  backgroundColor: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  outline: 'none',
                  minWidth: '240px',
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Format:</span>
              <select
                value={formatFilter}
                onChange={(e) => setFormatFilter(e.target.value)}
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
                <option value="ALL">All Formats</option>
                <option value="PDF">PDF</option>
                <option value="DOCX">DOCX</option>
                <option value="TXT">TXT</option>
                <option value="HTML">HTML</option>
                <option value="PNG">PNG (OCR)</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Verdict:</span>
              <select
                value={verdictFilter}
                onChange={(e) => setVerdictFilter(e.target.value)}
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
                <option value="ALL">All Verdicts</option>
                <option value="SAFE">Safe</option>
                <option value="SUSPICIOUS">Suspicious</option>
                <option value="HIGH_RISK">High Risk</option>
                <option value="BLOCKED">Blocked</option>
                <option value="UNINSPECTABLE">Uninspectable</option>
              </select>
            </div>
          </div>
        }
        rightControls={
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Showing <strong>{filteredScans.length}</strong> of {scans.length} records
          </span>
        }
      />

      <Card
        title="Evaluated Document History"
        subtitle="Real-time multi-tenant scan records and forensic detections"
      >
        <DataTable
          columns={scanColumns}
          data={filteredScans}
          keyExtractor={(row) => row.scan_id}
          emptyTitle="No Scan Telemetry Available"
          emptyDescription="Upload a document above to generate security scan records."
          pageSize={8}
        />
      </Card>

      {/* 5. Deep Forensic Inspection Drawer */}
      <Drawer
        isOpen={selectedScan !== null}
        onClose={() => setSelectedScan(null)}
        title="Document Security Assessment"
        subtitle={`Scan ID: ${selectedScan?.scan_id || ''} • File: ${selectedScan?.filename || ''}`}
        badge={selectedScan ? <VerdictBadge verdict={selectedScan.verdict} /> : undefined}
        footer={
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <Button variant="secondary" onClick={() => setSelectedScan(null)}>
              Close Drawer
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                setViewerFindingId(null);
                setIsViewerOpen(true);
              }}
              icon={<Eye size={14} />}
            >
              Inspect on Document
            </Button>
            <Button variant="outline" onClick={() => navigate('/security-brain')}>
              Open in Security Brain
            </Button>
          </div>
        }
      >
        {selectedScan && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* UNINSPECTABLE Warning if applicable */}
            {(selectedScan.verdict as string) === 'UNINSPECTABLE' && (
              <Alert type="warning" title="Raster / Scanned Image Payload Quarantined">
                This document is a rasterized image-only file with zero extractable text streams. It has been quarantined and routed to the OCR Sandbox. <strong>UNINSPECTABLE is never treated as SAFE.</strong>
              </Alert>
            )}

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'block' }}>
                Calibrated Document Risk Gauge
              </span>
              <RiskIndicator score={selectedScan.risk_score} size="lg" />
            </div>

            {/* Meta Attributes Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.8125rem' }}>
              <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>DOCUMENT FORMAT</span>
                <div style={{ fontWeight: 700, textTransform: 'uppercase' }}>{selectedScan.document_type}</div>
              </div>
              <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>TIMESTAMP</span>
                <div style={{ fontWeight: 600, fontSize: '0.75rem' }}>{new Date(selectedScan.created_at).toLocaleString()}</div>
              </div>
            </div>

            {/* Assessment Summary */}
            <div style={{ padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)', fontSize: '0.8125rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '4px', color: 'var(--text-primary)' }}>
                Assessment Summary
              </div>
              <div style={{ color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {selectedScan.summary || 'Document evaluated cleanly against deterministic injection, font-concealment, and structural rules.'}
              </div>
            </div>

            {/* Extracted Findings & Evidence */}
            {selectedScan.findings && selectedScan.findings.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Extracted Forensic Findings ({selectedScan.findings.length})
                  </span>
                  <Button
                    variant="outline"
                    size="xs"
                    onClick={() => {
                      setViewerFindingId(null);
                      setIsViewerOpen(true);
                    }}
                    icon={<Crosshair size={12} />}
                  >
                    View All on Document
                  </Button>
                </div>
                {selectedScan.findings.map((f, i) => (
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <EvidenceBlock
                      threatType={f.threat_type}
                      category={f.category}
                      severity={f.severity}
                      confidence={f.confidence}
                      evidence={f.evidence}
                      explanation={f.description}
                      location={f.line_number ? `Line ${f.line_number}` : 'Layout Span [72.0, 140.5, 540.0, 148.0]'}
                    />
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '-4px' }}>
                      <Button
                        variant="secondary"
                        size="xs"
                        onClick={() => {
                          setViewerFindingId((f as any).finding_id || `FINDING-${i + 1}`);
                          setIsViewerOpen(true);
                        }}
                        icon={<Eye size={12} />}
                      >
                        Highlight on Document Page
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <Alert type="success" title="Clean Verification">
                Zero malicious prompt injections, visual deceptions, or structural anomalies detected.
              </Alert>
            )}
          </div>
        )}
      </Drawer>

      {/* 6. Forensic Document Viewer Overlay */}
      {selectedScan && (
        <ForensicDocumentViewer
          isOpen={isViewerOpen}
          onClose={() => setIsViewerOpen(false)}
          filename={selectedScan.filename}
          documentType={selectedScan.document_type}
          verdict={selectedScan.verdict}
          riskScore={selectedScan.risk_score}
          findings={selectedScan.findings || []}
          pdfData={pdfBuffer}
          selectedFindingId={viewerFindingId}
          onOpenSecurityBrain={() => {
            setIsViewerOpen(false);
            navigate('/security-brain');
          }}
        />
      )}
    </PageContainer>
  );
};
