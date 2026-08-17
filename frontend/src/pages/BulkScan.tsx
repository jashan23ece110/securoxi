import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { ScanReport } from '../api/types';
import {
  Card,
  StatCard,
  Button,
  StatusBadge,
  SeverityBadge,
  VerdictBadge,
  Badge,
  Alert,
  RiskIndicator,
  LoadingState,
  EmptyState,
  ErrorState,
} from '../components/ui';
import { ForensicDocumentViewer } from '../components/forensics';
import { PageHeader, PageToolbar, PageContainer } from '../components/layout';
import {
  FolderArchive,
  FolderOpen,
  FileText,
  FileCheck,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  EyeOff,
  RefreshCw,
  Zap,
  CheckCircle2,
  XCircle,
  Pause,
  Play,
  RotateCcw,
  ArrowRight,
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  Cpu,
  Layers,
  ExternalLink,
  Eye,
  Search,
  Filter,
} from 'lucide-react';

interface DiscoveredFile {
  file: File;
  id: string;
  name: string;
  relativePath: string;
  size: number;
  sizeFormatted: string;
  extension: string;
  isSupported: boolean;
  isDuplicate: boolean;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  report?: ScanReport;
  error?: string;
}

const SUPPORTED_EXTENSIONS = new Set(['pdf', 'docx', 'txt', 'html', 'png', 'jpg', 'jpeg']);
const DEFAULT_BATCH_SIZE = 5;

export const BulkScanPage: React.FC = () => {
  const navigate = useNavigate();
  const folderInputRef = useRef<HTMLInputElement>(null);

  // Workflow Stages: 'select' -> 'review' -> 'scanning' -> 'complete'
  const [stage, setStage] = useState<'select' | 'review' | 'scanning' | 'complete'>('select');

  // Discovered Files
  const [folderName, setFolderName] = useState<string>('');
  const [discoveredFiles, setDiscoveredFiles] = useState<DiscoveredFile[]>([]);
  const [isDiscovering, setIsDiscovering] = useState(false);

  // Live Scan State
  const [isPaused, setIsPaused] = useState(false);
  const isPausedRef = useRef(false);
  const isCancelledRef = useRef(false);
  const [activeBatchIndex, setActiveBatchIndex] = useState(0);
  const [currentProcessingName, setCurrentProcessingName] = useState<string>('');
  const [showAdvancedTelemetry, setShowAdvancedTelemetry] = useState(false);

  // Results & Filtering
  const [resultFilter, setResultFilter] = useState<'ALL' | 'SAFE' | 'SUSPICIOUS' | 'HIGH_RISK' | 'UNINSPECTABLE' | 'FAILED'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Forensic Viewer State
  const [viewerDoc, setViewerDoc] = useState<ScanReport | null>(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);

  // Helper to format bytes
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Helper to calculate deduplication key
  const getDeduplicationKey = (f: File): string => `${f.name}_${f.size}`;

  // Handle native folder selection via webkitdirectory
  const handleFolderSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;

    setIsDiscovering(true);
    const rawFiles = Array.from(e.target.files);

    // Derive root folder name from the first file's webkitRelativePath
    let inferredFolderName = 'Selected_Directory';
    if (rawFiles[0].webkitRelativePath) {
      const parts = rawFiles[0].webkitRelativePath.split('/');
      if (parts.length > 1) {
        inferredFolderName = parts[0];
      }
    }
    setFolderName(inferredFolderName);

    // Discover, inspect extensions, and identify duplicates
    const seenHashes = new Set<string>();
    const files: DiscoveredFile[] = rawFiles.map((file, idx) => {
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      const isSupported = SUPPORTED_EXTENSIONS.has(ext);
      const hashKey = getDeduplicationKey(file);
      const isDuplicate = isSupported && seenHashes.has(hashKey);

      if (isSupported && !isDuplicate) {
        seenHashes.add(hashKey);
      }

      return {
        file,
        id: `DOC-${idx + 1}`,
        name: file.name,
        relativePath: file.webkitRelativePath || file.name,
        size: file.size,
        sizeFormatted: formatFileSize(file.size),
        extension: ext.toUpperCase(),
        isSupported,
        isDuplicate,
        status: isDuplicate ? 'SKIPPED' : 'PENDING',
      };
    });

    setDiscoveredFiles(files);
    setIsDiscovering(false);
    setStage('review');
  };

  // Start Controlled Memory-Safe Batch Scanning
  const handleStartScan = async () => {
    setStage('scanning');
    setIsPaused(false);
    isPausedRef.current = false;
    isCancelledRef.current = false;

    const supportedFiles = discoveredFiles.filter((f) => f.isSupported && !f.isDuplicate);
    const filesList = [...discoveredFiles];

    for (let i = 0; i < supportedFiles.length; i += DEFAULT_BATCH_SIZE) {
      if (isCancelledRef.current) break;

      // Handle pause loop
      while (isPausedRef.current && !isCancelledRef.current) {
        await new Promise((r) => setTimeout(r, 200));
      }

      const batch = supportedFiles.slice(i, i + DEFAULT_BATCH_SIZE);
      setActiveBatchIndex(Math.floor(i / DEFAULT_BATCH_SIZE) + 1);

      // Mark batch as processing
      batch.forEach((bf) => {
        const target = filesList.find((f) => f.id === bf.id);
        if (target) target.status = 'PROCESSING';
      });
      setCurrentProcessingName(batch.map((b) => b.name).join(', '));
      setDiscoveredFiles([...filesList]);

      // Process batch files concurrently via API
      await Promise.all(
        batch.map(async (discoveredItem) => {
          try {
            const report = await api.uploadAndScanDocument(discoveredItem.file);
            const target = filesList.find((f) => f.id === discoveredItem.id);
            if (target) {
              target.status = 'COMPLETED';
              target.report = report;
            }
          } catch (err: any) {
            const target = filesList.find((f) => f.id === discoveredItem.id);
            if (target) {
              target.status = 'FAILED';
              target.error = err.message || 'Scan failed';
            }
          }
        })
      );

      setDiscoveredFiles([...filesList]);
    }

    setStage('complete');
  };

  // Pause / Resume Toggle
  const handleTogglePause = () => {
    const nextPaused = !isPaused;
    setIsPaused(nextPaused);
    isPausedRef.current = nextPaused;
  };

  // Cancel Scan
  const handleCancelScan = () => {
    isCancelledRef.current = true;
    setIsPaused(false);
    isPausedRef.current = false;
    setStage('complete');
  };

  // Retry Failed Documents
  const handleRetryFailed = async () => {
    const failedItems = discoveredFiles.filter((f) => f.status === 'FAILED');
    if (failedItems.length === 0) return;

    setStage('scanning');
    isCancelledRef.current = false;

    const filesList = [...discoveredFiles];
    for (const item of failedItems) {
      if (isCancelledRef.current) break;
      item.status = 'PROCESSING';
      setCurrentProcessingName(item.name);
      setDiscoveredFiles([...filesList]);

      try {
        const report = await api.uploadAndScanDocument(item.file);
        item.status = 'COMPLETED';
        item.report = report;
        item.error = undefined;
      } catch (err: any) {
        item.status = 'FAILED';
        item.error = err.message || 'Retry failed';
      }
      setDiscoveredFiles([...filesList]);
    }

    setStage('complete');
  };

  // Inspect Result in Forensic Viewer
  const handleInspectResult = (report: ScanReport) => {
    setViewerDoc(report);
    setIsViewerOpen(true);
  };

  // Aggregated Counts
  const totalCount = discoveredFiles.length;
  const supportedCount = discoveredFiles.filter((f) => f.isSupported).length;
  const unsupportedCount = discoveredFiles.filter((f) => !f.isSupported).length;
  const duplicateCount = discoveredFiles.filter((f) => f.isDuplicate).length;

  const completedFiles = discoveredFiles.filter((f) => f.status === 'COMPLETED');
  const failedFiles = discoveredFiles.filter((f) => f.status === 'FAILED');
  const pendingFiles = discoveredFiles.filter((f) => f.status === 'PENDING');
  const processingFiles = discoveredFiles.filter((f) => f.status === 'PROCESSING');

  const safeCount = completedFiles.filter((f) => f.report?.verdict === 'SAFE').length;
  const suspiciousCount = completedFiles.filter((f) => f.report?.verdict === 'SUSPICIOUS').length;
  const highRiskCount = completedFiles.filter((f) => f.report?.verdict === 'HIGH_RISK' || f.report?.verdict === 'CRITICAL').length;
  const uninspectableCount = completedFiles.filter((f) => (f.report?.verdict as string) === 'UNINSPECTABLE').length;

  const totalEligible = supportedCount - duplicateCount;
  const progressPercent = totalEligible > 0 ? Math.round((completedFiles.length / totalEligible) * 100) : 0;

  // Filtered Results for Complete Stage
  const filteredResults = completedFiles.concat(failedFiles).filter((item) => {
    if (resultFilter === 'SAFE' && item.report?.verdict !== 'SAFE') return false;
    if (resultFilter === 'SUSPICIOUS' && item.report?.verdict !== 'SUSPICIOUS') return false;
    if (resultFilter === 'HIGH_RISK' && item.report?.verdict !== 'HIGH_RISK' && item.report?.verdict !== 'CRITICAL') return false;
    if (resultFilter === 'UNINSPECTABLE' && (item.report?.verdict as string) !== 'UNINSPECTABLE') return false;
    if (resultFilter === 'FAILED' && item.status !== 'FAILED') return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        item.name.toLowerCase().includes(q) ||
        item.relativePath.toLowerCase().includes(q) ||
        (item.report?.verdict && item.report.verdict.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <PageContainer>
      {/* 1. Top Header */}
      <PageHeader
        title="Bulk Folder & Large-Scale Document Scanner"
        subtitle="Controlled batch discovery, memory-safe streaming, deduplication, and distributed security analysis"
        breadcrumbs={[{ label: 'DOCUMENTS' }, { label: 'SCAN FOLDER' }]}
        badge={<Badge variant="info">Batch Memory Safe</Badge>}
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button variant="secondary" size="sm" onClick={() => navigate('/')} icon={<ArrowLeft size={13} />}>
              Back to Home
            </Button>
          </div>
        }
      />

      {/* Hidden Folder Picker */}
      <input
        ref={folderInputRef}
        type="file"
        multiple
        // @ts-ignore
        webkitdirectory="true"
        directory=""
        style={{ display: 'none' }}
        onChange={handleFolderSelected}
      />

      {/* ========================================================================= */}
      {/* STAGE 1: FOLDER SELECTION                                                 */}
      {/* ========================================================================= */}
      {stage === 'select' && (
        <div style={{ maxWidth: '800px', margin: '32px auto 0 auto' }}>
          <Card>
            <div style={{ padding: '36px 20px', textAlign: 'center' }}>
              <div
                style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: 'var(--radius-lg)',
                  backgroundColor: 'rgba(99, 102, 241, 0.12)',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-indigo)',
                  margin: '0 auto 16px auto',
                }}
              >
                <FolderArchive size={32} />
              </div>

              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 8px 0' }}>
                Scan a Local Folder
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto 24px auto', lineHeight: 1.5 }}>
                Select a folder containing documents or candidate resumes. SECUROXI will discover files, deduplicate content, and evaluate security threats automatically.
              </p>

              <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
                <Button
                  variant="primary"
                  size="md"
                  onClick={() => folderInputRef.current?.click()}
                  icon={<FolderOpen size={16} />}
                >
                  Select Local Folder
                </Button>
              </div>

              <div style={{ marginTop: '28px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Supported formats: <strong>PDF, DOCX, TXT, HTML, PNG, JPG/JPEG</strong> • Duplicates skipped automatically
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STAGE 2: PRE-SCAN REVIEW                                                  */}
      {/* ========================================================================= */}
      {stage === 'review' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Card
            title={`Discovered Folder: ${folderName}`}
            subtitle="Pre-scan inventory and validation analysis"
            action={
              <div style={{ display: 'flex', gap: '8px' }}>
                <Button variant="secondary" size="sm" onClick={() => folderInputRef.current?.click()}>
                  Change Folder
                </Button>
                <Button variant="primary" size="sm" onClick={handleStartScan} icon={<Zap size={14} />}>
                  Start Security Scan ({totalEligible} Files)
                </Button>
              </div>
            }
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '20px' }}>
              <StatCard
                label="Total Files Found"
                value={totalCount}
                icon={<FolderOpen size={18} />}
              />
              <StatCard
                label="Supported Documents"
                value={supportedCount}
                icon={<FileCheck size={18} />}
                statusBadge={<Badge variant="safe">Supported</Badge>}
              />
              <StatCard
                label="Unsupported Files"
                value={unsupportedCount}
                icon={<AlertTriangle size={18} />}
                statusBadge={unsupportedCount > 0 ? <Badge variant="suspicious">Skipped</Badge> : undefined}
              />
              <StatCard
                label="Duplicates Identified"
                value={duplicateCount}
                icon={<CopyIcon size={18} />}
                statusBadge={duplicateCount > 0 ? <Badge variant="neutral">Deduplicated</Badge> : undefined}
              />
            </div>

            {/* Scale Recommendation Notice */}
            {totalEligible > 5000 && (
              <Alert type="info" title="Large Workload Detected">
                This folder contains over 5,000 documents. SECUROXI will stream files in controlled batches of {DEFAULT_BATCH_SIZE} to protect browser memory. For ongoing automated workloads of 20,000+ files, the SECUROXI Desktop Agent is recommended.
              </Alert>
            )}

            {/* Discovered Files Table Preview */}
            <div style={{ marginTop: '14px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px' }}>
                FILE DISCOVERY PREVIEW ({discoveredFiles.slice(0, 10).length} of {discoveredFiles.length})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '280px', overflowY: 'auto' }}>
                {discoveredFiles.slice(0, 50).map((item) => (
                  <div
                    key={item.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      backgroundColor: 'var(--bg-app)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '0.75rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <FileText size={14} style={{ color: item.isSupported ? 'var(--accent-cyan)' : 'var(--text-muted)' }} />
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.relativePath}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>{item.sizeFormatted}</span>
                      {item.isDuplicate ? (
                        <Badge variant="neutral">Duplicate</Badge>
                      ) : item.isSupported ? (
                        <Badge variant="safe">{item.extension}</Badge>
                      ) : (
                        <Badge variant="suspicious">Unsupported</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STAGE 3: LIVE SCANNING PROGRESS                                           */}
      {/* ========================================================================= */}
      {stage === 'scanning' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Card
            title={`Scanning Folder: ${folderName}`}
            subtitle={`Batch #${activeBatchIndex} in progress • ${completedFiles.length} of ${totalEligible} completed`}
            action={
              <div style={{ display: 'flex', gap: '8px' }}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleTogglePause}
                  icon={isPaused ? <Play size={13} /> : <Pause size={13} />}
                >
                  {isPaused ? 'Resume Scan' : 'Pause'}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCancelScan}
                  icon={<XCircle size={13} />}
                >
                  Cancel Scan
                </Button>
              </div>
            }
          >
            {/* Progress Bar */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', fontWeight: 700, marginBottom: '6px' }}>
                <span>Overall Scan Progress</span>
                <span style={{ color: 'var(--accent-cyan)' }}>{progressPercent}%</span>
              </div>
              <div
                style={{
                  height: '10px',
                  backgroundColor: 'var(--bg-app)',
                  borderRadius: '999px',
                  overflow: 'hidden',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${progressPercent}%`,
                    backgroundColor: isPaused ? 'var(--status-warning)' : 'var(--accent-cyan)',
                    transition: 'width 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                  }}
                />
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                {isPaused ? 'Scan paused' : `Currently analyzing: ${currentProcessingName}`}
              </div>
            </div>

            {/* Real-time Category Breakdown */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px', marginBottom: '16px' }}>
              <div style={{ padding: '10px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>COMPLETED</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>{completedFiles.length}</div>
              </div>
              <div style={{ padding: '10px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>SAFE</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--status-safe)' }}>{safeCount}</div>
              </div>
              <div style={{ padding: '10px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>SUSPICIOUS</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--status-warning)' }}>{suspiciousCount}</div>
              </div>
              <div style={{ padding: '10px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>HIGH RISK</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--status-highrisk)' }}>{highRiskCount}</div>
              </div>
              <div style={{ padding: '10px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>UNINSPECTABLE</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--status-critical)' }}>{uninspectableCount}</div>
              </div>
              <div style={{ padding: '10px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>FAILED</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-muted)' }}>{failedFiles.length}</div>
              </div>
            </div>

            {/* Expandable Advanced Telemetry */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
              <button
                onClick={() => setShowAdvancedTelemetry(!showAdvancedTelemetry)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: 0,
                }}
              >
                <span>{showAdvancedTelemetry ? 'Hide Advanced Telemetry' : 'Show Advanced Telemetry'}</span>
                {showAdvancedTelemetry ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              </button>

              {showAdvancedTelemetry && (
                <div style={{ marginTop: '10px', padding: '12px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div>Memory Management: <strong>Bounded Streaming (Release on Complete)</strong></div>
                  <div>Batch Worker Concurrency: <strong>{DEFAULT_BATCH_SIZE} Parallel Streams</strong></div>
                  <div>Deduplication Cache: <strong>{duplicateCount} files skipped</strong></div>
                  <div>Active Batch ID: <code>BATCH-DIR-{activeBatchIndex}</code></div>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STAGE 4: COMPLETION SUMMARY & FORENSIC DRILLDOWN                          */}
      {/* ========================================================================= */}
      {stage === 'complete' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Header Summary Card */}
          <Card
            title="Folder Scan Complete"
            subtitle={`${completedFiles.length} of ${totalEligible} documents successfully processed in folder "${folderName}"`}
            action={
              <div style={{ display: 'flex', gap: '8px' }}>
                {failedFiles.length > 0 && (
                  <Button variant="outline" size="sm" onClick={handleRetryFailed} icon={<RotateCcw size={13} />}>
                    Retry {failedFiles.length} Failed
                  </Button>
                )}
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setStage('select');
                    setDiscoveredFiles([]);
                  }}
                  icon={<FolderOpen size={14} />}
                >
                  Scan Another Folder
                </Button>
              </div>
            }
          >
            {/* Clickable Filter Pills */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px', marginBottom: '20px' }}>
              <div
                onClick={() => setResultFilter('ALL')}
                style={{
                  padding: '12px',
                  backgroundColor: resultFilter === 'ALL' ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${resultFilter === 'ALL' ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>ALL ANALYZED</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>{completedFiles.length}</div>
              </div>

              <div
                onClick={() => setResultFilter('SAFE')}
                style={{
                  padding: '12px',
                  backgroundColor: resultFilter === 'SAFE' ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${resultFilter === 'SAFE' ? 'var(--status-safe)' : 'var(--border-subtle)'}`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>SAFE</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--status-safe)' }}>{safeCount}</div>
              </div>

              <div
                onClick={() => setResultFilter('SUSPICIOUS')}
                style={{
                  padding: '12px',
                  backgroundColor: resultFilter === 'SUSPICIOUS' ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${resultFilter === 'SUSPICIOUS' ? 'var(--status-warning)' : 'var(--border-subtle)'}`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>SUSPICIOUS</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--status-warning)' }}>{suspiciousCount}</div>
              </div>

              <div
                onClick={() => setResultFilter('HIGH_RISK')}
                style={{
                  padding: '12px',
                  backgroundColor: resultFilter === 'HIGH_RISK' ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${resultFilter === 'HIGH_RISK' ? 'var(--status-highrisk)' : 'var(--border-subtle)'}`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>HIGH RISK</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--status-highrisk)' }}>{highRiskCount}</div>
              </div>

              <div
                onClick={() => setResultFilter('UNINSPECTABLE')}
                style={{
                  padding: '12px',
                  backgroundColor: resultFilter === 'UNINSPECTABLE' ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${resultFilter === 'UNINSPECTABLE' ? 'var(--status-critical)' : 'var(--border-subtle)'}`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>UNINSPECTABLE</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--status-critical)' }}>{uninspectableCount}</div>
              </div>

              {failedFiles.length > 0 && (
                <div
                  onClick={() => setResultFilter('FAILED')}
                  style={{
                    padding: '12px',
                    backgroundColor: resultFilter === 'FAILED' ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${resultFilter === 'FAILED' ? 'var(--status-critical)' : 'var(--border-subtle)'}`,
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>FAILED</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--status-critical)' }}>{failedFiles.length}</div>
                </div>
              )}
            </div>

            {/* Search Input Bar */}
            <div style={{ marginBottom: '14px', display: 'flex', gap: '8px' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '6px 12px',
                  flex: 1,
                }}
              >
                <Search size={14} style={{ color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Filter results by filename, path, or threat category..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    background: 'none',
                    border: 'none',
                    outline: 'none',
                    color: 'var(--text-primary)',
                    fontSize: '0.8125rem',
                    width: '100%',
                  }}
                />
              </div>
            </div>

            {/* Filtered Results Table */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '420px', overflowY: 'auto' }}>
              {filteredResults.length === 0 ? (
                <EmptyState title="No Matching Results" description="Try selecting a different filter category or clearing search query." />
              ) : (
                filteredResults.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      backgroundColor: 'var(--bg-app)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <FileText
                        size={18}
                        style={{
                          color:
                            item.report?.verdict === 'HIGH_RISK'
                              ? 'var(--status-highrisk)'
                              : item.report?.verdict === 'SUSPICIOUS'
                              ? 'var(--status-warning)'
                              : 'var(--accent-cyan)',
                        }}
                      />
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
                          {item.name}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          Path: <code>{item.relativePath}</code> • Size: {item.sizeFormatted}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      {item.report ? (
                        <div style={{ textAlign: 'right' }}>
                          <VerdictBadge verdict={item.report.verdict} />
                          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                            Risk: {item.report.risk_score}/100
                          </div>
                        </div>
                      ) : (
                        <Badge variant="critical">Failed: {item.error}</Badge>
                      )}

                      {item.report && (
                        <Button
                          variant="secondary"
                          size="xs"
                          onClick={() => handleInspectResult(item.report!)}
                          icon={<Eye size={12} />}
                        >
                          Inspect Evidence
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* 5. Forensic Document Viewer Overlay */}
      {viewerDoc && (
        <ForensicDocumentViewer
          isOpen={isViewerOpen}
          onClose={() => setIsViewerOpen(false)}
          filename={viewerDoc.filename}
          documentType={viewerDoc.document_type}
          verdict={viewerDoc.verdict}
          riskScore={viewerDoc.risk_score}
          findings={viewerDoc.findings || []}
          onOpenSecurityBrain={() => {
            setIsViewerOpen(false);
            navigate('/security-brain');
          }}
        />
      )}
    </PageContainer>
  );
};

// Internal copy icon helper
const CopyIcon: React.FC<{ size?: number }> = ({ size = 16 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
    <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
  </svg>
);
