import React from 'react';
import { NavLink } from 'react-router-dom';

export interface NavGroup {
  groupName: string;
  items: {
    label: string;
    path: string;
    icon: string;
    badge?: string;
  }[];
}

const navGroups: NavGroup[] = [
  {
    groupName: 'SECURITY & DEFENSE',
    items: [
      { label: 'Overview', path: '/overview', icon: '📊' },
      { label: 'Security Brain', path: '/security-brain', icon: '🧠', badge: 'AI' },
      { label: 'Incidents', path: '/incidents', icon: '🚨', badge: 'LIVE' },
      { label: 'Scan Console', path: '/scans', icon: '🔍' },
    ],
  },
  {
    groupName: 'INTELLIGENCE & SCREENING',
    items: [
      { label: 'Candidate Screening', path: '/screening', icon: '👤' },
      { label: 'Documents', path: '/documents', icon: '📄' },
      { label: 'ATS Connectors', path: '/ats', icon: '⚡' },
      { label: 'Continuous Monitoring', path: '/monitoring', icon: '📈' },
    ],
  },
  {
    groupName: 'GOVERNANCE & CONTROL',
    items: [
      { label: 'Policy Engine', path: '/policies', icon: '🛡️' },
      { label: 'Audit Trail', path: '/audit', icon: '📜' },
      { label: 'Settings & Control', path: '/settings', icon: '⚙️' },
      { label: 'Design System', path: '/design-system', icon: '🎨' },
    ],
  },
];

export const Sidebar: React.FC<{ isOpen: boolean; onToggle: () => void }> = ({ isOpen }) => {
  return (
    <aside className={`sidebar-nav ${isOpen ? 'open' : 'collapsed'}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <div
          style={{
            width: '36px',
            height: '36px',
            background: 'linear-gradient(135deg, #6366F1, #06B6D4)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            color: '#FFF',
            boxShadow: '0 0 12px rgba(6, 182, 212, 0.3)',
          }}
        >
          SX
        </div>
        <div className="brand-text">
          <div style={{ fontWeight: 800, fontSize: '1.125rem', letterSpacing: '0.5px' }}>SECUROXI</div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
            Enterprise AI Defense
          </div>
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
        {navGroups.map((group) => (
          <div key={group.groupName}>
            <div
              className="nav-group-title"
              style={{
                fontSize: '0.6875rem',
                fontWeight: 700,
                color: 'var(--text-muted)',
                letterSpacing: '1px',
                marginBottom: '8px',
                paddingLeft: '8px',
              }}
            >
              {group.groupName}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  style={({ isActive }) => ({
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    color: isActive ? '#FFF' : 'var(--text-secondary)',
                    backgroundColor: isActive ? 'var(--bg-surface-elevated)' : 'transparent',
                    borderLeft: isActive ? '3px solid var(--accent-cyan)' : '3px solid transparent',
                    textDecoration: 'none',
                    fontSize: '0.875rem',
                    fontWeight: isActive ? 600 : 500,
                  })}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span>{item.icon}</span>
                    <span className="nav-label">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      style={{
                        fontSize: '0.625rem',
                        fontWeight: 800,
                        backgroundColor: item.badge === 'LIVE' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(6, 182, 212, 0.2)',
                        color: item.badge === 'LIVE' ? '#EF4444' : '#06B6D4',
                        padding: '2px 6px',
                        borderRadius: '4px',
                      }}
                    >
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
};
