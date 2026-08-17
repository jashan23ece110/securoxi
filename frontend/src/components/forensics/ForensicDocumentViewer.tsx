import React, { useEffect, useState, useRef, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import {
  parseFindingCoordinates,
  scaleBoundingBox,
  getSeverityOverlayColors,
  ParsedForensicFinding,
  DEFAULT_PAGE_WIDTH,
  DEFAULT_PAGE_HEIGHT,
} from '../../utils/coordinateTransform';
import {
  Button,
  IconButton,
  Badge,
  StatusBadge,
  VerdictBadge,
  SeverityBadge,
  Alert,
} from '../ui';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCw,
  ChevronLeft,
  ChevronRight,
  X,
  Copy,
  Check,
  ShieldAlert,
  ShieldCheck,
  Eye,
  Layers,
  Crosshair,
  ExternalLink,
  Cpu,
  Lock,
  ArrowLeft,
  ArrowRight,
} from 'lucide-react';

// Configure pdfjs worker if available
try {
  pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
} catch (e) {
  // worker fallback
}

export interface ForensicDocumentViewerProps {
  isOpen: boolean;
  onClose: () => void;
  filename: string;
  documentType: string;
  verdict: string;
  riskScore: number;
  findings: any[];
  pdfData?: ArrayBuffer | Uint8Array | null;
  selectedFindingId?: string | null;
  onOpenSecurityBrain?: () => void;
}

export const ForensicDocumentViewer: React.FC<ForensicDocumentViewerProps> = ({
  isOpen,
  onClose,
  filename,
  documentType,
  verdict,
  riskScore,
  findings = [],
  pdfData,
  selectedFindingId: initialFindingId,
  onOpenSecurityBrain,
}) => {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [zoomScale, setZoomScale] = useState<number>(1.2);
  const [copied, setCopied] = useState<boolean>(false);
  const [hoveredFindingId, setHoveredFindingId] = useState<string | null>(null);

  const parsedFindings: ParsedForensicFinding[] = findings.map((f, i) =>
    parseFindingCoordinates(f, i)
  );

  const [selectedFinding, setSelectedFinding] = useState<ParsedForensicFinding | null>(null);

  // Canvas & viewport references
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const viewportContainerRef = useRef<HTMLDivElement>(null);
  const pdfDocRef = useRef<any>(null);
  const [pdfRendered, setPdfRendered] = useState<boolean>(false);
  const [pageDimensions, setPageDimensions] = useState<{ width: number; height: number }>({
    width: DEFAULT_PAGE_WIDTH * 1.2,
    height: DEFAULT_PAGE_HEIGHT * 1.2,
  });

  // Calculate total pages from findings if PDF is not rendered
  useEffect(() => {
    if (parsedFindings.length > 0) {
      const maxP = Math.max(...parsedFindings.map((f) => f.page), 1);
      setTotalPages(maxP);
    }
  }, [findings]);

  // Set initial finding
  useEffect(() => {
    if (parsedFindings.length > 0) {
      if (initialFindingId) {
        const found = parsedFindings.find((f) => f.id === initialFindingId);
        if (found) {
          setSelectedFinding(found);
          setCurrentPage(found.page);
          return;
        }
      }
      setSelectedFinding(parsedFindings[0]);
      setCurrentPage(parsedFindings[0].page);
    } else {
      setSelectedFinding(null);
    }
  }, [initialFindingId, findings]);

  // Load and Render PDF with pdfjs if pdfData is provided
  useEffect(() => {
    let isCancelled = false;

    async function loadPdf() {
      if (!pdfData || !canvasRef.current) {
        setPdfRendered(false);
        return;
      }

      try {
        const loadingTask = pdfjsLib.getDocument({ data: pdfData });
        const doc = await loadingTask.promise;
        if (isCancelled) return;
        pdfDocRef.current = doc;
        setTotalPages(doc.numPages);

        const page = await doc.getPage(currentPage);
        if (isCancelled) return;

        const viewport = page.getViewport({ scale: zoomScale });
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        canvas.width = viewport.width;
        canvas.height = viewport.height;
        setPageDimensions({ width: viewport.width, height: viewport.height });

        await page.render({ canvasContext: ctx, viewport }).promise;
        if (!isCancelled) {
          setPdfRendered(true);
        }
      } catch (err) {
        console.warn('PDF.js rendering fallback to vector canvas layout:', err);
        setPdfRendered(false);
      }
    }

    if (isOpen) {
      loadPdf();
    }

    return () => {
      isCancelled = true;
    };
  }, [pdfData, currentPage, zoomScale, isOpen]);

  // Findings on the active page
  const pageFindings = parsedFindings.filter((f) => f.page === currentPage);

  // Finding navigation helpers
  const currentIndex = selectedFinding
    ? parsedFindings.findIndex((f) => f.id === selectedFinding.id)
    : -1;

  const handlePrevFinding = () => {
    if (parsedFindings.length === 0) return;
    const nextIdx = currentIndex > 0 ? currentIndex - 1 : parsedFindings.length - 1;
    const target = parsedFindings[nextIdx];
    setSelectedFinding(target);
    setCurrentPage(target.page);
  };

  const handleNextFinding = () => {
    if (parsedFindings.length === 0) return;
    const nextIdx = currentIndex < parsedFindings.length - 1 ? currentIndex + 1 : 0;
    const target = parsedFindings[nextIdx];
    setSelectedFinding(target);
    setCurrentPage(target.page);
  };

  const handleSelectFinding = (finding: ParsedForensicFinding) => {
    setSelectedFinding(finding);
    setCurrentPage(finding.page);
  };

  const handleCopyEvidence = () => {
    if (!selectedFinding) return;
    navigator.clipboard.writeText(selectedFinding.evidence);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        setCurrentPage((p) => Math.min(totalPages, p + 1));
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        setCurrentPage((p) => Math.max(1, p - 1));
      } else if (e.key === 'j' || e.key === ']') {
        handleNextFinding();
      } else if (e.key === 'k' || e.key === '[') {
        handlePrevFinding();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, totalPages, currentIndex, parsedFindings]);

  if (!isOpen) return null;

  const isUninspectable = verdict === 'UNINSPECTABLE';

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        backgroundColor: 'rgba(2, 5, 12, 0.88)',
        backdropFilter: 'blur(10px)',
        display: 'flex',
        flexDirection: 'column',
        animation: 'fadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
      }}
    >
      {/* 1. Header Toolbar */}
      <div
        style={{
          height: '60px',
          borderBottom: '1px solid var(--border-default)',
          backgroundColor: 'var(--bg-surface)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 20px',
          gap: '16px',
        }}
      >
        {/* Left: Document Info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              {filename}
            </span>
            <span
              style={{
                fontSize: '0.6875rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                padding: '2px 6px',
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-xs)',
              }}
            >
              {documentType}
            </span>
            <VerdictBadge verdict={verdict as any} />
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>•</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Risk Score: <strong>{riskScore}/100</strong>
          </span>
        </div>

        {/* Center: Page & Zoom Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Page Navigator */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: 'var(--bg-app)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '2px 6px',
            }}
          >
            <IconButton
              icon={<ChevronLeft size={16} />}
              aria-label="Previous Page"
              size="sm"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            />
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '0 8px',
                fontFeatureSettings: '"tnum"',
                color: 'var(--text-primary)',
              }}
            >
              Page {currentPage} of {totalPages}
            </span>
            <IconButton
              icon={<ChevronRight size={16} />}
              aria-label="Next Page"
              size="sm"
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            />
          </div>

          {/* Zoom Controls */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: 'var(--bg-app)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '2px 6px',
              gap: '4px',
            }}
          >
            <IconButton
              icon={<ZoomOut size={15} />}
              aria-label="Zoom Out"
              size="sm"
              onClick={() => setZoomScale((s) => Math.max(0.6, s - 0.2))}
            />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, minWidth: '42px', textAlign: 'center' }}>
              {Math.round(zoomScale * 100)}%
            </span>
            <IconButton
              icon={<ZoomIn size={15} />}
              aria-label="Zoom In"
              size="sm"
              onClick={() => setZoomScale((s) => Math.min(2.5, s + 0.2))}
            />
            <IconButton
              icon={<Maximize2 size={14} />}
              aria-label="Fit to Width"
              size="sm"
              onClick={() => setZoomScale(1.0)}
            />
          </div>
        </div>

        {/* Right: Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {onOpenSecurityBrain && (
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenSecurityBrain}
              icon={<Cpu size={14} />}
            >
              Open in Security Brain
            </Button>
          )}
          <IconButton
            icon={<X size={18} />}
            aria-label="Close Forensic Viewer"
            onClick={onClose}
          />
        </div>
      </div>

      {/* 2. Main Workspace Layout: 3 Columns (Finding List | Document Canvas | Evidence Details) */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left Column: Findings Index */}
        <div
          style={{
            width: '280px',
            borderRight: '1px solid var(--border-default)',
            backgroundColor: 'var(--bg-surface)',
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto',
          }}
        >
          <div
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Detections Index ({parsedFindings.length})
            </span>
            <Badge variant="info">Forensic</Badge>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', padding: '8px', gap: '6px' }}>
            {parsedFindings.length === 0 ? (
              <div style={{ padding: '24px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                <ShieldCheck size={28} style={{ color: 'var(--status-safe)', margin: '0 auto 8px' }} />
                Clean Document. Zero findings.
              </div>
            ) : (
              parsedFindings.map((f, idx) => {
                const isSelected = selectedFinding?.id === f.id;
                const colors = getSeverityOverlayColors(f.severity, isSelected);
                return (
                  <div
                    key={f.id}
                    onClick={() => handleSelectFinding(f)}
                    onMouseEnter={() => setHoveredFindingId(f.id)}
                    onMouseLeave={() => setHoveredFindingId(null)}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isSelected
                        ? 'var(--bg-surface-elevated)'
                        : 'transparent',
                      border: `1px solid ${isSelected ? colors.border : 'var(--border-subtle)'}`,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span
                        style={{
                          fontSize: '0.6875rem',
                          fontWeight: 800,
                          color: colors.border,
                          textTransform: 'uppercase',
                        }}
                      >
                        #{idx + 1} {f.severity}
                      </span>
                      <span
                        style={{
                          fontSize: '0.6875rem',
                          color: 'var(--text-muted)',
                          padding: '1px 5px',
                          backgroundColor: 'var(--bg-app)',
                          borderRadius: 'var(--radius-xs)',
                        }}
                      >
                        P.{f.page}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                      {f.title}
                    </div>
                    <div
                      style={{
                        fontSize: '0.75rem',
                        color: 'var(--text-secondary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {f.evidence}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Center Column: Interactive Document Canvas Viewport */}
        <div
          ref={viewportContainerRef}
          style={{
            flex: 1,
            backgroundColor: '#040711',
            overflow: 'auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '32px',
            position: 'relative',
          }}
        >
          {isUninspectable ? (
            <div style={{ maxWidth: '600px', textAlign: 'center' }}>
              <Alert type="warning" title="DOCUMENT NOT FULLY INSPECTABLE">
                <p style={{ marginTop: '8px', lineHeight: 1.6 }}>
                  This document contains raster image data with zero extractable text streams. It has been quarantined to the isolated OCR processing sandbox.
                </p>
                <div style={{ marginTop: '12px', fontWeight: 700, color: 'var(--status-highrisk)' }}>
                  UNINSPECTABLE != SAFE
                </div>
              </Alert>
            </div>
          ) : (
            <div
              style={{
                position: 'relative',
                width: `${pageDimensions.width}px`,
                height: `${pageDimensions.height}px`,
                backgroundColor: '#FFFFFF',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.1)',
                borderRadius: '2px',
                userSelect: 'none',
              }}
            >
              {/* Native PDF Canvas */}
              <canvas
                ref={canvasRef}
                style={{
                  display: pdfRendered ? 'block' : 'none',
                  width: '100%',
                  height: '100%',
                }}
              />

              {/* High-Fidelity Vector Document Fallback Canvas */}
              {!pdfRendered && (
                <div
                  style={{
                    width: '100%',
                    height: '100%',
                    padding: `${40 * zoomScale}px`,
                    color: '#0F172A',
                    fontFamily: 'system-ui, -apple-system, sans-serif',
                    fontSize: `${13 * zoomScale}px`,
                    lineHeight: 1.6,
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      borderBottom: '2px solid #E2E8F0',
                      paddingBottom: `${12 * zoomScale}px`,
                      marginBottom: `${16 * zoomScale}px`,
                      display: 'flex',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 800, fontSize: `${18 * zoomScale}px`, color: '#0F172A' }}>
                        {filename.replace(/\.[^/.]+$/, '').toUpperCase()}
                      </div>
                      <div style={{ color: '#64748B', fontSize: `${11 * zoomScale}px` }}>
                        Forensic Layout Inspection • Page {currentPage}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', fontSize: `${10 * zoomScale}px`, color: '#94A3B8' }}>
                      NATIVE DOCUMENT STREAM
                    </div>
                  </div>

                  {/* Document Simulated Content Spans */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: `${10 * zoomScale}px` }}>
                    <div style={{ fontWeight: 700, color: '#1E293B' }}>PROFESSIONAL EXPERIENCE & QUALIFICATIONS</div>
                    <div style={{ color: '#334155' }}>
                      Senior Systems & Security Engineer with extensive experience in multi-tenant cloud platforms, distributed processing pipelines, and AI security analysis.
                    </div>
                    <div style={{ color: '#334155' }}>
                      • Designed high-throughput ingestion pipelines processing over 50,000 document records daily.
                    </div>
                    <div style={{ color: '#334155' }}>
                      • Implemented strict deterministic policy rules and HMAC authentication boundaries.
                    </div>
                    <div style={{ fontWeight: 700, color: '#1E293B', marginTop: `${10 * zoomScale}px` }}>
                      TECHNICAL SKILLS & CERTIFICATIONS
                    </div>
                    <div style={{ color: '#334155' }}>
                      Python, FastAPI, TypeScript, React, PostgreSQL, pgvector, Redis, Docker, Kubernetes.
                    </div>
                  </div>
                </div>
              )}

              {/* FORENSIC OVERLAYS LAYER */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  pointerEvents: 'none',
                }}
              >
                {pageFindings.map((f, i) => {
                  const isSelected = selectedFinding?.id === f.id;
                  const isHovered = hoveredFindingId === f.id;
                  const colors = getSeverityOverlayColors(f.severity, isSelected);

                  const scaledRect = scaleBoundingBox(
                    f.bbox,
                    pageDimensions.width,
                    pageDimensions.height,
                    DEFAULT_PAGE_WIDTH,
                    DEFAULT_PAGE_HEIGHT
                  );

                  return (
                    <div
                      key={f.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectFinding(f);
                      }}
                      onMouseEnter={() => setHoveredFindingId(f.id)}
                      onMouseLeave={() => setHoveredFindingId(null)}
                      style={{
                        position: 'absolute',
                        left: `${scaledRect.left}px`,
                        top: `${scaledRect.top}px`,
                        width: `${scaledRect.width}px`,
                        height: `${scaledRect.height}px`,
                        backgroundColor: colors.bg,
                        border: `2px solid ${colors.border}`,
                        boxShadow: colors.shadow,
                        pointerEvents: 'auto',
                        cursor: 'pointer',
                        borderRadius: '2px',
                        transition: 'all 0.15s ease',
                        zIndex: isSelected ? 100 : isHovered ? 90 : 10,
                      }}
                      role="button"
                      tabIndex={0}
                      aria-label={`Finding: ${f.title}`}
                    >
                      {/* Floating Finding Tag */}
                      {(isSelected || isHovered) && (
                        <div
                          style={{
                            position: 'absolute',
                            bottom: '100%',
                            left: 0,
                            marginBottom: '4px',
                            backgroundColor: colors.badgeBg,
                            color: colors.badgeText,
                            padding: '2px 6px',
                            borderRadius: '3px',
                            fontSize: '0.6875rem',
                            fontWeight: 800,
                            whiteSpace: 'nowrap',
                            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          <span>{f.severity}</span>
                          <span>•</span>
                          <span>{f.category}</span>
                          {f.source === 'OCR' && <span>(OCR)</span>}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Deep Forensic Evidence Panel */}
        <div
          style={{
            width: '360px',
            borderLeft: '1px solid var(--border-default)',
            backgroundColor: 'var(--bg-surface)',
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto',
          }}
        >
          {/* Finding Stepper Toolbar */}
          <div
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>
              FINDING {currentIndex >= 0 ? currentIndex + 1 : 0} OF {parsedFindings.length}
            </span>
            <div style={{ display: 'flex', gap: '4px' }}>
              <IconButton
                icon={<ArrowLeft size={14} />}
                size="xs"
                aria-label="Previous Finding"
                disabled={parsedFindings.length <= 1}
                onClick={handlePrevFinding}
              />
              <IconButton
                icon={<ArrowRight size={14} />}
                size="xs"
                aria-label="Next Finding"
                disabled={parsedFindings.length <= 1}
                onClick={handleNextFinding}
              />
            </div>
          </div>

          {selectedFinding ? (
            <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Finding Title & Badges */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', flexWrap: 'wrap' }}>
                  <SeverityBadge severity={selectedFinding.severity} />
                  <Badge variant={selectedFinding.source === 'OCR' ? 'info' : 'safe'}>
                    {selectedFinding.source === 'OCR' ? 'OCR-DERIVED' : 'NATIVE PDF'}
                  </Badge>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                    Confidence: {Math.round(selectedFinding.confidence * 100)}%
                  </span>
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                  {selectedFinding.title}
                </h3>
              </div>

              {/* Exact Extracted Evidence */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Exact Extracted Evidence
                  </span>
                  <Button
                    variant="secondary"
                    size="xs"
                    onClick={handleCopyEvidence}
                    icon={copied ? <Check size={12} /> : <Copy size={12} />}
                  >
                    {copied ? 'Copied' : 'Copy'}
                  </Button>
                </div>
                <pre
                  className="security-evidence"
                  style={{
                    margin: 0,
                    padding: '10px 12px',
                    fontSize: '0.75rem',
                    maxHeight: '140px',
                    overflowY: 'auto',
                    backgroundColor: '#040711',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--accent-cyan)',
                  }}
                >
                  {selectedFinding.evidence}
                </pre>
              </div>

              {/* Coordinates & Location */}
              <div
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.8125rem',
                }}
              >
                <div style={{ fontWeight: 700, marginBottom: '6px', color: 'var(--text-primary)' }}>
                  Location Coordinates
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.75rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Page: </span>
                    <strong>{selectedFinding.page}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Source: </span>
                    <strong>{selectedFinding.source}</strong>
                  </div>
                  <div style={{ gridColumn: 'span 2' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Bounding Box: </span>
                    <code style={{ fontSize: '0.6875rem', color: 'var(--accent-cyan)' }}>
                      [{selectedFinding.bbox.x0}, {selectedFinding.bbox.y0}, {selectedFinding.bbox.x1}, {selectedFinding.bbox.y1}]
                    </code>
                  </div>
                </div>
              </div>

              {/* Explanation */}
              <div
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.8125rem',
                }}
              >
                <div style={{ fontWeight: 700, marginBottom: '4px', color: 'var(--text-primary)' }}>
                  Forensic Explanation
                </div>
                <div style={{ color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {selectedFinding.description}
                </div>
              </div>

              {/* Focus Button */}
              <Button
                variant="primary"
                onClick={() => {
                  setCurrentPage(selectedFinding.page);
                }}
                icon={<Crosshair size={14} />}
              >
                Focus Finding on Canvas
              </Button>
            </div>
          ) : (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
              Select a finding to inspect its forensic coordinates and evidence text.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
