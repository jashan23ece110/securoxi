import React from 'react';

export interface TabItem {
  id: string;
  label: string;
  count?: number | string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  variant?: 'line' | 'pill';
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  variant = 'line',
  className = '',
}) => {
  return (
    <div
      role="tablist"
      className={className}
      style={{
        display: 'flex',
        gap: variant === 'pill' ? '6px' : '16px',
        borderBottom: variant === 'line' ? '1px solid var(--border-subtle)' : undefined,
        paddingBottom: variant === 'line' ? '2px' : undefined,
        overflowX: 'auto',
      }}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            disabled={tab.disabled}
            onClick={() => onChange(tab.id)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: variant === 'pill' ? '6px 12px' : '8px 4px',
              fontSize: '0.8125rem',
              fontWeight: isActive ? 700 : 500,
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              backgroundColor:
                variant === 'pill'
                  ? isActive
                    ? 'var(--bg-surface-elevated)'
                    : 'transparent'
                  : 'transparent',
              border: variant === 'pill' ? '1px solid' : 'none',
              borderColor:
                variant === 'pill'
                  ? isActive
                    ? 'var(--border-default)'
                    : 'transparent'
                  : undefined,
              borderBottom:
                variant === 'line'
                  ? isActive
                    ? '2px solid var(--accent-cyan)'
                    : '2px solid transparent'
                  : undefined,
              borderRadius: variant === 'pill' ? 'var(--radius-md)' : undefined,
              cursor: tab.disabled ? 'not-allowed' : 'pointer',
              opacity: tab.disabled ? 0.4 : 1,
              whiteSpace: 'nowrap',
              transition: 'all var(--transition-fast)',
            }}
          >
            {tab.icon && <span style={{ display: 'flex' }}>{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                style={{
                  fontSize: '0.6875rem',
                  fontWeight: 700,
                  padding: '1px 6px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: isActive ? 'var(--accent-cyan-bg)' : 'var(--bg-surface-elevated)',
                  color: isActive ? 'var(--accent-cyan)' : 'var(--text-muted)',
                }}
              >
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
