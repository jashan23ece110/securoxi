import React, { useEffect, useRef } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Brain,
  ShieldAlert,
  Activity,
  FileSearch,
  FileText,
  UserCheck,
  Zap,
  ShieldCheck,
  ScrollText,
  Settings,
  Palette,
  Shield,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import { Tooltip } from '../ui/Tooltip';

export interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  badge?: string;
  badgeVariant?: 'live' | 'ai' | 'info';
}

export interface NavGroup {
  groupName: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    groupName: 'SECURITY',
    items: [
      { label: 'Overview', path: '/overview', icon: <LayoutDashboard size={17} /> },
      { label: 'Security Brain', path: '/security-brain', icon: <Brain size={17} />, badge: 'AI', badgeVariant: 'ai' },
      { label: 'Incidents', path: '/incidents', icon: <ShieldAlert size={17} />, badge: 'LIVE', badgeVariant: 'live' },
      { label: 'Monitoring', path: '/monitoring', icon: <Activity size={17} /> },
    ],
  },
  {
    groupName: 'DOCUMENTS',
    items: [
      { label: 'Scan Console', path: '/scans', icon: <FileSearch size={17} /> },
      { label: 'Documents', path: '/documents', icon: <FileText size={17} /> },
    ],
  },
  {
    groupName: 'HIRING',
    items: [
      { label: 'Screening', path: '/screening', icon: <UserCheck size={17} /> },
      { label: 'ATS Connectors', path: '/ats', icon: <Zap size={17} /> },
    ],
  },
  {
    groupName: 'GOVERNANCE',
    items: [
      { label: 'Policies', path: '/policies', icon: <ShieldCheck size={17} /> },
      { label: 'Audit Trail', path: '/audit', icon: <ScrollText size={17} /> },
      { label: 'Settings', path: '/settings', icon: <Settings size={17} /> },
      { label: 'Design System', path: '/design-system', icon: <Palette size={17} /> },
    ],
  },
];

export interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  isMobile?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  isMobile = false,
  onCloseMobile,
}) => {
  const location = useLocation();
  const navRef = useRef<HTMLDivElement>(null);

  // Close mobile drawer on route change
  useEffect(() => {
    if (isMobile && onCloseMobile) {
      onCloseMobile();
    }
  }, [location.pathname]);

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isMobile && isOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'var(--bg-overlay)',
            backdropFilter: 'blur(3px)',
            zIndex: 'var(--z-drawer)',
          }}
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`sidebar-nav ${isOpen ? 'open' : 'collapsed'}`}
        style={{
          position: isMobile ? 'fixed' : 'sticky',
          top: 0,
          left: 0,
          bottom: 0,
          height: '100vh',
          zIndex: isMobile ? 'calc(var(--z-drawer) + 1)' : 'var(--z-sticky)',
          transform: isMobile && !isOpen ? 'translateX(-100%)' : 'none',
          boxShadow: isMobile && isOpen ? 'var(--shadow-xl)' : undefined,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Brand Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: isOpen ? 'space-between' : 'center',
            padding: '16px 14px',
            borderBottom: '1px solid var(--border-subtle)',
            height: '56px',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                backgroundColor: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-cyan)',
                boxShadow: '0 0 10px rgba(6, 182, 212, 0.2)',
                flexShrink: 0,
              }}
            >
              <Shield size={18} />
            </div>

            {isOpen && (
              <div>
                <div style={{ fontWeight: 800, fontSize: '0.9375rem', letterSpacing: '0.04em', color: 'var(--text-primary)' }}>
                  SECUROXI
                </div>
                <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  AI Defense & SOC
                </div>
              </div>
            )}
          </div>

          {/* Desktop Toggle or Mobile Close */}
          {isMobile ? (
            <button
              onClick={onCloseMobile}
              aria-label="Close Navigation"
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
              }}
            >
              <X size={18} />
            </button>
          ) : (
            <button
              onClick={onToggle}
              aria-label={isOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '4px',
                display: isOpen ? 'flex' : 'none',
                borderRadius: 'var(--radius-xs)',
              }}
            >
              <ChevronLeft size={16} />
            </button>
          )}
        </div>

        {/* Navigation Links */}
        <nav
          ref={navRef}
          aria-label="Primary Platform Navigation"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            padding: '16px 8px',
            flex: 1,
            overflowY: 'auto',
          }}
        >
          {NAV_GROUPS.map((group) => (
            <div key={group.groupName}>
              {isOpen && (
                <div
                  style={{
                    fontSize: '0.625rem',
                    fontWeight: 700,
                    color: 'var(--text-muted)',
                    letterSpacing: '0.08em',
                    marginBottom: '6px',
                    paddingLeft: '10px',
                    textTransform: 'uppercase',
                  }}
                >
                  {group.groupName}
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {group.items.map((item) => {
                  const linkElement = (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      style={({ isActive }) => ({
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: isOpen ? 'space-between' : 'center',
                        padding: '8px 10px',
                        borderRadius: 'var(--radius-md)',
                        color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                        backgroundColor: isActive ? 'var(--bg-surface-elevated)' : 'transparent',
                        borderLeft: isActive ? '3px solid var(--accent-cyan)' : '3px solid transparent',
                        textDecoration: 'none',
                        fontSize: '0.8125rem',
                        fontWeight: isActive ? 600 : 500,
                        transition: 'all var(--transition-fast)',
                      })}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ display: 'flex' }}>{item.icon}</span>
                        {isOpen && <span>{item.label}</span>}
                      </div>

                      {isOpen && item.badge && (
                        <span
                          style={{
                            fontSize: '0.625rem',
                            fontWeight: 800,
                            backgroundColor:
                              item.badgeVariant === 'live'
                                ? 'var(--status-critical-bg)'
                                : 'var(--accent-cyan-bg)',
                            color:
                              item.badgeVariant === 'live'
                                ? 'var(--status-highrisk)'
                                : 'var(--accent-cyan)',
                            padding: '1px 5px',
                            borderRadius: 'var(--radius-xs)',
                            border: `1px solid ${
                              item.badgeVariant === 'live'
                                ? 'var(--status-critical-border)'
                                : 'var(--border-glow-cyan)'
                            }`,
                          }}
                        >
                          {item.badge}
                        </span>
                      )}
                    </NavLink>
                  );

                  if (!isOpen) {
                    return (
                      <Tooltip key={item.path} content={item.label} position="right">
                        {linkElement}
                      </Tooltip>
                    );
                  }

                  return linkElement;
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer System Status Indicator */}
        <div
          style={{
            padding: '12px 14px',
            borderTop: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-app)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: isOpen ? 'space-between' : 'center',
            fontSize: '0.6875rem',
            color: 'var(--text-muted)',
            flexShrink: 0,
          }}
        >
          {isOpen ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="pulse-live" />
                <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>SOC Engine Active</span>
              </div>
              <span style={{ fontFeatureSettings: '"tnum"' }}>v1.0.0</span>
            </>
          ) : (
            <button
              onClick={onToggle}
              aria-label="Expand Sidebar"
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
              }}
            >
              <ChevronRight size={16} />
            </button>
          )}
        </div>
      </aside>
    </>
  );
};
