import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';

interface HeaderProps {
  onToggleSidebar: () => void;
  selectedTenant: string;
  onSelectTenant: (tenantId: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar, selectedTenant, onSelectTenant }) => {
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Generate breadcrumb title from path
  const currentPath = location.pathname.substring(1) || 'overview';
  const formattedPath = currentPath.replace('-', ' ').toUpperCase();

  return (
    <header className="top-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle Sidebar Navigation"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            fontSize: '18px',
            cursor: 'pointer',
            padding: '4px',
          }}
        >
          ☰
        </button>

        {/* Breadcrumb */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8125rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>SECUROXI</span>
          <span style={{ color: 'var(--border-strong)' }}>/</span>
          <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{formattedPath}</span>
        </div>
      </div>

      {/* Center Global Search Entry Point */}
      <div className="search-container" style={{ position: 'relative', width: '320px' }}>
        <input
          type="text"
          placeholder="Search scans, incidents, candidates (Ctrl + K)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            backgroundColor: 'var(--bg-app)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '6px 12px',
            fontSize: '0.8125rem',
            color: 'var(--text-primary)',
            outline: 'none',
          }}
        />
      </div>

      {/* Right Controls: Tenant, Notifications, User */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Tenant Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Org:</span>
          <select
            value={selectedTenant}
            onChange={(e) => onSelectTenant(e.target.value)}
            style={{
              backgroundColor: 'var(--bg-surface-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '4px 8px',
              fontSize: '0.8125rem',
              fontWeight: 600,
            }}
          >
            <option value="TENANT-DEFAULT">TENANT-DEFAULT</option>
            <option value="TENANT-ALPHA">Alpha Security Org</option>
            <option value="TENANT-BETA">Beta Enterprise</option>
          </select>
        </div>

        {/* Notifications */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            aria-label="View System Security Notifications"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-secondary)',
              fontSize: '18px',
              cursor: 'pointer',
              position: 'relative',
            }}
          >
            🔔
            <span
              style={{
                position: 'absolute',
                top: '-2px',
                right: '-2px',
                width: '8px',
                height: '8px',
                backgroundColor: 'var(--status-highrisk)',
                borderRadius: '50%',
              }}
            />
          </button>

          {showNotifications && (
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: '32px',
                width: '280px',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '12px',
                boxShadow: 'var(--shadow-lg)',
                zIndex: 100,
              }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.875rem', marginBottom: '8px' }}>Security Notifications</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--status-highrisk)', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                🚨 High Risk Threat Blocked: Prompt injection in resume payload.
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--status-safe)', padding: '6px 0' }}>
                🟢 Continuous monitoring active across 3 ATS webhooks.
              </div>
            </div>
          )}
        </div>

        {/* User Profile */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            style={{
              background: 'none',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
            }}
          >
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                backgroundColor: 'var(--accent-indigo)',
                color: '#FFF',
                fontWeight: 700,
                fontSize: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              SA
            </div>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>Admin</span>
          </button>

          {showUserMenu && (
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: '36px',
                width: '180px',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '8px',
                boxShadow: 'var(--shadow-lg)',
                zIndex: 100,
              }}
            >
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', padding: '4px 8px' }}>Role: SUPER_ADMIN</div>
              <div style={{ height: '1px', backgroundColor: 'var(--border-subtle)', margin: '4px 0' }} />
              <button style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', color: 'var(--text-primary)', padding: '6px 8px', fontSize: '0.8125rem', cursor: 'pointer' }}>
                API Keys & Secrets
              </button>
              <button style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', color: 'var(--text-primary)', padding: '6px 8px', fontSize: '0.8125rem', cursor: 'pointer' }}>
                Audit Security Logs
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
