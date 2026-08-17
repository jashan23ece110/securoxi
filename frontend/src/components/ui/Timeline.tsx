import React from 'react';

export interface TimelineItem {
  id: string | number;
  title: string;
  timestamp: string;
  description?: string;
  badge?: React.ReactNode;
  icon?: React.ReactNode;
  statusColor?: string;
}

export interface TimelineProps {
  items: TimelineItem[];
  className?: string;
}

export const Timeline: React.FC<TimelineProps> = ({ items, className = '' }) => {
  return (
    <div className={className} style={{ display: 'flex', flexDirection: 'column', gap: '0px' }}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        return (
          <div
            key={item.id}
            style={{
              display: 'flex',
              gap: '14px',
              position: 'relative',
              paddingBottom: isLast ? '0' : '20px',
            }}
          >
            {/* Timeline Vertical Track Line */}
            {!isLast && (
              <div
                style={{
                  position: 'absolute',
                  left: '11px',
                  top: '20px',
                  bottom: '0',
                  width: '2px',
                  backgroundColor: 'var(--border-subtle)',
                }}
              />
            )}

            {/* Icon / Bullet Dot */}
            <div
              style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: item.statusColor ? `${item.statusColor}22` : 'var(--bg-surface-elevated)',
                border: `2px solid ${item.statusColor || 'var(--border-default)'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 2,
                flexShrink: 0,
                color: item.statusColor || 'var(--text-primary)',
              }}
            >
              {item.icon ? (
                <span style={{ fontSize: '10px' }}>{item.icon}</span>
              ) : (
                <div
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor: item.statusColor || 'var(--accent-cyan)',
                  }}
                />
              )}
            </div>

            {/* Event Content */}
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
                    {item.title}
                  </span>
                  {item.badge}
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFeatureSettings: '"tnum"' }}>
                  {item.timestamp}
                </span>
              </div>

              {item.description && (
                <div
                  style={{
                    fontSize: '0.8125rem',
                    color: 'var(--text-secondary)',
                    marginTop: '4px',
                    lineHeight: 1.5,
                  }}
                >
                  {item.description}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
