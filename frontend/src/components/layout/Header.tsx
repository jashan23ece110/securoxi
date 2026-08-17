import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Menu,
  Search,
  Bell,
  Building2,
  ChevronDown,
  ShieldCheck,
  Key,
  ShieldAlert,
  Sliders,
  Check,
} from 'lucide-react';
import { IconButton } from '../ui/IconButton';

export interface HeaderProps {
  onToggleSidebar: () => void;
  selectedTenant: string;
  onSelectTenant: (tenantId: string) => void;
  onOpenCommandPalette: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onToggleSidebar,
  selectedTenant,
  onSelectTenant,
  onOpenCommandPalette,
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showTenantMenu, setShowTenantMenu] = useState(false);

  const notifRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);
  const tenantRef = useRef<HTMLDivElement>(null);

  // Close menus on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
      if (userRef.current && !userRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
      if (tenantRef.current && !tenantRef.current.contains(event.target as Node)) {
        setShowTenantMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Generate breadcrumb title from path
  const currentPath = location.pathname.substring(1) || 'overview';
  const pathParts = currentPath.split('/');
  const formattedPath = pathParts[0].replace(/-/g, ' ').toUpperCase();

  const getSectionName = (path: string) => {
    if (['overview', 'security-brain', 'incidents', 'monitoring'].includes(path)) return 'SECURITY';
    if (['scans', 'documents'].includes(path)) return 'DOCUMENTS';
    if (['screening', 'ats'].includes(path)) return 'HIRING';
    return 'GOVERNANCE';
  };

  const sectionName = getSectionName(pathParts[0]);

  return (
    <header className="top-header">
      {/* Left: Sidebar toggle & Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <IconButton
          icon={<Menu size={18} />}
          aria-label="Toggle Navigation"
          onClick={onToggleSidebar}
          size="sm"
        />

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8125rem' }}>
          <span style={{ color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.75rem', letterSpacing: '0.04em' }}>
            {sectionName}
          </span>
          <span style={{ color: 'var(--border-strong)' }}>/</span>
          <span style={{ fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
            {formattedPath}
          </span>
        </div>
      </div>

      {/* Center: Global Search & Command Palette Trigger (Cmd+K) */}
      <div className="search-container">
        <button
          onClick={onOpenCommandPalette}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: '340px',
            backgroundColor: 'var(--bg-input)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '6px 12px',
            color: 'var(--text-secondary)',
            fontSize: '0.8125rem',
            cursor: 'pointer',
            transition: 'border-color var(--transition-fast)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--border-strong)')}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-default)')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Search size={14} style={{ color: 'var(--text-muted)' }} />
            <span>Search or jump to...</span>
          </div>
          <kbd
            style={{
              padding: '2px 6px',
              backgroundColor: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-xs)',
              fontSize: '0.6875rem',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right Controls: Tenant, Notifications, User */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Tenant Selector Dropdown */}
        <div ref={tenantRef} style={{ position: 'relative' }}>
          <button
            onClick={() => setShowTenantMenu(!showTenantMenu)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '4px 10px',
              color: 'var(--text-primary)',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <Building2 size={13} style={{ color: 'var(--accent-cyan)' }} />
            <span>{selectedTenant}</span>
            <ChevronDown size={12} style={{ color: 'var(--text-muted)' }} />
          </button>

          {showTenantMenu && (
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: '34px',
                width: '210px',
                backgroundColor: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '6px',
                boxShadow: 'var(--shadow-xl)',
                zIndex: 'var(--z-dropdown)',
              }}
            >
              <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)', padding: '4px 8px', textTransform: 'uppercase' }}>
                Active Tenant Scope
              </div>
              {['TENANT-DEFAULT', 'TENANT-ALPHA', 'TENANT-BETA'].map((t) => (
                <button
                  key={t}
                  onClick={() => {
                    onSelectTenant(t);
                    setShowTenantMenu(false);
                  }}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: selectedTenant === t ? 'var(--bg-surface-hover)' : 'none',
                    border: 'none',
                    color: selectedTenant === t ? 'var(--accent-cyan)' : 'var(--text-primary)',
                    padding: '6px 8px',
                    fontSize: '0.75rem',
                    fontWeight: selectedTenant === t ? 700 : 500,
                    borderRadius: 'var(--radius-xs)',
                    cursor: 'pointer',
                  }}
                >
                  <span>{t}</span>
                  {selectedTenant === t && <Check size={12} />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Notifications Dropdown */}
        <div ref={notifRef} style={{ position: 'relative' }}>
          <IconButton
            icon={
              <div style={{ position: 'relative', display: 'flex' }}>
                <Bell size={16} />
                <span
                  style={{
                    position: 'absolute',
                    top: '-2px',
                    right: '-2px',
                    width: '6px',
                    height: '6px',
                    backgroundColor: 'var(--status-highrisk)',
                    borderRadius: '50%',
                  }}
                />
              </div>
            }
            aria-label="View security notifications"
            onClick={() => setShowNotifications(!showNotifications)}
            size="sm"
          />

          {showNotifications && (
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: '36px',
                width: '320px',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-xl)',
                zIndex: 'var(--z-dropdown)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  padding: '10px 14px',
                  backgroundColor: 'var(--bg-surface-elevated)',
                  borderBottom: '1px solid var(--border-subtle)',
                  fontWeight: 700,
                  fontSize: '0.8125rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span>Live Security Alerts</span>
                <span style={{ fontSize: '0.6875rem', color: 'var(--accent-cyan)' }}>Real-Time SOC</span>
              </div>
              <div style={{ padding: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div
                  style={{
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--status-critical-bg)',
                    border: '1px solid var(--status-critical-border)',
                    fontSize: '0.75rem',
                  }}
                >
                  <div style={{ fontWeight: 700, color: 'var(--status-highrisk)', marginBottom: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldAlert size={12} />
                    High-Risk Injection Neutralized
                  </div>
                  <div style={{ color: '#FECACA', fontSize: '0.6875rem' }}>
                    Candidate PDF contained concealed prompt injection payload.
                  </div>
                </div>
                <div
                  style={{
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--status-safe-bg)',
                    border: '1px solid var(--status-safe-border)',
                    fontSize: '0.75rem',
                  }}
                >
                  <div style={{ fontWeight: 700, color: 'var(--status-safe)', marginBottom: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldCheck size={12} />
                    Multi-Tenant Isolation Verified
                  </div>
                  <div style={{ color: '#A7F3D0', fontSize: '0.6875rem' }}>
                    100% strict tenant boundary enforced across vector store and database.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile */}
        <div ref={userRef} style={{ position: 'relative' }}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            style={{
              background: 'none',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              padding: '2px 4px',
              borderRadius: 'var(--radius-md)',
            }}
          >
            <div
              style={{
                width: '26px',
                height: '26px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--accent-indigo)',
                color: '#FFF',
                fontWeight: 700,
                fontSize: '11px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              SA
            </div>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              SuperAdmin
            </span>
          </button>

          {showUserMenu && (
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: '36px',
                width: '200px',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '6px',
                boxShadow: 'var(--shadow-xl)',
                zIndex: 'var(--z-dropdown)',
              }}
            >
              <div style={{ padding: '6px 8px', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                Role: <strong style={{ color: 'var(--accent-cyan)' }}>SUPER_ADMIN</strong>
              </div>
              <div style={{ height: '1px', backgroundColor: 'var(--border-subtle)', margin: '4px 0' }} />
              <button
                onClick={() => {
                  navigate('/settings');
                  setShowUserMenu(false);
                }}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-primary)',
                  padding: '6px 8px',
                  fontSize: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  borderRadius: 'var(--radius-xs)',
                }}
              >
                <Key size={13} />
                <span>API Keys & Secrets</span>
              </button>
              <button
                onClick={() => {
                  navigate('/policies');
                  setShowUserMenu(false);
                }}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-primary)',
                  padding: '6px 8px',
                  fontSize: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  borderRadius: 'var(--radius-xs)',
                }}
              >
                <Sliders size={13} />
                <span>Tenant Governance</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
