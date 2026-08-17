import React from 'react';

export interface RiskIndicatorProps {
  score: number;
  maxScore?: number;
  showLabel?: boolean;
  showBar?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const RiskIndicator: React.FC<RiskIndicatorProps> = ({
  score,
  maxScore = 100,
  showLabel = true,
  showBar = true,
  size = 'md',
  className = '',
}) => {
  const percentage = Math.min(100, Math.max(0, (score / maxScore) * 100));

  const getColor = (s: number) => {
    if (s >= 70) return 'var(--status-highrisk)';
    if (s >= 35) return 'var(--status-suspicious)';
    return 'var(--status-safe)';
  };

  const color = getColor(score);

  const getVerdictLabel = (s: number) => {
    if (s >= 70) return 'HIGH RISK';
    if (s >= 35) return 'SUSPICIOUS';
    return 'SAFE';
  };

  const height = size === 'sm' ? 4 : size === 'lg' ? 8 : 6;
  const fontSize = size === 'sm' ? '0.75rem' : size === 'lg' ? '1rem' : '0.8125rem';

  return (
    <div className={className} style={{ width: '100%' }}>
      {showLabel && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            marginBottom: '4px',
            fontSize,
          }}
        >
          <span style={{ fontWeight: 700, color, fontFeatureSettings: '"tnum"' }}>
            Risk Score: {score}/{maxScore}
          </span>
          <span style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            {getVerdictLabel(score)}
          </span>
        </div>
      )}

      {showBar && (
        <div
          style={{
            width: '100%',
            height: `${height}px`,
            backgroundColor: 'var(--bg-surface-elevated)',
            borderRadius: 'var(--radius-full)',
            overflow: 'hidden',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              width: `${percentage}%`,
              height: '100%',
              backgroundColor: color,
              borderRadius: 'var(--radius-full)',
              transition: 'width var(--transition-normal)',
            }}
          />
        </div>
      )}
    </div>
  );
};
