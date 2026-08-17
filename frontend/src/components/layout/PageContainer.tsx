import React from 'react';
import { BackgroundPattern } from '../ui/BackgroundPattern';

export interface PageContainerProps {
  children: React.ReactNode;
  showPattern?: boolean;
  maxWidth?: string;
  className?: string;
}

export const PageContainer: React.FC<PageContainerProps> = ({
  children,
  showPattern = true,
  maxWidth = '1600px',
  className = '',
}) => {
  return (
    <div
      className={`page-container ${className}`.trim()}
      style={{
        position: 'relative',
        width: '100%',
        maxWidth,
        margin: '0 auto',
        minHeight: '100%',
      }}
    >
      {showPattern && <BackgroundPattern variant="grid" opacity={0.025} />}
      <div style={{ position: 'relative', zIndex: 1 }}>
        {children}
      </div>
    </div>
  );
};
