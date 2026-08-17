import React from 'react';
import { ScanReport } from '../../api/types';
import { ShieldAlert, ShieldCheck, AlertTriangle, EyeOff, XCircle, ArrowRight } from 'lucide-react';

export interface SecurityDistributionBarProps {
  scans: ScanReport[];
  activeFilter: string;
  onFilterChange: (verdict: string) => void;
}

export const SecurityDistributionBar: React.FC<SecurityDistributionBarProps> = ({
  scans,
  activeFilter,
  onFilterChange,
}) => {
  const total = scans.length;
  if (total === 0) return null;

  const safeCount = scans.filter((s) => s.verdict === 'SAFE').length;
  const suspiciousCount = scans.filter((s) => s.verdict === 'SUSPICIOUS').length;
  const highRiskCount = scans.filter((s) => s.verdict === 'HIGH_RISK' || s.verdict === 'CRITICAL').length;
  const uninspectableCount = scans.filter((s) => (s.verdict as string) === 'UNINSPECTABLE').length;
  const failedCount = scans.filter((s) => (s.verdict as string) === 'FAILED').length;

  const safePct = (safeCount / total) * 100;
  const suspiciousPct = (suspiciousCount / total) * 100;
  const highRiskPct = (highRiskCount / total) * 100;
  const uninspectablePct = (uninspectableCount / total) * 100;
  const failedPct = (failedCount / total) * 100;

  const attentionRequiredCount = highRiskCount + uninspectableCount + suspiciousCount;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* 1. Action Priority Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 16px',
          backgroundColor:
            attentionRequiredCount > 0 ? 'rgba(244, 63, 94, 0.08)' : 'rgba(16, 185, 129, 0.08)',
          borderRadius: 'var(--radius-md)',
          border: `1px solid ${
            attentionRequiredCount > 0
              ? 'rgba(244, 63, 94, 0.25)'
              : 'rgba(16, 185, 129, 0.25)'
          }`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {attentionRequiredCount > 0 ? (
            <ShieldAlert size={18} style={{ color: 'var(--status-highrisk)' }} />
          ) : (
            <ShieldCheck size={18} style={{ color: 'var(--status-safe)' }} />
          )}
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
              {attentionRequiredCount > 0
                ? `${attentionRequiredCount} document${attentionRequiredCount > 1 ? 's' : ''} require attention`
                : `All ${total} documents passed security verification`}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {highRiskCount > 0 && `${highRiskCount} High Risk • `}
              {uninspectableCount > 0 && `${uninspectableCount} Uninspectable • `}
              {suspiciousCount > 0 && `${suspiciousCount} Suspicious • `}
              {safeCount} Clean Passed
            </div>
          </div>
        </div>

        {highRiskCount > 0 && activeFilter !== 'HIGH_RISK' && (
          <button
            onClick={() => onFilterChange('HIGH_RISK')}
            style={{
              background: 'var(--status-highrisk)',
              color: '#fff',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 12px',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>Review High Risk</span>
            <ArrowRight size={12} />
          </button>
        )}
      </div>

      {/* 2. Proportional Segmented Distribution Bar */}
      <div>
        <div
          style={{
            height: '12px',
            borderRadius: '999px',
            overflow: 'hidden',
            display: 'flex',
            backgroundColor: 'var(--bg-app)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          {highRiskPct > 0 && (
            <div
              title={`High Risk: ${highRiskCount} (${highRiskPct.toFixed(1)}%)`}
              onClick={() => onFilterChange(activeFilter === 'HIGH_RISK' ? 'ALL' : 'HIGH_RISK')}
              style={{
                width: `${highRiskPct}%`,
                backgroundColor: 'var(--status-highrisk)',
                cursor: 'pointer',
                transition: 'opacity 0.2s',
                opacity: activeFilter === 'ALL' || activeFilter === 'HIGH_RISK' ? 1 : 0.4,
              }}
            />
          )}
          {uninspectablePct > 0 && (
            <div
              title={`Uninspectable: ${uninspectableCount} (${uninspectablePct.toFixed(1)}%)`}
              onClick={() => onFilterChange(activeFilter === 'UNINSPECTABLE' ? 'ALL' : 'UNINSPECTABLE')}
              style={{
                width: `${uninspectablePct}%`,
                backgroundColor: 'var(--status-critical)',
                cursor: 'pointer',
                transition: 'opacity 0.2s',
                opacity: activeFilter === 'ALL' || activeFilter === 'UNINSPECTABLE' ? 1 : 0.4,
              }}
            />
          )}
          {suspiciousPct > 0 && (
            <div
              title={`Suspicious: ${suspiciousCount} (${suspiciousPct.toFixed(1)}%)`}
              onClick={() => onFilterChange(activeFilter === 'SUSPICIOUS' ? 'ALL' : 'SUSPICIOUS')}
              style={{
                width: `${suspiciousPct}%`,
                backgroundColor: 'var(--status-warning)',
                cursor: 'pointer',
                transition: 'opacity 0.2s',
                opacity: activeFilter === 'ALL' || activeFilter === 'SUSPICIOUS' ? 1 : 0.4,
              }}
            />
          )}
          {safePct > 0 && (
            <div
              title={`Safe: ${safeCount} (${safePct.toFixed(1)}%)`}
              onClick={() => onFilterChange(activeFilter === 'SAFE' ? 'ALL' : 'SAFE')}
              style={{
                width: `${safePct}%`,
                backgroundColor: 'var(--status-safe)',
                cursor: 'pointer',
                transition: 'opacity 0.2s',
                opacity: activeFilter === 'ALL' || activeFilter === 'SAFE' ? 1 : 0.4,
              }}
            />
          )}
          {failedPct > 0 && (
            <div
              title={`Failed: ${failedCount} (${failedPct.toFixed(1)}%)`}
              onClick={() => onFilterChange(activeFilter === 'FAILED' ? 'ALL' : 'FAILED')}
              style={{
                width: `${failedPct}%`,
                backgroundColor: 'var(--text-muted)',
                cursor: 'pointer',
                transition: 'opacity 0.2s',
                opacity: activeFilter === 'ALL' || activeFilter === 'FAILED' ? 1 : 0.4,
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};
