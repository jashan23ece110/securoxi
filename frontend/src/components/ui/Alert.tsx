import React from 'react';
import { AlertTriangle, CheckCircle, Info, XCircle, X } from 'lucide-react';

export type AlertType = 'info' | 'success' | 'warning' | 'danger' | 'critical';

export interface AlertProps {
  type?: AlertType;
  title?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
  onDismiss?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  children,
  icon,
  onDismiss,
  className = '',
  style,
}) => {
  const configMap: Record<
    AlertType,
    { bg: string; border: string; text: string; defaultIcon: React.ReactNode }
  > = {
    info: {
      bg: 'var(--status-info-bg)',
      border: 'var(--status-info)',
      text: '#BAE6FD',
      defaultIcon: <Info size={16} color="var(--status-info)" />,
    },
    success: {
      bg: 'var(--status-safe-bg)',
      border: 'var(--status-safe)',
      text: '#A7F3D0',
      defaultIcon: <CheckCircle size={16} color="var(--status-safe)" />,
    },
    warning: {
      bg: 'var(--status-suspicious-bg)',
      border: 'var(--status-suspicious)',
      text: '#FDE68A',
      defaultIcon: <AlertTriangle size={16} color="var(--status-suspicious)" />,
    },
    danger: {
      bg: 'var(--status-highrisk-bg)',
      border: 'var(--status-highrisk)',
      text: '#FECACA',
      defaultIcon: <XCircle size={16} color="var(--status-highrisk)" />,
    },
    critical: {
      bg: 'var(--status-critical-bg)',
      border: 'var(--status-critical)',
      text: '#FCA5A5',
      defaultIcon: <XCircle size={16} color="var(--status-critical)" />,
    },
  };

  const config = configMap[type] || configMap.info;

  return (
    <div
      role="alert"
      className={className}
      style={{
        backgroundColor: config.bg,
        border: `1px solid ${config.border}`,
        borderLeft: `4px solid ${config.border}`,
        borderRadius: 'var(--radius-md)',
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        position: 'relative',
        ...style,
      }}
    >
      <div style={{ flexShrink: 0, marginTop: '2px' }}>
        {icon || config.defaultIcon}
      </div>

      <div style={{ flex: 1, color: config.text }}>
        {title && (
          <div style={{ fontWeight: 700, fontSize: '0.875rem', marginBottom: '2px' }}>
            {title}
          </div>
        )}
        <div style={{ fontSize: '0.8125rem', lineHeight: 1.5, color: config.text }}>
          {children}
        </div>
      </div>

      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label="Dismiss alert"
          style={{
            background: 'none',
            border: 'none',
            color: config.text,
            cursor: 'pointer',
            opacity: 0.7,
            padding: '2px',
            display: 'flex',
          }}
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
};
