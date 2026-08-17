import React from 'react';
import { X } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  onClear?: () => void;
  fullWidth?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  helperText,
  error,
  icon,
  iconRight,
  onClear,
  fullWidth = true,
  className = '',
  style,
  disabled,
  value,
  ...props
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        width: fullWidth ? '100%' : 'auto',
      }}
    >
      {label && (
        <label
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            color: 'var(--text-secondary)',
            letterSpacing: '0.02em',
          }}
        >
          {label}
        </label>
      )}

      <div
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          width: '100%',
        }}
      >
        {icon && (
          <span
            style={{
              position: 'absolute',
              left: '10px',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              pointerEvents: 'none',
            }}
          >
            {icon}
          </span>
        )}

        <input
          className={`input-field ${error ? 'input-error' : ''} ${className}`.trim()}
          disabled={disabled}
          value={value}
          style={{
            width: '100%',
            backgroundColor: 'var(--bg-input)',
            border: `1px solid ${error ? 'var(--status-highrisk)' : 'var(--border-default)'}`,
            borderRadius: 'var(--radius-md)',
            padding: icon && (iconRight || onClear)
              ? '8px 34px 8px 34px'
              : icon
              ? '8px 12px 8px 34px'
              : (iconRight || onClear)
              ? '8px 34px 8px 12px'
              : '8px 12px',
            fontSize: '0.8125rem',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-sans)',
            outline: 'none',
            transition: 'border-color var(--transition-fast), box-shadow var(--transition-fast)',
            opacity: disabled ? 0.5 : 1,
            cursor: disabled ? 'not-allowed' : 'text',
            ...style,
          }}
          {...props}
        />

        {onClear && value && !disabled && (
          <button
            type="button"
            onClick={onClear}
            aria-label="Clear input"
            style={{
              position: 'absolute',
              right: '10px',
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              padding: '2px',
            }}
          >
            <X size={14} />
          </button>
        )}

        {!onClear && iconRight && (
          <span
            style={{
              position: 'absolute',
              right: '10px',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              pointerEvents: 'none',
            }}
          >
            {iconRight}
          </span>
        )}
      </div>

      {(error || helperText) && (
        <span
          style={{
            fontSize: '0.6875rem',
            color: error ? 'var(--status-highrisk)' : 'var(--text-muted)',
          }}
        >
          {error || helperText}
        </span>
      )}
    </div>
  );
};
