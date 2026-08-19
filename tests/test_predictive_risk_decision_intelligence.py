"""
SECUROXI AI Intelligence 2.0 — Predictive Risk & Decision Intelligence Test Suite (Phase 8 Stage 50)
Validates risk forecast generation, insufficient data gap handling, prediction vs authority separation,
governed predictive recommendations, what-if capacity simulations, and tenant isolation.
"""

import pytest
from securoxi.enterprise.predictive import (
    PredictiveRiskEngine,
    RiskType,
    PredictionHorizon,
    PredictionUncertainty,
    ForecastStatus,
    PredictiveRecommendationStatus,
)


# =========================================================================
# 1. RISK FORECAST GENERATION & INSUFFICIENT DATA HANDLING
# =========================================================================

def test_risk_forecast_generation_and_data_gap():
    """Verifies calibrated forecast generation and explicit reporting of INSUFFICIENT_DATA."""
    engine = PredictiveRiskEngine()

    # 1. Sufficient historical data (count >= 2) -> ACTIVE forecast
    fcst_active = engine.generate_forecast(
        organization_id="ORG-TEST",
        workspace_id="WS-SEC",
        subject_type="ENDPOINT",
        subject_id="API-GATEWAY",
        risk_type=RiskType.SECURITY_ESCALATION,
        historical_event_count=4,
        horizon=PredictionHorizon.HOURS_24,
    )
    assert fcst_active.status == ForecastStatus.ACTIVE
    assert fcst_active.probability >= 0.70
    assert fcst_active.uncertainty == PredictionUncertainty.MEDIUM_CONFIDENCE

    # 2. Sparse data (count < 2) -> INSUFFICIENT_DATA
    fcst_sparse = engine.generate_forecast(
        organization_id="ORG-TEST",
        workspace_id="WS-SEC",
        subject_type="SERVICE",
        subject_id="SVC-NEW",
        risk_type=RiskType.INTEGRATION_FAILURE,
        historical_event_count=1,
    )
    assert fcst_sparse.status == ForecastStatus.INSUFFICIENT_DATA
    assert fcst_sparse.uncertainty == PredictionUncertainty.INSUFFICIENT_DATA


# =========================================================================
# 2. PREDICTION VS AUTHORITY INVARIANT & GOVERNED RECOMMENDATIONS
# =========================================================================

def test_prediction_vs_authority_and_governed_recommendations():
    """Verifies that forecasts generate governed recommendations requiring approval, without overriding security state."""
    engine = PredictiveRiskEngine()

    fcst = engine.generate_forecast(
        organization_id="ORG-TEST",
        workspace_id="WS-SEC",
        subject_type="ATS",
        subject_id="GH-INTEGRATION",
        risk_type=RiskType.INTEGRATION_FAILURE,
        historical_event_count=5,
    )

    # Propose Predictive Recommendation
    rec = engine.propose_recommendation(
        forecast=fcst,
        recommendation_type="PROACTIVE_ATS_HEALTH_CHECK",
        reason="Elevated probability of ATS provider synchronization outage within 24h",
        impact="HIGH",
    )
    assert rec is not None
    assert rec.requires_approval is True  # Invariant: Consequential action requires human sign-off
    assert rec.status == PredictiveRecommendationStatus.PROPOSED


# =========================================================================
# 3. WHAT-IF CAPACITY SIMULATION & TENANT ISOLATION
# =========================================================================

def test_whatif_simulation_and_tenant_isolation():
    """Verifies safe what-if simulations and tenant-isolated forecast queries."""
    engine = PredictiveRiskEngine()

    # What-if Simulation
    sim = engine.run_whatif_simulation(
        organization_id="ORG-ALPHA",
        scenario_name="Candidate Volume 3x Spike",
        volume_multiplier=3.0,
    )
    assert sim.is_simulation is True
    assert sim.predicted_queue_saturation_pct == 60.0
    assert sim.worker_scale_recommendation == 6

    # Tenant Isolation: Org Beta cannot see Org Alpha forecasts
    fcst = engine.generate_forecast(
        organization_id="ORG-ALPHA",
        workspace_id="WS-SEC",
        subject_type="RESOURCE",
        subject_id="DOC-ALPHA",
        risk_type=RiskType.SECURITY_ESCALATION,
        historical_event_count=3,
    )
    assert len(engine.get_forecasts("ORG-BETA")) == 0
    assert len(engine.get_forecasts("ORG-ALPHA")) == 1
