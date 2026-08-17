import React from 'react';

export interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  size?: 'sm' | 'md';
}

export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  size = 'md',
}) => {
  const width = size === 'sm' ? 32 : 40;
  const height = size === 'sm' ? 18 : 22;
  const knobSize = size === 'sm' ? 14 : 18;
  const translateDist = size === 'sm' ? 14 : 18;

  return (
    <label
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        userSelect: 'none',
      }}
    >
      {(label || description) && (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {label && (
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {label}
            </span>
          )}
          {description && (
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              {description}
            </span>
          )}
        </div>
      )}

      <div
        role="switch"
        aria-checked={checked}
        tabIndex={disabled ? -1 : 0}
        onClick={() => !disabled && onChange(!checked)}
        onKeyDown={(e) => {
          if (!disabled && (e.key === ' ' || e.key === 'Enter')) {
            e.preventDefault();
            onChange(!checked);
          }
        }}
        style={{
          width: `${width}px`,
          height: `${height}px`,
          backgroundColor: checked ? 'var(--accent-cyan)' : 'var(--bg-surface-elevated)',
          border: `1px solid ${checked ? 'var(--accent-cyan)' : 'var(--border-default)'}`,
          borderRadius: 'var(--radius-full)',
          position: 'relative',
          transition: 'background-color var(--transition-fast), border-color var(--transition-fast)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: `${knobSize}px`,
            height: `${knobSize}px`,
            backgroundColor: checked ? '#030712' : 'var(--text-secondary)',
            borderRadius: '50%',
            position: 'absolute',
            top: '1px',
            left: '1px',
            transform: checked ? `translateX(${translateDist}px)` : 'translateX(0px)',
            transition: 'transform var(--transition-fast), background-color var(--transition-fast)',
            boxShadow: 'var(--shadow-sm)',
          }}
        />
      </div>
    </label>
  );
};
