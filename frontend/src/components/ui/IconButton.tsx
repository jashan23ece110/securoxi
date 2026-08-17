import React from 'react';
import { ButtonVariant, ButtonSize } from './Button';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  'aria-label': string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  tooltip?: string;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  'aria-label': ariaLabel,
  variant = 'ghost',
  size = 'md',
  tooltip,
  className = '',
  style,
  ...props
}) => {
  const sizeMap = {
    xs: { padding: '4px', fontSize: '12px' },
    sm: { padding: '6px', fontSize: '14px' },
    md: { padding: '8px', fontSize: '16px' },
    lg: { padding: '10px', fontSize: '18px' },
  };

  return (
    <button
      className={`btn btn-${variant} ${className}`}
      aria-label={ariaLabel}
      title={tooltip || ariaLabel}
      style={{
        ...sizeMap[size],
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 'var(--radius-md)',
        lineHeight: 1,
        ...style,
      }}
      {...props}
    >
      {icon}
    </button>
  );
};
