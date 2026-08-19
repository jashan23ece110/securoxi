"""
SECUROXI AI Intelligence 2.0 — Predictive Risk & Decision Intelligence Models (Phase 8 Stage 50)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import time
import uuid
from securoxi.enterprise.predictive.types import (
    RiskType,
    PredictionHorizon,
    PredictionUncertainty,
    ForecastStatus,
    PredictiveRecommendationStatus,
)


@dataclass
class RiskForecast:
    """Statistical/probabilistic risk forecast strictly separated from authoritative state."""
    forecast_id: str = field(default_factory=lambda: f"FCST-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-SECURITY"
    subject_type: str = "RESOURCE"
    subject_id: str = "RES-001"
    risk_type: RiskType = RiskType.SECURITY_ESCALATION
    probability: float = 0.85
    uncertainty: PredictionUncertainty = PredictionUncertainty.MEDIUM_CONFIDENCE
    horizon: PredictionHorizon = PredictionHorizon.HOURS_24
    evidence: List[str] = field(default_factory=list)
    model_version: str = "v1.0-calibrated"
    status: ForecastStatus = ForecastStatus.ACTIVE
    generated_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 86400)


@dataclass
class PredictiveRecommendation:
    """Actionable attention prioritization recommendation derived from a forecast."""
    recommendation_id: str = field(default_factory=lambda: f"PRED-REC-{uuid.uuid4().hex[:8].upper()}")
    forecast_id: str = "FCST-DEFAULT"
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-SECURITY"
    recommendation_type: str = "PROACTIVE_INVESTIGATION"
    reason: str = "High forecast of recurring prompt injection attacks"
    confidence: float = 0.88
    impact: str = "HIGH"
    requires_approval: bool = True
    status: PredictiveRecommendationStatus = PredictiveRecommendationStatus.PROPOSED
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 86400 * 3)


@dataclass
class ScenarioSimulationResult:
    """What-if simulation result predicting resource load under hypothetical workload spikes."""
    simulation_id: str = field(default_factory=lambda: f"SIM-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    scenario_name: str = "Candidate Volume 2x Spike"
    predicted_queue_saturation_pct: float = 45.0
    predicted_p95_latency_ms: float = 380.0
    worker_scale_recommendation: int = 4
    is_simulation: bool = True
    simulated_at: float = field(default_factory=time.time)
