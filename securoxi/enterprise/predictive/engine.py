"""
SECUROXI AI Intelligence 2.0 — Predictive Risk & Decision Intelligence Engine (Phase 8 Stage 50)
Coordinates risk forecasts, what-if simulations, and governed predictive recommendations.
Strictly maintains the invariant that Prediction != Authority.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.enterprise.predictive.types import (
    RiskType,
    PredictionHorizon,
    PredictionUncertainty,
    ForecastStatus,
    PredictiveRecommendationStatus,
)
from securoxi.enterprise.predictive.models import (
    RiskForecast,
    PredictiveRecommendation,
    ScenarioSimulationResult,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.predictive.engine")


class PredictiveRiskEngine:
    """
    Predictive Risk & Decision Intelligence Engine.
    Generates multi-horizon forecasts, what-if capacity simulations, and governed recommendations.
    """

    def __init__(self):
        self._forecasts: Dict[str, RiskForecast] = {}  # forecast_id -> RiskForecast
        self._recommendations: List[PredictiveRecommendation] = []

    def generate_forecast(
        self,
        organization_id: str,
        workspace_id: str,
        subject_type: str,
        subject_id: str,
        risk_type: RiskType,
        historical_event_count: int,
        horizon: PredictionHorizon = PredictionHorizon.HOURS_24,
    ) -> RiskForecast:
        """
        Generates calibrated forecast based on historical signals.
        If data is sparse (count < 2), explicitly reports INSUFFICIENT_DATA rather than guessing.
        """
        if historical_event_count < 2:
            forecast = RiskForecast(
                organization_id=organization_id,
                workspace_id=workspace_id,
                subject_type=subject_type,
                subject_id=subject_id,
                risk_type=risk_type,
                probability=0.0,
                uncertainty=PredictionUncertainty.INSUFFICIENT_DATA,
                horizon=horizon,
                evidence=["Sparse historical data - below minimum threshold (N >= 2)"],
                status=ForecastStatus.INSUFFICIENT_DATA,
            )
            self._forecasts[forecast.forecast_id] = forecast
            logger.info(f"Generated Forecast '{forecast.forecast_id}': Status=INSUFFICIENT_DATA for Org '{organization_id}'")
            return forecast

        # Calculate calibrated probability based on historical signal intensity
        raw_prob = min(0.95, 0.40 + (historical_event_count * 0.10))
        uncertainty = PredictionUncertainty.HIGH_CONFIDENCE if historical_event_count >= 5 else PredictionUncertainty.MEDIUM_CONFIDENCE

        forecast = RiskForecast(
            organization_id=organization_id,
            workspace_id=workspace_id,
            subject_type=subject_type,
            subject_id=subject_id,
            risk_type=risk_type,
            probability=round(raw_prob, 2),
            uncertainty=uncertainty,
            horizon=horizon,
            evidence=[f"Observed {historical_event_count} related signals within recent observation window"],
            status=ForecastStatus.ACTIVE,
        )
        self._forecasts[forecast.forecast_id] = forecast
        logger.info(f"Generated Calibrated Forecast '{forecast.forecast_id}' ({risk_type.value}, P={forecast.probability}) for Org '{organization_id}'")
        return forecast

    def propose_recommendation(
        self,
        forecast: RiskForecast,
        recommendation_type: str = "PROACTIVE_INVESTIGATION",
        reason: str = "Elevated risk forecast indicates potential escalation",
        impact: str = "HIGH",
    ) -> Optional[PredictiveRecommendation]:
        """Proposes a governed recommendation based on an active forecast."""
        if forecast.status != ForecastStatus.ACTIVE:
            logger.warning(f"Cannot generate recommendation from non-active forecast '{forecast.forecast_id}'")
            return None

        rec = PredictiveRecommendation(
            forecast_id=forecast.forecast_id,
            organization_id=forecast.organization_id,
            workspace_id=forecast.workspace_id,
            recommendation_type=recommendation_type,
            reason=reason,
            confidence=0.90,
            impact=impact,
            requires_approval=True,  # Invariant: Consequential actions require Stage 23 approval
        )
        self._recommendations.append(rec)
        logger.info(f"Created Predictive Recommendation '{rec.recommendation_id}' for Forecast '{forecast.forecast_id}'")
        return rec

    def run_whatif_simulation(
        self,
        organization_id: str,
        scenario_name: str,
        volume_multiplier: float = 2.0,
    ) -> ScenarioSimulationResult:
        """Runs a safe what-if capacity and latency simulation (zero external mutations)."""
        base_saturation = 20.0
        base_latency = 240.0

        predicted_saturation = min(100.0, base_saturation * volume_multiplier)
        predicted_latency = base_latency * (1.0 + (volume_multiplier - 1.0) * 0.4)
        worker_scale = max(2, int(2 * volume_multiplier))

        result = ScenarioSimulationResult(
            organization_id=organization_id,
            scenario_name=scenario_name,
            predicted_queue_saturation_pct=round(predicted_saturation, 1),
            predicted_p95_latency_ms=round(predicted_latency, 1),
            worker_scale_recommendation=worker_scale,
            is_simulation=True,
        )
        logger.info(f"Ran What-If Simulation '{scenario_name}' for Org '{organization_id}': Saturation={result.predicted_queue_saturation_pct}%")
        return result

    def get_forecasts(self, organization_id: str, workspace_id: Optional[str] = None) -> List[RiskForecast]:
        """Returns forecasts strictly scoped by tenant."""
        results = [f for f in self._forecasts.values() if f.organization_id == organization_id]
        if workspace_id:
            results = [f for f in results if f.workspace_id == workspace_id]
        return results
