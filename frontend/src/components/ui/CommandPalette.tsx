import React, { useState, useEffect } from 'react';
import { Search, ShieldAlert, FileText, UserCheck, Settings, X, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  const actions = [
    { label: 'Security Overview', path: '/overview', category: 'SECURITY', icon: <Search size={14} /> },
    { label: 'Security Brain & Attack Graphs', path: '/security-brain', category: 'SECURITY', icon: <ShieldAlert size={14} /> },
    { label: 'Incident Response Queue', path: '/incidents', category: 'SECURITY', icon: <ShieldAlert size={14} /> },
    { label: 'Run Document Security Scan', path: '/scans', category: 'DOCUMENTS', icon: <FileText size={14} /> },
    { label: 'Candidate Fit Screening', path: '/screening', category: 'HIRING', icon: <UserCheck size={14} /> },
    { label: 'Continuous Event Monitoring', path: '/monitoring', category: 'SECURITY', icon: <Search size={14} /> },
    { label: 'Security Policies & Governance', path: '/policies', category: 'GOVERNANCE', icon: <Settings size={14} /> },
    { label: 'Audit Trail & Compliance Logs', path: '/audit', category: 'GOVERNANCE', icon: <FileText size={14} /> },
    { label: 'Tenant Settings & API Keys', path: '/settings', category: 'GOVERNANCE', icon: <Settings size={14} /> },
    { label: 'Design System Showcase', path: '/design-system', category: 'SYSTEM', icon: <Settings size={14} /> },
  ];

  const filtered = actions.filter((a) =>
    a.label.toLowerCase().includes(query.toLowerCase()) ||
    a.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % (filtered.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + (filtered.length || 1)) % (filtered.length || 1));
      } else if (e.key === 'Enter') {
        if (filtered[selectedIndex]) {
          navigate(filtered[selectedIndex].path);
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filtered, selectedIndex, navigate, onClose]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'var(--bg-overlay)',
        backdropFilter: 'blur(4px)',
        zIndex: 'var(--z-modal)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '15vh',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '560px',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-xl)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            borderBottom: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-surface-elevated)',
          }}
        >
          <Search size={18} style={{ color: 'var(--accent-cyan)' }} />
          <input
            type="text"
            autoFocus
            placeholder="Type a command or jump to page..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            style={{
              flex: 1,
              background: 'none',
              border: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.9375rem',
              outline: 'none',
            }}
          />
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Results List */}
        <div style={{ maxHeight: '320px', overflowY: 'auto', padding: '6px' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
              No commands or pages matching "{query}"
            </div>
          ) : (
            filtered.map((item, index) => {
              const isSelected = index === selectedIndex;
              return (
                <div
                  key={item.path}
                  onClick={() => {
                    navigate(item.path);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: isSelected ? 'var(--bg-surface-hover)' : 'transparent',
                    cursor: 'pointer',
                    color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
                    transition: 'all var(--transition-fast)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: isSelected ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
                      {item.icon}
                    </span>
                    <span style={{ fontSize: '0.875rem', fontWeight: isSelected ? 600 : 500 }}>
                      {item.label}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        fontSize: '0.6875rem',
                        fontWeight: 600,
                        color: 'var(--text-muted)',
                        backgroundColor: 'var(--bg-surface-elevated)',
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-xs)',
                      }}
                    >
                      {item.category}
                    </span>
                    {isSelected && <ArrowRight size={14} style={{ color: 'var(--accent-cyan)' }} />}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 16px',
            borderTop: '1px solid var(--border-subtle)',
            backgroundColor: '#070B14',
            fontSize: '0.6875rem',
            color: 'var(--text-muted)',
          }}
        >
          <div>
            Use <kbd style={{ padding: '1px 4px', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '2px' }}>↑</kbd>{' '}
            <kbd style={{ padding: '1px 4px', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '2px' }}>↓</kbd> to navigate,{' '}
            <kbd style={{ padding: '1px 4px', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '2px' }}>↵</kbd> to select
          </div>
          <div>
            <kbd style={{ padding: '1px 4px', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '2px' }}>ESC</kbd> to close
          </div>
        </div>
      </div>
    </div>
  );
};
