"""
SECUROXI AI Intelligence 2.0 — Enterprise Analytics & Reporting Models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
from securoxi.enterprise.analytics.types import (
    MetricCategory,
    ReportType,
    TimeRange,
    AnomalySeverity,
)
from securoxi.enterprise.identity.types import Permission


@dataclass
class MetricDefinition:
    """Canonical versioned definition of a system metric."""
    metric_id: str
    name: str
    description: str
    category: MetricCategory
    formula_summary: str
    version: str = "v1.0"
    required_permission: Permission = Permission.ORG_READ


@dataclass
class MetricValue:
    """Computed metric value for an organization/workspace scope."""
    metric_id: str
    organization_id: str
    workspace_id: Optional[str]
    value: float
    unit: str
    sample_count: int
    time_range: TimeRange = TimeRange.LAST_7_DAYS
    calculated_at: float = field(default_factory=time.time)
    is_suppressed: bool = False  # True if sample_count < minimum threshold (small-sample protection)


@dataclass
class AnomalyAlert:
    """Statistical anomaly notification derived from metrics."""
    alert_id: str = field(default_factory=lambda: f"ANOM-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    metric_id: str = "security_high_risk_rate"
    severity: AnomalySeverity = AnomalySeverity.MEDIUM
    observed_deviation: str = "High-risk detections increased 35% vs 7-day baseline"
    contributing_factors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ReportSnapshot:
    """Immutable, versioned report snapshot containing verified metrics and grounded insights."""
    report_id: str = field(default_factory=lambda: f"REP-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: Optional[str] = None
    report_type: ReportType = ReportType.EXECUTIVE_OVERVIEW
    generated_by: str = "executive@enterprise.com"
    metrics: List[MetricValue] = field(default_factory=list)
    executive_narrative: str = ""
    grounded_claims: List[str] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "report_type": self.report_type.value,
            "generated_by": self.generated_by,
            "metrics_count": len(self.metrics),
            "executive_narrative": self.executive_narrative,
            "grounded_claims": self.grounded_claims,
            "generated_at": self.generated_at,
        }
