import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface MetricProps {
  label: string;
  value: string | number;
  delta?: string | number;
  trend?: 'up' | 'down' | 'neutral';
  trendLabel?: string;
  statusColor?: string;
  subtext?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Metric: React.FC<MetricProps> = ({
  label,
  value,
  delta,
  trend,
  trendLabel,
  statusColor,
  subtext,
  size = 'md',
  className = '',
}) => {
  const valueFontSize = size === 'sm' ? '1.25rem' : size === 'lg' ? '2rem' : '1.5rem';

  return (
    <div className={className} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
        <span
          style={{
            fontSize: valueFontSize,
            fontWeight: 800,
            color: statusColor || 'var(--text-primary)',
            letterSpacing: '-0.02em',
            fontFeatureSettings: '"tnum"',
          }}
        >
          {value}
        </span>

        {delta !== undefined && (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '2px',
              fontSize: '0.75rem',
              fontWeight: 700,
              color:
                trend === 'up'
                  ? 'var(--status-safe)'
                  : trend === 'down'
                  ? 'var(--status-highrisk)'
                  : 'var(--text-muted)',
            }}
          >
            {trend === 'up' && <TrendingUp size={12} />}
            {trend === 'down' && <TrendingDown size={12} />}
            {trend === 'neutral' && <Minus size={12} />}
            <span>{delta}</span>
            {trendLabel && <span style={{ color: 'var(--text-muted)', fontWeight: 500 }}>{trendLabel}</span>}
          </span>
        )}
      </div>

      {subtext && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {subtext}
        </div>
      )}
    </div>
  );
};
