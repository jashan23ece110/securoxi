import React from 'react';

interface AlertProps {
  type?: 'info' | 'success' | 'warning' | 'danger';
  title?: string;
  children: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({ type = 'info', title, children }) => {
  const styles: Record<string, { bg: string; border: string; text: string }> = {
    info: { bg: 'rgba(59, 130, 246, 0.1)', border: '#3B82F6', text: '#93C5FD' },
    success: { bg: 'rgba(16, 185, 129, 0.1)', border: '#10B981', text: '#6EE7B7' },
    warning: { bg: 'rgba(245, 158, 11, 0.1)', border: '#F59E0B', text: '#FDE68A' },
    danger: { bg: 'rgba(239, 68, 68, 0.1)', border: '#EF4444', text: '#FCA5A5' },
  };

  const s = styles[type];

  return (
    <div
      style={{
        backgroundColor: s.bg,
        borderLeft: `4px solid ${s.border}`,
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-4)',
        marginBottom: 'var(--space-4)',
        color: s.text,
      }}
    >
      {title && <div style={{ fontWeight: 700, marginBottom: '4px' }}>{title}</div>}
      <div style={{ fontSize: '0.875rem' }}>{children}</div>
    </div>
  );
};
