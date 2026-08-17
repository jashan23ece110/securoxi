import React from 'react';
import { Loader2, AlertOctagon, Inbox, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export interface LoadingStateProps {
  message?: string;
  subMessage?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading security data...',
  subMessage,
  size = 'md',
}) => {
  const iconSize = size === 'sm' ? 20 : size === 'lg' ? 36 : 24;

  return (
    <div
      style={{
        padding: size === 'sm' ? '24px' : '48px 24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '12px',
        color: 'var(--text-secondary)',
        textAlign: 'center',
      }}
    >
      <Loader2
        className="animate-spin"
        size={iconSize}
        style={{ color: 'var(--accent-cyan)' }}
      />
      <div>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
          {message}
        </div>
        {subMessage && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            {subMessage}
          </div>
        )}
      </div>
    </div>
  );
};

export interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  description = 'There are currently no security records matching this filter.',
  icon,
  action,
  className = '',
}) => {
  return (
    <div
      className={className}
      style={{
        padding: '48px 24px',
        textAlign: 'center',
        border: '1px dashed var(--border-default)',
        borderRadius: 'var(--radius-lg)',
        backgroundColor: 'rgba(12, 18, 30, 0.4)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          width: '48px',
          height: '48px',
          borderRadius: '50%',
          backgroundColor: 'var(--bg-surface-elevated)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          marginBottom: '16px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {icon || <Inbox size={22} />}
      </div>
      <h4 style={{ color: 'var(--text-primary)', fontSize: '0.9375rem', fontWeight: 700, marginBottom: '6px' }}>
        {title}
      </h4>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', maxWidth: '420px', lineHeight: 1.5, marginBottom: action ? '16px' : '0' }}>
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
};

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  action?: React.ReactNode;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to Load Security Data',
  message,
  onRetry,
  action,
}) => {
  return (
    <div
      style={{
        padding: '32px 24px',
        textAlign: 'center',
        backgroundColor: 'var(--status-critical-bg)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--status-critical-border)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div style={{ color: 'var(--status-highrisk)', marginBottom: '12px' }}>
        <AlertOctagon size={32} />
      </div>
      <h4 style={{ color: 'var(--status-highrisk)', fontWeight: 700, fontSize: '1rem', marginBottom: '6px' }}>
        {title}
      </h4>
      <p style={{ color: '#FECACA', fontSize: '0.8125rem', maxWidth: '480px', marginBottom: '16px', lineHeight: 1.5 }}>
        {message}
      </p>
      <div style={{ display: 'flex', gap: '8px' }}>
        {onRetry && (
          <Button
            variant="secondary"
            size="sm"
            onClick={onRetry}
            icon={<RefreshCw size={14} />}
          >
            Retry Connection
          </Button>
        )}
        {action}
      </div>
    </div>
  );
};

export const Skeleton: React.FC<{ width?: string; height?: string; borderRadius?: string }> = ({
  width = '100%',
  height = '16px',
  borderRadius = 'var(--radius-xs)',
}) => {
  return (
    <div
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: 'var(--bg-surface-elevated)',
        opacity: 0.6,
      }}
    />
  );
};
