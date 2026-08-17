import React, { useState, useMemo } from 'react';
import { ScanReport } from '../../api/types';
import {
  Card,
  Button,
  StatusBadge,
  VerdictBadge,
  Badge,
  RiskIndicator,
  EmptyState,
} from '../ui';
import { SecurityDistributionBar } from './SecurityDistributionBar';
import {
  FileText,
  Search,
  Download,
  ExternalLink,
  Eye,
  Brain,
  Filter,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  EyeOff,
} from 'lucide-react';

export interface SmartResultTableProps {
  scans: ScanReport[];
  title?: string;
  subtitle?: string;
  onInspectScan: (scan: ScanReport) => void;
  onOpenSecurityBrain?: (scan: ScanReport) => void;
  onExportCsv?: () => void;
  onExportJson?: () => void;
}

// User-friendly plain-language threat translation dictionary
export const translateThreatCategory = (category?: string, threatType?: string): string => {
  const norm = (category || threatType || '').toUpperCase().trim();
  if (norm.includes('PROMPT_INJECTION') || norm.includes('INJECTION')) {
    return 'Instruction detected attempting to manipulate automated workflow';
  }
  if (norm.includes('MICRO_TEXT') || norm.includes('FONT_SIZE')) {
    return 'Concealed micro text with font size below readability threshold';
  }
  if (norm.includes('WHITE_TEXT') || norm.includes('BACKGROUND_MATCH') || norm.includes('COLOR_MATCH')) {
    return 'Text styled to blend into background for visual concealment';
  }
  if (norm.includes('ATS_MANIPULATION') || norm.includes('ATS')) {
    return 'Adversarial override attempting to force keyword pass';
  }
  if (norm.includes('OCR') || norm.includes('SCANNED')) {
    return 'Suspicious payload detected in scanned image layer';
  }
  if (norm.includes('UNICODE') || norm.includes('ZERO_WIDTH')) {
    return 'Hidden or invisible unicode characters detected';
  }
  return 'Document evaluated cleanly against security policies';
};

export const SmartResultTable: React.FC<SmartResultTableProps> = ({
  scans,
  title = 'Document Security Inventory',
  subtitle = 'Prioritized threat analysis, plain-language summaries, and forensic verification',
  onInspectScan,
  onOpenSecurityBrain,
  onExportCsv,
  onExportJson,
}) => {
  const [activeVerdictFilter, setActiveVerdictFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [formatFilter, setFormatFilter] = useState<string>('ALL');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);

  // Priority weight map for sorting (High Risk -> Uninspectable -> Suspicious -> Failed -> Safe)
  const getPriorityWeight = (verdict: string): number => {
    const v = (verdict || '').toUpperCase();
    if (v === 'CRITICAL' || v === 'HIGH_RISK') return 5;
    if (v === 'UNINSPECTABLE') return 4;
    if (v === 'SUSPICIOUS') return 3;
    if (v === 'FAILED') return 2;
    return 1; // SAFE
  };

  // Filtered & Prioritized Scans
  const filteredScans = useMemo(() => {
    return scans
      .filter((s) => {
        // Verdict filter
        if (activeVerdictFilter !== 'ALL') {
          if (activeVerdictFilter === 'HIGH_RISK') {
            if (s.verdict !== 'HIGH_RISK' && s.verdict !== 'CRITICAL') return false;
          } else if (s.verdict.toUpperCase() !== activeVerdictFilter) {
            return false;
          }
        }
        // Format filter
        if (formatFilter !== 'ALL' && s.document_type.toUpperCase() !== formatFilter) {
          return false;
        }
        // Search query
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchName = s.filename.toLowerCase().includes(q);
          const matchId = s.scan_id.toLowerCase().includes(q);
          const matchSummary = (s.summary || '').toLowerCase().includes(q);
          if (!matchName && !matchId && !matchSummary) return false;
        }
        return true;
      })
      .sort((a, b) => {
        const pDiff = getPriorityWeight(b.verdict) - getPriorityWeight(a.verdict);
        if (pDiff !== 0) return pDiff;
        return b.risk_score - a.risk_score;
      });
  }, [scans, activeVerdictFilter, formatFilter, searchQuery]);

  // Counts for tabs
  const totalCount = scans.length;
  const highRiskCount = scans.filter((s) => s.verdict === 'HIGH_RISK' || s.verdict === 'CRITICAL').length;
  const uninspectableCount = scans.filter((s) => (s.verdict as string) === 'UNINSPECTABLE').length;
  const suspiciousCount = scans.filter((s) => s.verdict === 'SUSPICIOUS').length;
  const safeCount = scans.filter((s) => s.verdict === 'SAFE').length;
  const failedCount = scans.filter((s) => (s.verdict as string) === 'FAILED').length;

  // Pagination Slice
  const totalPages = Math.ceil(filteredScans.length / pageSize) || 1;
  const paginatedScans = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredScans.slice(start, start + pageSize);
  }, [filteredScans, currentPage, pageSize]);

  return (
    <Card
      title={title}
      subtitle={subtitle}
      action={
        <div style={{ display: 'flex', gap: '8px' }}>
          {onExportCsv && (
            <Button variant="secondary" size="xs" onClick={onExportCsv} icon={<Download size={12} />}>
              Export CSV
            </Button>
          )}
          {onExportJson && (
            <Button variant="secondary" size="xs" onClick={onExportJson} icon={<Download size={12} />}>
              Export JSON
            </Button>
          )}
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* 1. Visual Distribution Segmented Bar */}
        <SecurityDistributionBar
          scans={scans}
          activeFilter={activeVerdictFilter}
          onFilterChange={(v) => {
            setActiveVerdictFilter(v);
            setCurrentPage(1);
          }}
        />

        {/* 2. Interactive Category Filter Tabs */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          {[
            { key: 'ALL', label: 'All Results', count: totalCount, color: 'var(--text-primary)' },
            { key: 'HIGH_RISK', label: 'High Risk', count: highRiskCount, color: 'var(--status-highrisk)' },
            { key: 'UNINSPECTABLE', label: 'Uninspectable', count: uninspectableCount, color: 'var(--status-critical)' },
            { key: 'SUSPICIOUS', label: 'Suspicious', count: suspiciousCount, color: 'var(--status-warning)' },
            { key: 'SAFE', label: 'Safe', count: safeCount, color: 'var(--status-safe)' },
            ...(failedCount > 0
              ? [{ key: 'FAILED', label: 'Failed', count: failedCount, color: 'var(--text-muted)' }]
              : []),
          ].map((tab) => {
            const isActive = activeVerdictFilter === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => {
                  setActiveVerdictFilter(tab.key);
                  setCurrentPage(1);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  border: `1px solid ${isActive ? tab.color : 'var(--border-subtle)'}`,
                  backgroundColor: isActive ? 'var(--bg-surface-elevated)' : 'var(--bg-app)',
                  color: isActive ? tab.color : 'var(--text-secondary)',
                  transition: 'all 0.15s ease',
                }}
              >
                <span>{tab.label}</span>
                <span
                  style={{
                    fontSize: '0.6875rem',
                    padding: '1px 5px',
                    borderRadius: '999px',
                    backgroundColor: isActive ? tab.color : 'var(--border-subtle)',
                    color: isActive ? '#fff' : 'var(--text-muted)',
                  }}
                >
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* 3. Search & Format Filter Bar */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
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
              minWidth: '220px',
            }}
          >
            <Search size={14} style={{ color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search by file name, scan ID, or summary..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
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

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Format:</span>
            <select
              value={formatFilter}
              onChange={(e) => {
                setFormatFilter(e.target.value);
                setCurrentPage(1);
              }}
              style={{
                backgroundColor: 'var(--bg-input)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 8px',
                fontSize: '0.75rem',
                outline: 'none',
              }}
            >
              <option value="ALL">All Formats</option>
              <option value="PDF">PDF</option>
              <option value="DOCX">DOCX</option>
              <option value="TXT">TXT</option>
              <option value="HTML">HTML</option>
              <option value="PNG">PNG</option>
              <option value="JPG">JPG</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Per Page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              style={{
                backgroundColor: 'var(--bg-input)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 8px',
                fontSize: '0.75rem',
                outline: 'none',
              }}
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>

        {/* 4. Results List */}
        {filteredScans.length === 0 ? (
          <EmptyState
            title="No Matching Documents"
            description="No documents matched the selected filters. Try clearing your search or switching filter categories."
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {paginatedScans.map((scan) => {
              const firstFinding = scan.findings && scan.findings.length > 0 ? scan.findings[0] : null;
              const plainSummary = firstFinding
                ? translateThreatCategory(firstFinding.category, firstFinding.threat_type)
                : scan.summary || 'Security analysis complete. Zero threats detected.';

              return (
                <div
                  key={scan.scan_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    backgroundColor: 'var(--bg-app)',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${
                      scan.verdict === 'HIGH_RISK' || scan.verdict === 'CRITICAL'
                        ? 'var(--status-critical-border)'
                        : scan.verdict === 'SUSPICIOUS'
                        ? 'var(--border-default)'
                        : 'var(--border-subtle)'
                    }`,
                    transition: 'all var(--transition-fast)',
                  }}
                >
                  {/* Left: Document details & Plain Language Threat Summary */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', maxWidth: '65%' }}>
                    <div
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--bg-surface)',
                        border: '1px solid var(--border-default)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginTop: '2px',
                        color:
                          scan.verdict === 'HIGH_RISK' || scan.verdict === 'CRITICAL'
                            ? 'var(--status-highrisk)'
                            : scan.verdict === 'SUSPICIOUS'
                            ? 'var(--status-warning)'
                            : 'var(--accent-cyan)',
                      }}
                    >
                      <FileText size={18} />
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
                          {scan.filename}
                        </span>
                        <span
                          style={{
                            fontSize: '0.6875rem',
                            fontWeight: 700,
                            padding: '1px 5px',
                            backgroundColor: 'var(--bg-surface)',
                            borderRadius: 'var(--radius-xs)',
                            border: '1px solid var(--border-subtle)',
                            color: 'var(--text-muted)',
                            textTransform: 'uppercase',
                          }}
                        >
                          {scan.document_type}
                        </span>
                      </div>

                      <div
                        style={{
                          fontSize: '0.8125rem',
                          color:
                            scan.verdict === 'HIGH_RISK'
                              ? 'var(--status-highrisk)'
                              : scan.verdict === 'SUSPICIOUS'
                              ? 'var(--status-warning)'
                              : 'var(--text-secondary)',
                          marginTop: '2px',
                          lineHeight: 1.4,
                        }}
                      >
                        {plainSummary}
                      </div>

                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Scan ID: <code>{scan.scan_id}</code> • {new Date(scan.created_at).toLocaleString()}
                        {scan.findings && scan.findings.length > 0 && ` • ${scan.findings.length} findings`}
                      </div>
                    </div>
                  </div>

                  {/* Right: Risk Gauge & Action Buttons */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ textAlign: 'right', minWidth: '110px' }}>
                      <VerdictBadge verdict={scan.verdict} />
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        Risk: <strong>{scan.risk_score}</strong>/100
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '6px' }}>
                      <Button
                        variant="secondary"
                        size="xs"
                        onClick={() => onInspectScan(scan)}
                        icon={<Eye size={12} />}
                      >
                        Inspect Evidence
                      </Button>

                      {onOpenSecurityBrain && (scan.verdict === 'HIGH_RISK' || scan.verdict === 'SUSPICIOUS') && (
                        <Button
                          variant="ghost"
                          size="xs"
                          onClick={() => onOpenSecurityBrain(scan)}
                          icon={<Brain size={12} />}
                        >
                          Investigate
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* 5. Pagination Bar */}
        {filteredScans.length > 0 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              paddingTop: '8px',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
            }}
          >
            <div>
              Showing {Math.min((currentPage - 1) * pageSize + 1, filteredScans.length)}–
              {Math.min(currentPage * pageSize, filteredScans.length)} of {filteredScans.length} documents
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Button
                variant="ghost"
                size="xs"
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                icon={<ChevronLeft size={12} />}
              >
                Previous
              </Button>

              <span>
                Page {currentPage} of {totalPages}
              </span>

              <Button
                variant="ghost"
                size="xs"
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                icon={<ChevronRight size={12} />}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
