/**
 * SECUROXI Coordinate Transformation & Forensic Overlay Utilities
 * Standardized coordinate mapping between PDF point coordinates [x0, y0, x1, y1]
 * (origin: Top-Left, unit: 72 DPI points) and rendered canvas/viewport pixels.
 */

export interface BoundingBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface ScaledRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface ParsedForensicFinding {
  id: string;
  category: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  title: string;
  description: string;
  evidence: string;
  page: number;
  bbox: BoundingBox;
  source: 'NATIVE_PDF' | 'OCR' | 'STRUCTURAL_LAYOUT' | string;
  ocrConfidence?: number;
  confidence: number;
  isOffscreen?: boolean;
  rawFinding: any;
}

/**
 * Standard PDF Page Dimensions (Points @ 72 DPI)
 * US Letter: 612 x 792
 * A4: 595.28 x 841.89
 */
export const DEFAULT_PAGE_WIDTH = 612.0;
export const DEFAULT_PAGE_HEIGHT = 792.0;

/**
 * Extract structured bounding box and page from any finding or evidence record.
 */
export function parseFindingCoordinates(finding: any, index: number = 0): ParsedForensicFinding {
  let page = 1;
  let bbox: BoundingBox = { x0: 72.0, y0: 120.0 + index * 45.0, x1: 540.0, y1: 155.0 + index * 45.0 };
  let isOffscreen = false;

  // 1. Extract Page
  if (typeof finding.page === 'number' && finding.page > 0) {
    page = finding.page;
  } else if (finding.metadata && typeof finding.metadata.page === 'number') {
    page = finding.metadata.page;
  } else if (typeof finding.location === 'string') {
    const pageMatch = finding.location.match(/Page\s+(\d+)/i);
    if (pageMatch) {
      page = parseInt(pageMatch[1], 10);
    }
  }

  // 2. Extract Bounding Box [x0, y0, x1, y1]
  if (Array.isArray(finding.bbox) && finding.bbox.length === 4) {
    bbox = {
      x0: Number(finding.bbox[0]),
      y0: Number(finding.bbox[1]),
      x1: Number(finding.bbox[2]),
      y1: Number(finding.bbox[3]),
    };
  } else if (finding.metadata && Array.isArray(finding.metadata.bbox) && finding.metadata.bbox.length === 4) {
    bbox = {
      x0: Number(finding.metadata.bbox[0]),
      y0: Number(finding.metadata.bbox[1]),
      x1: Number(finding.metadata.bbox[2]),
      y1: Number(finding.metadata.bbox[3]),
    };
  } else if (typeof finding.location === 'string') {
    // Parse format: "span bbox (x0, y0, x1, y1)" or "bbox [x0, y0, x1, y1]"
    const bboxMatch = finding.location.match(/bbox\s*[(\[]\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*[)\]]/i);
    if (bboxMatch) {
      bbox = {
        x0: parseFloat(bboxMatch[1]),
        y0: parseFloat(bboxMatch[2]),
        x1: parseFloat(bboxMatch[3]),
        y1: parseFloat(bboxMatch[4]),
      };
    }
  }

  // 3. Detect off-screen / clipped coordinates
  if (bbox.x0 < -5.0 || bbox.y0 < -5.0 || bbox.x1 > DEFAULT_PAGE_WIDTH + 5.0 || bbox.y1 > DEFAULT_PAGE_HEIGHT + 5.0) {
    isOffscreen = true;
  }

  // 4. Extract Provenance Source
  const source =
    finding.source ||
    finding.analyzer_source ||
    finding.metadata?.source ||
    (finding.category?.includes('OCR') ? 'OCR' : 'NATIVE_PDF');

  const ocrConfidence = finding.ocr_confidence ?? finding.metadata?.ocr_confidence;

  const severityNorm = (finding.severity || 'HIGH').toUpperCase() as any;
  const severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO' =
    ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].includes(severityNorm) ? severityNorm : 'HIGH';

  return {
    id: finding.finding_id || finding.evidence_id || `FINDING-${index + 1}`,
    category: finding.category || finding.threat_type || 'SECURITY_ANOMALY',
    severity,
    title: finding.title || finding.threat_type || 'Adversarial Injection Detected',
    description: finding.description || finding.explanation || 'Suspicious instruction or layout anomaly.',
    evidence: finding.evidence || finding.original_text || 'Exact evidence unavailable',
    page,
    bbox,
    source,
    ocrConfidence,
    confidence: typeof finding.confidence === 'number' ? finding.confidence : 0.95,
    isOffscreen,
    rawFinding: finding,
  };
}

/**
 * Transform PDF Point Bounding Box to Rendered Screen Pixels based on current viewport.
 */
export function scaleBoundingBox(
  bbox: BoundingBox,
  renderedWidth: number,
  renderedHeight: number,
  pageWidth: number = DEFAULT_PAGE_WIDTH,
  pageHeight: number = DEFAULT_PAGE_HEIGHT
): ScaledRect {
  const scaleX = renderedWidth / Math.max(pageWidth, 1);
  const scaleY = renderedHeight / Math.max(pageHeight, 1);

  const left = Math.max(0, bbox.x0 * scaleX);
  const top = Math.max(0, bbox.y0 * scaleY);
  const width = Math.max(12, (bbox.x1 - bbox.x0) * scaleX);
  const height = Math.max(12, (bbox.y1 - bbox.y0) * scaleY);

  return {
    left: Math.round(left),
    top: Math.round(top),
    width: Math.round(width),
    height: Math.round(height),
  };
}

/**
 * Get Color Palette for Forensic Overlays matching the SECUROXI Design System.
 */
export function getSeverityOverlayColors(severity: string, isSelected: boolean) {
  const sev = (severity || '').toUpperCase();
  switch (sev) {
    case 'CRITICAL':
    case 'HIGH':
    case 'HIGH_RISK':
      return {
        border: '#F43F5E',
        bg: isSelected ? 'rgba(244, 63, 94, 0.28)' : 'rgba(244, 63, 94, 0.14)',
        badgeBg: '#F43F5E',
        badgeText: '#FFFFFF',
        shadow: isSelected ? '0 0 0 3px rgba(244, 63, 94, 0.6), 0 0 16px rgba(244, 63, 94, 0.4)' : 'none',
      };
    case 'MEDIUM':
    case 'SUSPICIOUS':
      return {
        border: '#F59E0B',
        bg: isSelected ? 'rgba(245, 158, 11, 0.28)' : 'rgba(245, 158, 11, 0.14)',
        badgeBg: '#F59E0B',
        badgeText: '#000000',
        shadow: isSelected ? '0 0 0 3px rgba(245, 158, 11, 0.6), 0 0 16px rgba(245, 158, 11, 0.4)' : 'none',
      };
    case 'LOW':
    case 'INFO':
    default:
      return {
        border: '#06B6D4',
        bg: isSelected ? 'rgba(6, 182, 212, 0.28)' : 'rgba(6, 182, 212, 0.14)',
        badgeBg: '#06B6D4',
        badgeText: '#040711',
        shadow: isSelected ? '0 0 0 3px rgba(6, 182, 212, 0.6), 0 0 16px rgba(6, 182, 212, 0.4)' : 'none',
      };
  }
}
