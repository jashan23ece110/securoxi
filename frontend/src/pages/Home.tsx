import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { ScanReport, Incident, RAGAnswer } from '../api/types';
import {
  Card,
  StatCard,
  Button,
  StatusBadge,
  SeverityBadge,
  VerdictBadge,
  Badge,
  Alert,
  Modal,
  RiskIndicator,
  LoadingState,
  EmptyState,
  ErrorState,
} from '../components/ui';
import { ForensicDocumentViewer } from '../components/forensics';
import { PageContainer } from '../components/layout';
import {
  FileSearch,
  FolderArchive,
  MessageSquare,
  UserCheck,
  Shield,
  ShieldAlert,
  ShieldCheck,
  ArrowRight,
  UploadCloud,
  CheckCircle2,
  Clock,
  ExternalLink,
  Sparkles,
  Zap,
  AlertTriangle,
  Eye,
  FileText,
  Search,
  Check,
  HelpCircle,
} from 'lucide-react';

interface FileQueueItem {
  file: File;
  id: string;
  name: string;
  sizeFormatted: string;
  status: 'READY' | 'UPLOADING' | 'PROCESSING' | 'COMPLETE' | 'FAILED';
  report?: ScanReport;
  error?: string;
}

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  // Data states
  const [scans, setScans] = useState<ScanReport[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Universal Scan Workflow states
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [fileQueue, setFileQueue] = useState<FileQueueItem[]>([]);
  const [activeScanIndex, setActiveScanIndex] = useState<number>(0);
  const [scanStep, setScanStep] = useState<'idle' | 'validating' | 'parsing' | 'analyzing' | 'evaluating' | 'complete'>('idle');
  const [isScanning, setIsScanning] = useState(false);

  // Ask SECUROXI states
  const [isAskModalOpen, setIsAskModalOpen] = useState(false);
  const [askQuery, setAskQuery] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [askResult, setAskResult] = useState<RAGAnswer | null>(null);
  const [askError, setAskError] = useState<string | null>(null);

  // Forensic Document Viewer states
  const [viewerDoc, setViewerDoc] = useState<ScanReport | null>(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [pdfBuffer, setPdfBuffer] = useState<ArrayBuffer | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [scansData, incidentsData] = await Promise.all([
        api.listScans().catch(() => []),
        api.listIncidents().catch(() => []),
      ]);
      setScans(scansData);
      setIncidents(incidentsData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch recent security activity.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Handle files selected for Universal Scan
  const handleFilesSelected = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const newItems: FileQueueItem[] = Array.from(files).map((f) => ({
      file: f,
      id: `FILE-${Math.random().toString(36).substring(2, 9)}`,
      name: f.name,
      sizeFormatted: formatFileSize(f.size),
      status: 'READY',
    }));
    setFileQueue((prev) => [...prev, ...newItems]);
    setIsScanModalOpen(true);
  };

  // Start Universal Multi-file Scan
  const handleStartScan = async () => {
    if (fileQueue.length === 0) return;
    setIsScanning(true);

    const updatedQueue = [...fileQueue];

    for (let i = 0; i < updatedQueue.length; i++) {
      const item = updatedQueue[i];
      if (item.status === 'COMPLETE') continue;

      setActiveScanIndex(i);
      item.status = 'UPLOADING';
      setScanStep('validating');
      setFileQueue([...updatedQueue]);

      await new Promise((r) => setTimeout(r, 200));
      setScanStep('parsing');

      await new Promise((r) => setTimeout(r, 300));
      setScanStep('analyzing');

      try {
        if (item.file.name.toLowerCase().endsWith('.pdf')) {
          item.file.arrayBuffer().then((buf) => setPdfBuffer(buf)).catch(() => {});
        }

        const report = await api.uploadAndScanDocument(item.file);
        setScanStep('evaluating');
        await new Promise((r) => setTimeout(r, 200));

        item.status = 'COMPLETE';
        item.report = report;
        setScans((prev) => [report, ...prev]);
      } catch (err: any) {
        item.status = 'FAILED';
        item.error = err.message || 'Scan failed';
      }

      setFileQueue([...updatedQueue]);
    }

    setScanStep('complete');
    setIsScanning(false);
  };

  // Ask SECUROXI Q&A
  const handleAskSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!askQuery.trim()) return;

    setIsAsking(true);
    setAskError(null);
    setAskResult(null);

    try {
      const res = await api.askSecuroxi(askQuery);
      setAskResult(res);
    } catch (err: any) {
      setAskError(err.message || 'Unable to retrieve answer.');
    } finally {
      setIsAsking(false);
    }
  };

  // Open forensic evidence for a scan
  const handleInspectScan = (scan: ScanReport) => {
    setViewerDoc(scan);
    setIsViewerOpen(true);
  };

  // Aggregate stats
  const totalScans = scans.length;
  const highRiskCount = scans.filter((s) => s.verdict === 'HIGH_RISK' || s.verdict === 'CRITICAL').length;
  const suspiciousCount = scans.filter((s) => s.verdict === 'SUSPICIOUS').length;
  const safeCount = scans.filter((s) => s.verdict === 'SAFE').length;
  const latestScan = scans.length > 0 ? scans[0] : null;

  return (
    <PageContainer>
      {/* 1. Welcoming Hero Section */}
      <div
        style={{
          padding: '32px 0 24px 0',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '4px 12px',
            backgroundColor: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-default)',
            borderRadius: '999px',
            fontSize: '0.75rem',
            fontWeight: 700,
            color: 'var(--accent-cyan)',
            marginBottom: '14px',
          }}
        >
          <Sparkles size={14} />
          <span>SECUROXI AI • Enterprise Security Platform</span>
        </div>

        <h1
          style={{
            fontSize: '2.25rem',
            fontWeight: 900,
            letterSpacing: '-0.03em',
            color: 'var(--text-primary)',
            margin: '0 0 8px 0',
          }}
        >
          What would you like to secure today?
        </h1>

        <p
          style={{
            fontSize: '1rem',
            color: 'var(--text-secondary)',
            maxWidth: '560px',
            margin: '0 0 32px 0',
            lineHeight: 1.5,
          }}
        >
          Secure your documents, candidate hiring workflows, and AI pipelines against hidden prompt injection, visual deception, and adversarial overrides.
        </p>

        {/* 2. Four Primary Action Cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '16px',
            width: '100%',
            maxWidth: '1080px',
            textAlign: 'left',
          }}
        >
          {/* Card A: Scan Files */}
          <div
            onClick={() => {
              setFileQueue([]);
              fileInputRef.current?.click();
            }}
            style={{
              padding: '24px 20px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-lg)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              boxShadow: 'var(--shadow-sm)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-cyan)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-default)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(6, 182, 212, 0.12)',
                  border: '1px solid rgba(6, 182, 212, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-cyan)',
                  marginBottom: '16px',
                }}
              >
                <FileSearch size={22} />
              </div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--text-primary)' }}>
                Scan Files
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 16px 0' }}>
                Upload one or more documents to check for prompt injection, micro-text, and hidden instructions.
              </p>
            </div>
            <div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '14px' }}>
                {['PDF', 'DOCX', 'TXT', 'HTML', 'PNG', 'JPG'].map((ext) => (
                  <span
                    key={ext}
                    style={{
                      fontSize: '0.6875rem',
                      fontWeight: 700,
                      padding: '1px 5px',
                      backgroundColor: 'var(--bg-app)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-xs)',
                      color: 'var(--text-muted)',
                    }}
                  >
                    {ext}
                  </span>
                ))}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8125rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                <span>Scan Files</span>
                <ArrowRight size={14} />
              </div>
            </div>
          </div>

          {/* Card B: Scan Folder */}
          <div
            onClick={() => navigate('/scan-folder')}
            style={{
              padding: '24px 20px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-lg)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              boxShadow: 'var(--shadow-sm)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-indigo)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-default)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(99, 102, 241, 0.12)',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-indigo)',
                  marginBottom: '16px',
                }}
              >
                <FolderArchive size={22} />
              </div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--text-primary)' }}>
                Scan Folder / Bulk
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 16px 0' }}>
                Analyze collections of resumes and documents automatically with bulk batch processing.
              </p>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
                Best for large candidate pools
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8125rem', fontWeight: 700, color: 'var(--accent-indigo)' }}>
                <span>Scan Collection</span>
                <ArrowRight size={14} />
              </div>
            </div>
          </div>

          {/* Card C: Ask SECUROXI */}
          <div
            onClick={() => setIsAskModalOpen(true)}
            style={{
              padding: '24px 20px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-lg)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              boxShadow: 'var(--shadow-sm)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-purple)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-default)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(168, 85, 247, 0.12)',
                  border: '1px solid rgba(168, 85, 247, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-purple)',
                  marginBottom: '16px',
                }}
              >
                <MessageSquare size={22} />
              </div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--text-primary)' }}>
                Ask SECUROXI
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 16px 0' }}>
                Ask questions across your document repository with verified evidence citations and prompt injection defense.
              </p>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
                Grounded Q&A
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8125rem', fontWeight: 700, color: 'var(--accent-purple)' }}>
                <span>Ask Question</span>
                <ArrowRight size={14} />
              </div>
            </div>
          </div>

          {/* Card D: Hiring / ATS */}
          <div
            onClick={() => navigate('/screening')}
            style={{
              padding: '24px 20px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-lg)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              boxShadow: 'var(--shadow-sm)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--status-safe)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-default)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--status-safe)',
                  marginBottom: '16px',
                }}
              >
                <UserCheck size={22} />
              </div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--text-primary)' }}>
                Hiring & Screening
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 16px 0' }}>
                Screen applicants and verify candidate qualification with mandatory security clearance gates.
              </p>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
                Applicant Tracking Protection
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8125rem', fontWeight: 700, color: 'var(--status-safe)' }}>
                <span>Open Hiring</span>
                <ArrowRight size={14} />
              </div>
            </div>
          </div>
        </div>

        {/* Hidden File Inputs */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.html,.png,.jpg,.jpeg,.zip"
          style={{ display: 'none' }}
          onChange={(e) => handleFilesSelected(e.target.files)}
        />
        <input
          ref={folderInputRef}
          type="file"
          multiple
          style={{ display: 'none' }}
          onChange={(e) => handleFilesSelected(e.target.files)}
        />
      </div>

      {/* 3. Compact Recent Security Activity */}
      <div style={{ marginTop: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
              Recent Document Activity
            </h2>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
              Real-time scan summaries and threat verdicts across your workspace
            </p>
          </div>
          <Button variant="secondary" size="sm" onClick={() => navigate('/overview')} icon={<ExternalLink size={13} />}>
            Advanced Security Operations
          </Button>
        </div>

        {/* Summary Stats Row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
            marginBottom: '16px',
          }}
        >
          <StatCard
            label="Total Documents Scanned"
            value={totalScans}
            icon={<FileText size={18} />}
          />
          <StatCard
            label="Safe Documents"
            value={safeCount}
            icon={<ShieldCheck size={18} />}
            statusBadge={<StatusBadge status="SAFE" />}
          />
          <StatCard
            label="Suspicious Findings"
            value={suspiciousCount}
            icon={<AlertTriangle size={18} />}
            statusBadge={suspiciousCount > 0 ? <StatusBadge status="SUSPICIOUS" /> : undefined}
          />
          <StatCard
            label="High Risk Intercepted"
            value={highRiskCount}
            icon={<ShieldAlert size={18} />}
            statusBadge={highRiskCount > 0 ? <StatusBadge status="HIGH_RISK" /> : undefined}
          />
        </div>

        {/* Recent Activity Table / List */}
        <Card>
          {scans.length === 0 ? (
            <EmptyState
              title="No Scans Yet"
              description="Start by clicking 'Scan Files' above to evaluate your first document."
              action={
                <Button variant="primary" size="sm" onClick={() => fileInputRef.current?.click()} icon={<FileSearch size={14} />}>
                  Scan a Document
                </Button>
              }
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {scans.slice(0, 5).map((scan) => (
                <div
                  key={scan.scan_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    backgroundColor: 'var(--bg-app)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--bg-surface)',
                        border: '1px solid var(--border-default)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--accent-cyan)',
                      }}
                    >
                      <FileText size={16} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
                        {scan.filename}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Scan ID: <code>{scan.scan_id}</code> • {new Date(scan.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{ textAlign: 'right' }}>
                      <VerdictBadge verdict={scan.verdict} />
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        Risk: {scan.risk_score}/100
                      </div>
                    </div>
                    <Button variant="secondary" size="xs" onClick={() => handleInspectScan(scan)} icon={<Eye size={12} />}>
                      View Evidence
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* 4. Universal Scan Modal Flow */}
      <Modal
        isOpen={isScanModalOpen}
        onClose={() => {
          if (!isScanning) setIsScanModalOpen(false);
        }}
        title="Universal Document Security Scanner"
        footer={
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {fileQueue.length} {fileQueue.length === 1 ? 'file' : 'files'} in queue
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <Button
                variant="secondary"
                onClick={() => setIsScanModalOpen(false)}
                disabled={isScanning}
              >
                {scanStep === 'complete' ? 'Close' : 'Cancel'}
              </Button>
              {scanStep !== 'complete' && (
                <Button
                  variant="primary"
                  onClick={handleStartScan}
                  disabled={isScanning || fileQueue.length === 0}
                  icon={<Zap size={14} />}
                >
                  {isScanning ? 'Scanning...' : 'Start Security Scan'}
                </Button>
              )}
            </div>
          </div>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Friendly Progress Indicator during active scanning */}
          {isScanning && (
            <div
              style={{
                padding: '16px',
                backgroundColor: 'var(--bg-app)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-default)',
              }}
            >
              <div style={{ fontSize: '0.8125rem', fontWeight: 700, marginBottom: '10px', color: 'var(--accent-cyan)' }}>
                Scanning: {fileQueue[activeScanIndex]?.name}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                <span style={{ color: scanStep === 'validating' ? 'var(--accent-cyan)' : 'var(--status-safe)' }}>
                  ✓ 1. Validating
                </span>
                <span style={{ color: scanStep === 'parsing' ? 'var(--accent-cyan)' : scanStep === 'analyzing' || scanStep === 'evaluating' ? 'var(--status-safe)' : 'var(--text-muted)' }}>
                  {scanStep === 'analyzing' || scanStep === 'evaluating' ? '✓' : '•'} 2. Parsing Layout
                </span>
                <span style={{ color: scanStep === 'analyzing' ? 'var(--accent-cyan)' : scanStep === 'evaluating' ? 'var(--status-safe)' : 'var(--text-muted)' }}>
                  {scanStep === 'evaluating' ? '✓' : '•'} 3. Security Analysis
                </span>
                <span style={{ color: scanStep === 'evaluating' ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
                  • 4. Risk Evaluation
                </span>
              </div>
            </div>
          )}

          {/* Queued / Scanned Files List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '280px', overflowY: 'auto' }}>
            {fileQueue.map((item, idx) => (
              <div
                key={item.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  backgroundColor: 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${item.report?.verdict === 'HIGH_RISK' ? 'var(--status-critical-border)' : 'var(--border-subtle)'}`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <FileText size={16} style={{ color: 'var(--accent-cyan)' }} />
                  <div>
                    <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {item.name}
                    </div>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                      {item.sizeFormatted}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  {item.status === 'READY' && <Badge variant="neutral">Ready</Badge>}
                  {item.status === 'UPLOADING' && <Badge variant="info">Uploading...</Badge>}
                  {item.status === 'PROCESSING' && <Badge variant="info">Analyzing...</Badge>}
                  {item.status === 'COMPLETE' && item.report && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <VerdictBadge verdict={item.report.verdict} />
                      <Button
                        variant="secondary"
                        size="xs"
                        onClick={() => {
                          setIsScanModalOpen(false);
                          handleInspectScan(item.report!);
                        }}
                        icon={<Eye size={12} />}
                      >
                        Evidence
                      </Button>
                    </div>
                  )}
                  {item.status === 'FAILED' && <Badge variant="critical">Failed</Badge>}
                </div>
              </div>
            ))}
          </div>

          {/* Add more files button */}
          {!isScanning && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                icon={<UploadCloud size={14} />}
              >
                + Add More Files
              </Button>
            </div>
          )}
        </div>
      </Modal>

      {/* 5. Ask SECUROXI Modal */}
      <Modal
        isOpen={isAskModalOpen}
        onClose={() => setIsAskModalOpen(false)}
        title="Ask SECUROXI — Grounded Document Intelligence"
        footer={
          <Button variant="secondary" onClick={() => setIsAskModalOpen(false)}>
            Close
          </Button>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
            Query your authorized document collection with automatic prompt-injection defense and verified evidence citations.
          </p>

          <form onSubmit={handleAskSubmit} style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              placeholder="e.g. Which candidates have Kubernetes experience?"
              value={askQuery}
              onChange={(e) => setAskQuery(e.target.value)}
              style={{
                flex: 1,
                backgroundColor: 'var(--bg-input)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 12px',
                fontSize: '0.8125rem',
                outline: 'none',
              }}
            />
            <Button variant="primary" type="submit" disabled={isAsking || !askQuery.trim()} icon={<Search size={14} />}>
              {isAsking ? 'Thinking...' : 'Ask'}
            </Button>
          </form>

          {isAsking && <LoadingState message="Searching document repository & validating evidence citations..." />}

          {askError && <Alert type="critical" title="Query Failed">{askError}</Alert>}

          {askResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div
                style={{
                  padding: '14px',
                  backgroundColor: 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '6px' }}>
                  GROUNDED ANSWER
                </div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>
                  {askResult.answer_text}
                </div>
              </div>

              {/* Citations List */}
              {askResult.citations && askResult.citations.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    SUPPORTING CITATIONS ({askResult.citations.length})
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {askResult.citations.map((c) => (
                      <div
                        key={c.citation_id}
                        style={{
                          padding: '8px 12px',
                          backgroundColor: 'var(--bg-app)',
                          borderRadius: 'var(--radius-sm)',
                          border: '1px solid var(--border-subtle)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '0.75rem',
                        }}
                      >
                        <div>
                          <strong>Doc ID:</strong> <code>{c.document_id}</code> • <strong>Page:</strong> {c.page}
                        </div>
                        <Badge variant="info">{Math.round(c.similarity_score * 100)}% Match</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </Modal>

      {/* 6. Forensic Document Viewer Overlay */}
      {viewerDoc && (
        <ForensicDocumentViewer
          isOpen={isViewerOpen}
          onClose={() => setIsViewerOpen(false)}
          filename={viewerDoc.filename}
          documentType={viewerDoc.document_type}
          verdict={viewerDoc.verdict}
          riskScore={viewerDoc.risk_score}
          findings={viewerDoc.findings || []}
          pdfData={pdfBuffer}
          onOpenSecurityBrain={() => {
            setIsViewerOpen(false);
            navigate('/security-brain');
          }}
        />
      )}
    </PageContainer>
  );
};
