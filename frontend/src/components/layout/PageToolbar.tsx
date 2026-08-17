import React from 'react';

export interface PageToolbarProps {
  leftControls?: React.ReactNode;
  rightControls?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const PageToolbar: React.FC<PageToolbarProps> = ({
  leftControls,
  rightControls,
  children,
  className = '',
  style,
}) => {
  return (
    <div
      className={`page-toolbar ${className}`.trim()}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        padding: '10px 14px',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-lg)',
        marginBottom: '18px',
        ...style,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', flex: 1 }}>
        {leftControls}
        {children}
      </div>

      {rightControls && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          {rightControls}
        </div>
      )}
    </div>
  );
};
