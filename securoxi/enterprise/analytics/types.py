"""
SECUROXI AI Intelligence 2.0 — Enterprise Analytics & Reporting Types
"""

from enum import Enum


class MetricCategory(str, Enum):
    SECURITY = "SECURITY"
    HIRING = "HIRING"
    OPERATIONS = "OPERATIONS"
    COST = "COST"
    AI_EFFICIENCY = "AI_EFFICIENCY"


class ReportType(str, Enum):
    EXECUTIVE_OVERVIEW = "EXECUTIVE_OVERVIEW"
    SECURITY_THREAT_REPORT = "SECURITY_THREAT_REPORT"
    HIRING_FUNNEL_REPORT = "HIRING_FUNNEL_REPORT"
    OPERATIONS_HEALTH_REPORT = "OPERATIONS_HEALTH_REPORT"


class TimeRange(str, Enum):
    LAST_24_HOURS = "LAST_24_HOURS"
    LAST_7_DAYS = "LAST_7_DAYS"
    LAST_30_DAYS = "LAST_30_DAYS"
    CUSTOM = "CUSTOM"


class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
