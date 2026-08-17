import React from 'react';
import { Verdict } from '../../api/types';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'safe' | 'suspicious' | 'highrisk' | 'critical' | 'blocked' | 'info';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'info', className = '' }) => {
  return <span className={`badge badge-${variant} ${className}`}>{children}</span>;
};

interface VerdictBadgeProps {
  verdict: Verdict;
}

export const VerdictBadge: React.FC<VerdictBadgeProps> = ({ verdict }) => {
  const map: Record<Verdict, 'safe' | 'suspicious' | 'highrisk' | 'critical' | 'blocked'> = {
    SAFE: 'safe',
    SUSPICIOUS: 'suspicious',
    HIGH_RISK: 'highrisk',
    CRITICAL: 'critical',
    BLOCKED: 'blocked',
  };

  return <Badge variant={map[verdict] || 'info'}>{verdict}</Badge>;
};
