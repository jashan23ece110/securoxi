import React from 'react';
import { Verdict } from '../../api/types';

export type BadgeVariant =
  | 'safe'
  | 'suspicious'
  | 'highrisk'
  | 'critical'
  | 'blocked'
  | 'review'
  | 'allowed'
  | 'processing'
  | 'failed'
  | 'uninspectable'
  | 'info'
  | 'neutral';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  showDot?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  showDot = false,
  className = '',
  style,
}) => {
  return (
    <span className={`badge badge-${variant} ${className}`.trim()} style={style}>
      {showDot && <span className="badge-dot" />}
      <span>{children}</span>
    </span>
  );
};

export type SecurityStatusType =
  | 'SAFE'
  | 'SUSPICIOUS'
  | 'HIGH_RISK'
  | 'CRITICAL'
  | 'BLOCKED'
  | 'REVIEW'
  | 'REVIEW_REQUIRED'
  | 'ALLOWED'
  | 'PROCESSING'
  | 'FAILED'
  | 'UNINSPECTABLE';

export interface StatusBadgeProps {
  status: SecurityStatusType | string;
  label?: string;
  showDot?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  showDot = true,
  className = '',
  style,
}) => {
  const normalized = (status || '').toUpperCase().trim();

  const variantMap: Record<string, BadgeVariant> = {
    SAFE: 'safe',
    ALLOWED: 'allowed',
    SUSPICIOUS: 'suspicious',
    HIGH_RISK: 'highrisk',
    HIGHRISK: 'highrisk',
    CRITICAL: 'critical',
    BLOCKED: 'blocked',
    REVIEW: 'review',
    REVIEW_REQUIRED: 'review',
    PROCESSING: 'processing',
    PENDING: 'processing',
    FAILED: 'failed',
    POISON: 'critical',
    UNINSPECTABLE: 'uninspectable',
    INFO: 'info',
  };

  const variant = variantMap[normalized] || 'neutral';
  const displayLabel = label || normalized.replace(/_/g, ' ');

  return (
    <Badge variant={variant} showDot={showDot} className={className} style={style}>
      {displayLabel}
    </Badge>
  );
};

export interface VerdictBadgeProps {
  verdict: Verdict | string;
  label?: string;
  showDot?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const VerdictBadge: React.FC<VerdictBadgeProps> = ({ verdict, label, showDot = true, className = '', style }) => {
  return <StatusBadge status={verdict} label={label} showDot={showDot} className={className} style={style} />;
};

export interface SeverityBadgeProps {
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  showDot?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  showDot = true,
  className = '',
  style,
}) => {
  const norm = (severity || '').toUpperCase().trim();
  const map: Record<string, BadgeVariant> = {
    LOW: 'info',
    MEDIUM: 'suspicious',
    HIGH: 'highrisk',
    CRITICAL: 'critical',
  };

  return (
    <Badge variant={map[norm] || 'neutral'} showDot={showDot} className={className} style={style}>
      {norm}
    </Badge>
  );
};
