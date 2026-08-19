"""
SECUROXI AI Intelligence 2.0 — Enterprise Developer Platform & Webhook Types
"""

from enum import Enum


class APIScope(str, Enum):
    TASK_READ = "task:read"
    TASK_CREATE = "task:create"
    CANDIDATE_READ = "candidate:read"
    CANDIDATE_SCREEN = "candidate:screen"
    INVESTIGATION_READ = "investigation:read"
    ANALYTICS_READ = "analytics:read"
    ATS_WRITE = "ats:write"
    APPROVAL_WRITE = "approval:write"


class WebhookEventType(str, Enum):
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    SECURITY_HIGH_RISK_DETECTED = "security.high_risk_detected"
    INVESTIGATION_CREATED = "investigation.created"
    APPROVAL_REQUIRED = "approval.required"
    ATS_SYNC_COMPLETED = "ats.sync_completed"


class WebhookDeliveryStatus(str, Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    DISABLED = "DISABLED"
