import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { AuditEvent } from '../api/types';
import { Card } from '../components/ui/Card';
import { LoadingState, EmptyState, ErrorState } from '../components/ui/States';

export const AuditPage: React.FC = () => {
  const [auditLogs, setAuditLogs] = useState<AuditEvent[]>([]);
  const [searchFilter, setSearchFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const logs = await api.listAuditLogs();
      setAuditLogs(logs);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch audit logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  if (loading) {
    return <LoadingState message="Fetching immutable multi-tenant audit trail..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchLogs} />;
  }

  const filteredLogs = auditLogs.filter(
    (l) =>
      l.event_type.toLowerCase().includes(searchFilter.toLowerCase()) ||
      l.details.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span>📜</span>
          <span>Immutable Multi-Tenant Audit Trail</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Tamper-evident log of all API accesses, security evaluations, key rotations, and policy actions.
        </p>
      </div>

      {/* Audit Log Table */}
      <Card title="Audit Event Explorer" subtitle={`${filteredLogs.length} events logged for current tenant`}>
        <div style={{ marginBottom: '16px' }}>
          <input
            type="text"
            placeholder="Search audit logs by event type or details..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            style={{
              width: '100%',
              backgroundColor: 'var(--bg-app)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 12px',
              fontSize: '0.8125rem',
              color: 'var(--text-primary)',
            }}
          />
        </div>

        {filteredLogs.length === 0 ? (
          <EmptyState title="No Audit Records" description="Zero audit events match the current search query." />
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px 8px' }}>Log ID</th>
                <th style={{ padding: '10px 8px' }}>Timestamp</th>
                <th style={{ padding: '10px 8px' }}>Event Type</th>
                <th style={{ padding: '10px 8px' }}>Tenant ID</th>
                <th style={{ padding: '10px 8px' }}>User / Client</th>
                <th style={{ padding: '10px 8px' }}>Event Details</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => (
                <tr key={log.log_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    #{log.log_id}
                  </td>
                  <td style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontSize: '0.75rem' }}>{log.timestamp}</td>
                  <td style={{ padding: '12px 8px', fontWeight: 700, color: 'var(--accent-cyan)' }}>{log.event_type}</td>
                  <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{log.tenant_id}</td>
                  <td style={{ padding: '12px 8px', color: 'var(--text-secondary)' }}>{log.user_id}</td>
                  <td style={{ padding: '12px 8px', fontSize: '0.8125rem' }}>{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
};
