import React, { useState } from 'react';
import { Copy, Check, Terminal, ShieldAlert, FileText, Cpu, MapPin } from 'lucide-react';
import { SeverityBadge } from './Badge';

export interface EvidenceBlockProps {
  evidence: string;
  threatType?: string;
  category?: string;
  severity?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  page?: number | string;
  location?: string;
  detector?: string;
  explanation?: string;
  confidence?: number;
  className?: string;
}

export const EvidenceBlock: React.FC<EvidenceBlockProps> = ({
  evidence,
  threatType,
  category,
  severity,
  page,
  location,
  detector,
  explanation,
  confidence,
  className = '',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(evidence);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`evidence-container ${className}`.trim()}
      style={{
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        backgroundColor: '#040710',
      }}
    >
      {/* Evidence Meta Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 14px',
          backgroundColor: '#090E1A',
          borderBottom: '1px solid var(--border-subtle)',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            <Terminal size={14} style={{ color: 'var(--accent-cyan)' }} />
            <span>{threatType || 'FORENSIC EVIDENCE'}</span>
          </span>

          {severity && <SeverityBadge severity={severity} />}

          {category && (
            <span
              style={{
                fontSize: '0.6875rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                backgroundColor: 'var(--bg-surface-elevated)',
                padding: '2px 6px',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {category}
            </span>
          )}

          {confidence !== undefined && (
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              Confidence: {Math.round(confidence * 100)}%
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {page !== undefined && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              <FileText size={12} />
              Page {page}
            </span>
          )}

          {location && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              <MapPin size={12} />
              {location}
            </span>
          )}

          {detector && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', fontSize: '0.6875rem', color: 'var(--text-code)' }}>
              <Cpu size={12} />
              {detector}
            </span>
          )}

          <button
            onClick={handleCopy}
            title="Copy exact evidence payload"
            aria-label="Copy exact evidence payload"
            style={{
              background: 'none',
              border: 'none',
              color: copied ? 'var(--status-safe)' : 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.75rem',
              fontWeight: 600,
              padding: '2px 6px',
              borderRadius: 'var(--radius-xs)',
            }}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Exact Extracted Code / Text Evidence */}
      <div
        className="evidence-code"
        style={{
          padding: '12px 16px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8125rem',
          color: 'var(--text-code)',
          backgroundColor: '#03060D',
          overflowX: 'auto',
          lineHeight: 1.6,
        }}
      >
        <code>{evidence}</code>
      </div>

      {/* AI Reasoning vs. Deterministic Policy Explanation */}
      {explanation && (
        <div
          style={{
            padding: '8px 14px',
            backgroundColor: 'rgba(18, 26, 43, 0.6)',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px',
          }}
        >
          <ShieldAlert size={14} style={{ color: 'var(--status-suspicious)', flexShrink: 0, marginTop: '1px' }} />
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>Forensic Explanation: </strong>
            <span>{explanation}</span>
          </div>
        </div>
      )}
    </div>
  );
};
