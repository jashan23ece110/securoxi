import React from 'react';

export const LoadingState: React.FC<{ message?: string }> = ({ message = 'Loading security data...' }) => (
  <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-secondary)' }}>
    <div style={{ fontSize: '24px', marginBottom: '12px' }}>🔄</div>
    <p>{message}</p>
  </div>
);

export const EmptyState: React.FC<{ title?: string; description?: string }> = ({
  title = 'No records found',
  description = 'There are currently no security records matching this filter.',
}) => (
  <div style={{ padding: '48px', textAlign: 'center', border: '1px dashed var(--border-default)', borderRadius: 'var(--radius-lg)' }}>
    <div style={{ fontSize: '28px', marginBottom: '12px' }}>🛡️</div>
    <h4 style={{ color: 'var(--text-primary)', marginBottom: '4px' }}>{title}</h4>
    <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{description}</p>
  </div>
);

export const ErrorState: React.FC<{ message: string; onRetry?: () => void }> = ({ message, onRetry }) => (
  <div style={{ padding: '32px', textAlign: 'center', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--status-highrisk)' }}>
    <div style={{ fontSize: '28px', marginBottom: '8px' }}>⚠️</div>
    <h4 style={{ color: 'var(--status-highrisk)', marginBottom: '8px' }}>Failed to Load Data</h4>
    <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '16px' }}>{message}</p>
    {onRetry && (
      <button className="btn btn-secondary" onClick={onRetry}>
        Retry Connection
      </button>
    )}
  </div>
);
