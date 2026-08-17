import React from 'react';

export interface CardProps {
  title?: string;
  subtitle?: string;
  badge?: React.ReactNode;
  action?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'interactive';
  className?: string;
  style?: React.CSSProperties;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  badge,
  action,
  footer,
  children,
  variant = 'default',
  className = '',
  style,
  onClick,
}) => {
  const variantClass = variant === 'elevated' ? 'card-elevated' : variant === 'interactive' ? 'card-interactive' : '';

  return (
    <div
      className={`card ${variantClass} ${className}`.trim()}
      style={style}
      onClick={onClick}
    >
      {(title || subtitle || badge || action) && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '12px',
            marginBottom: '16px',
            paddingBottom: subtitle ? '0' : '4px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {title && (
                <h3
                  style={{
                    fontSize: '1rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    letterSpacing: '-0.01em',
                  }}
                >
                  {title}
                </h3>
              )}
              {badge}
            </div>
            {subtitle && (
              <p
                style={{
                  fontSize: '0.8125rem',
                  color: 'var(--text-secondary)',
                  marginTop: '2px',
                }}
              >
                {subtitle}
              </p>
            )}
          </div>
          {action && <div style={{ flexShrink: 0 }}>{action}</div>}
        </div>
      )}

      <div>{children}</div>

      {footer && (
        <div
          style={{
            marginTop: '16px',
            paddingTop: '12px',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.8125rem',
            color: 'var(--text-secondary)',
          }}
        >
          {footer}
        </div>
      )}
    </div>
  );
};

export interface StatCardProps {
  label: string;
  value: string | number;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  icon?: React.ReactNode;
  statusBadge?: React.ReactNode;
  subtitle?: string;
  className?: string;
  style?: React.CSSProperties;
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  delta,
  deltaType = 'neutral',
  icon,
  statusBadge,
  subtitle,
  className = '',
  style,
  onClick,
}) => {
  const deltaColor =
    deltaType === 'positive'
      ? 'var(--status-safe)'
      : deltaType === 'negative'
      ? 'var(--status-highrisk)'
      : 'var(--text-muted)';

  return (
    <Card className={className} style={style} onClick={onClick}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            color: 'var(--text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          {label}
        </span>
        {icon && <span style={{ color: 'var(--text-muted)', display: 'flex' }}>{icon}</span>}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '4px' }}>
        <span
          style={{
            fontSize: '1.75rem',
            fontWeight: 800,
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em',
            fontFeatureSettings: '"tnum"',
          }}
        >
          {value}
        </span>
        {delta && (
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: deltaColor }}>
            {delta}
          </span>
        )}
      </div>

      {(subtitle || statusBadge) && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px' }}>
          {subtitle && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {subtitle}
            </span>
          )}
          {statusBadge}
        </div>
      )}
    </Card>
  );
};
