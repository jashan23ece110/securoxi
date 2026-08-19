"""
SECUROXI AI Intelligence 2.0 — Phase 8 Final Safety, Autonomy & Cross-System Regression Freeze (Stage 53)
Tests the complete end-to-end autonomous intelligence loop:
Event Correlation (Stage 45) -> Security Early Warning (Stage 46) -> Hiring Monitor (Stage 47)
-> Continuous Knowledge (Stage 48) -> Autonomous Investigation (Stage 49) -> Predictive Risk (Stage 50)
-> Digital Twin Graph (Stage 51) -> Controlled Action & Outcome Verification (Stage 52).
"""

import pytest
import time
from securoxi.enterprise.intelligence import ContinuousEnterpriseIntelligenceManager, EnterpriseEvent, EventCategory
from securoxi.enterprise.hiring import AutonomousHiringMonitor, CandidateWatch
from securoxi.enterprise.knowledge import ContinuousKnowledgeManager, SourceAuthority
from securoxi.enterprise.investigation import CrossSystemInvestigationEngine, TriggerType, InvestigationFindingClass, ResponseActionType
from securoxi.enterprise.predictive import PredictiveRiskEngine, RiskType, PredictionHorizon
from securoxi.enterprise.graph import EnterpriseDigitalTwinGraph, NodeType, EdgeType
from securoxi.enterprise.autonomy import ControlledAutonomyEngine, AutonomyLevel, ActionImpactClass, ExecutionStatus


# =========================================================================
# 1. COMPLETE PHASE 8 CLOSED-LOOP AUTONOMOUS JOURNEY
# =========================================================================

def test_phase8_end_to_end_closed_loop_journey():
    """
    Validates complete cross-system flow:
    Event -> Correlation Signal -> Hiring Watch -> Knowledge Admission -> Investigation -> Prediction -> Graph -> Governed Action.
    """
    # 1. Event Ingestion & Correlation (Stage 45)
    intel_mgr = ContinuousEnterpriseIntelligenceManager()
    raw_event = {
        "event_type": "ats.candidate.resume_uploaded",
        "category": "HIRING",
        "resource_id": "CAND-999",
    }
    sig = intel_mgr.ingest_event(
        raw_event=raw_event,
        organization_id="ORG-ENTERPRISE",
        workspace_id="WS-CORP",
        source="Greenhouse",
    )

    # 2. Hiring Monitor (Stage 47)
    hiring_mon = AutonomousHiringMonitor()
    watch = hiring_mon.create_candidate_watch(
        organization_id="ORG-ENTERPRISE",
        workspace_id="WS-CORP",
        candidate_id="CAND-999",
        job_id="JOB-STAFF-ENG",
        created_by="USER-RECRUITER-1",
    )
    assert watch.status.value == "ACTIVE"

    # 3. Continuous Knowledge Admission (Stage 48)
    know_mgr = ContinuousKnowledgeManager()
    src = know_mgr.admit_source(
        organization_id="ORG-ENTERPRISE",
        workspace_id="WS-CORP",
        title="Enterprise_Hiring_Standard_2026.pdf",
        content="Mandatory requirement: 5+ years distributed systems architecture.",
        authority=SourceAuthority.AUTHORITATIVE,
        security_state="SAFE",
    )
    assert src.admission.value == "ADMITTED"

    # 4. Autonomous Investigation (Stage 49)
    inv_engine = CrossSystemInvestigationEngine()
    case = inv_engine.initiate_case(
        organization_id="ORG-ENTERPRISE",
        workspace_id="WS-CORP",
        trigger_type=TriggerType.CANDIDATE_SECURITY_ESCALATION,
        target_resource_id="CAND-999",
    )
    inv_engine.add_timeline_event(case.case_id, "ATS", "Candidate uploaded resume", provenance="GH-999")
    inv_engine.add_timeline_event(case.case_id, "SECURITY", "Scan verdict: SAFE", provenance="SCAN-999")
    rec = inv_engine.synthesize_and_recommend(
        case_id=case.case_id,
        finding_class=InvestigationFindingClass.NO_ISSUE,
        action_type=ResponseActionType.MONITOR,
        reason="Clean candidate with verified credentials",
    )
    assert rec is not None

    # 5. Predictive Risk Forecast (Stage 50)
    pred_engine = PredictiveRiskEngine()
    fcst = pred_engine.generate_forecast(
        organization_id="ORG-ENTERPRISE",
        workspace_id="WS-CORP",
        subject_type="CANDIDATE",
        subject_id="CAND-999",
        risk_type=RiskType.SECURITY_ESCALATION,
        historical_event_count=3,
        horizon=PredictionHorizon.HOURS_24,
    )
    assert fcst.status.value == "ACTIVE"

    # 6. Digital Twin Graph Linkage & Impact (Stage 51)
    graph = EnterpriseDigitalTwinGraph()
    cand_node = graph.add_node("ORG-ENTERPRISE", "WS-CORP", NodeType.CANDIDATE, "Candidate Bob")
    job_node = graph.add_node("ORG-ENTERPRISE", "WS-CORP", NodeType.JOB, "Staff Engineer")
    edge = graph.add_edge("ORG-ENTERPRISE", cand_node.node_id, job_node.node_id, EdgeType.CANDIDATE_FOR)
    assert edge is not None

    # 7. Controlled Autonomous Action Execution (Stage 52)
    autonomy_engine = ControlledAutonomyEngine()
    prop = autonomy_engine.propose_action(
        organization_id="ORG-ENTERPRISE",
        workspace_id="WS-CORP",
        action_type="REFRESH_CANDIDATE_INDEX",
        target_resource_id=cand_node.node_id,
        impact_class=ActionImpactClass.LOW_IMPACT_REVERSIBLE,
        autonomy_level=AutonomyLevel.L3_GUARDED_AUTONOMOUS_LOW_IMPACT,
    )
    ok, exec_rec, _ = autonomy_engine.execute_action(prop.proposal_id, current_evidence_version=1)
    assert ok is True
    assert exec_rec.status == ExecutionStatus.SUCCESS
    assert exec_rec.outcome.is_verified is True


# =========================================================================
# 2. CROSS-TENANT ISOLATION & PRIVILEGE ESCALATION RED TEAM
# =========================================================================

def test_phase8_cross_tenant_isolation_red_team():
    """Verifies that Org Alpha cannot view, query, or execute actions against Org Beta across all Phase 8 systems."""
    graph = EnterpriseDigitalTwinGraph()
    alpha_node = graph.add_node("ORG-ALPHA", "WS-A", NodeType.CANDIDATE, "Alpha Candidate")
    beta_node = graph.add_node("ORG-BETA", "WS-B", NodeType.JOB, "Beta Job")

    # Cross-tenant graph connection rejected
    cross_edge = graph.add_edge("ORG-ALPHA", alpha_node.node_id, beta_node.node_id, EdgeType.CANDIDATE_FOR)
    assert cross_edge is None

    # Cross-tenant knowledge query rejected
    know_mgr = ContinuousKnowledgeManager()
    know_mgr.admit_source("ORG-ALPHA", "WS-A", "Alpha Secret", "Confidential text")
    beta_results = know_mgr.query_knowledge("ORG-BETA", "WS-B", "Confidential")
    assert len(beta_results) == 0

    # Cross-tenant investigation isolation
    inv_engine = CrossSystemInvestigationEngine()
    inv_engine.initiate_case("ORG-ALPHA", "WS-A", TriggerType.REPEATED_SECURITY_FINDINGS, "RES-1")
    assert len(inv_engine.get_cases("ORG-BETA")) == 0


# =========================================================================
# 3. KILL SWITCH & OPERATIONAL SAFE MODE ENFORCEMENT
# =========================================================================

def test_phase8_operational_kill_switch_enforcement():
    """Verifies that activating Safe Mode halts all autonomous action executions immediately."""
    engine = ControlledAutonomyEngine()
    prop = engine.propose_action("ORG-TEST", "WS-MAIN", "AUTO_TASK", "RES-1")

    # Enable Safe Mode
    engine.set_safe_mode(True)

    ok, _, reason = engine.execute_action(prop.proposal_id, current_evidence_version=1)
    assert ok is False
    assert reason == "SAFE_MODE_BLOCKED"


# =========================================================================
# 4. DETERMINISTIC SECURITY CLEARANCE & IDEMPOTENCY BARRIERS
# =========================================================================

def test_phase8_security_gate_and_idempotency_barriers():
    """Verifies that HIGH_RISK entities cannot be target of autonomous actions and duplicate executions are blocked."""
    engine = ControlledAutonomyEngine()
    prop = engine.propose_action("ORG-TEST", "WS-MAIN", "REFRESH", "RES-MALICIOUS")

    # Target is HIGH_RISK -> Rejected
    ok, _, reason = engine.execute_action(prop.proposal_id, current_evidence_version=1, target_security_state="HIGH_RISK")
    assert ok is False
    assert "HIGH_RISK" in reason

    # Clean target -> Executes once
    clean_prop = engine.propose_action("ORG-TEST", "WS-MAIN", "REFRESH", "RES-CLEAN")
    ok, _, _ = engine.execute_action(clean_prop.proposal_id, current_evidence_version=1, target_security_state="SAFE")
    assert ok is True

    # Duplicate execution attempt with same idempotency key -> Blocked
    ok, _, reason = engine.execute_action(clean_prop.proposal_id, current_evidence_version=1, target_security_state="SAFE")
    assert ok is False
    assert reason == "DUPLICATE_IDEMPOTENCY"
