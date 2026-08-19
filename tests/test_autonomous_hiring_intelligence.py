"""
SECUROXI AI Intelligence 2.0 — Autonomous Hiring Intelligence Test Suite (Phase 8 Stage 47)
Validates candidate/job watches, security-first evaluation, change significance filtering,
ranking impact analysis, recommendation generation, stale state detection, and tenant isolation.
"""

import pytest
from securoxi.enterprise.hiring import (
    AutonomousHiringMonitor,
    CandidateChange,
    ChangeSignificance,
    CandidateChangeType,
    WatchStatus,
    RecommendationStatus,
)


# =========================================================================
# 1. CANDIDATE & JOB WATCH REGISTRATION
# =========================================================================

def test_candidate_and_job_watch_registration():
    """Verifies creation and scoping of Candidate and Job watches."""
    monitor = AutonomousHiringMonitor()

    cand_watch = monitor.create_candidate_watch(
        organization_id="ORG-ALPHA",
        workspace_id="WS-HIRING",
        candidate_id="CAND-101",
        job_id="JOB-SEC-ENG",
        created_by="recruiter-bob",
    )
    assert cand_watch.status == WatchStatus.ACTIVE
    assert cand_watch.candidate_id == "CAND-101"

    job_watch = monitor.create_job_watch(
        organization_id="ORG-ALPHA",
        workspace_id="WS-HIRING",
        job_id="JOB-SEC-ENG",
        created_by="recruiter-bob",
        target_top_k=25,
    )
    assert job_watch.status == WatchStatus.ACTIVE
    assert job_watch.target_top_k == 25


# =========================================================================
# 2. SECURITY-FIRST INVARIANT (HIGH_RISK / UNINSPECTABLE BLOCKED)
# =========================================================================

def test_security_first_invariant_blocks_malicious_candidate():
    """Verifies that a HIGH_RISK candidate change is strictly blocked from generating recommendations."""
    monitor = AutonomousHiringMonitor()

    change = CandidateChange(
        organization_id="ORG-ALPHA",
        workspace_id="WS-HIRING",
        candidate_id="CAND-MALICIOUS",
        change_type=CandidateChangeType.RESUME_UPDATED,
        significance=ChangeSignificance.SECURITY_CRITICAL,
        security_state="HIGH_RISK",
        changed_fields=["resume_pdf"],
        new_state={"fit_score": 98.0, "new_rank": 1},
    )

    rec = monitor.process_candidate_change(change)
    assert rec is None  # Blocked from trusted ranking / recommendations!


# =========================================================================
# 3. SIGNIFICANCE FILTERING & TOP-K RANKING IMPACT
# =========================================================================

def test_change_significance_and_ranking_impact_recommendation():
    """Verifies that non-material changes are ignored, while material evidence produces a recommendation."""
    monitor = AutonomousHiringMonitor()

    # 1. Non-material change (Phone update) -> Ignored
    phone_change = CandidateChange(
        organization_id="ORG-ALPHA",
        workspace_id="WS-HIRING",
        candidate_id="CAND-BOB",
        change_type=CandidateChangeType.RESUME_UPDATED,
        significance=ChangeSignificance.NO_IMPACT,
        security_state="SAFE",
        changed_fields=["phone_number"],
    )
    assert monitor.process_candidate_change(phone_change) is None

    # 2. Material change (New Kubernetes certification added -> Rank improves from #24 to #5)
    material_change = CandidateChange(
        organization_id="ORG-ALPHA",
        workspace_id="WS-HIRING",
        candidate_id="CAND-BOB",
        change_type=CandidateChangeType.EVIDENCE_ADDED,
        significance=ChangeSignificance.MATERIAL,
        security_state="SAFE",
        changed_fields=["certifications:CKA", "experience:kubernetes"],
        new_state={"job_id": "JOB-SEC-ENG", "new_rank": 5, "fit_score": 94.0},
    )
    rec = monitor.process_candidate_change(material_change)
    assert rec is not None
    assert rec.suggested_action == "ADVANCE_TO_INTERVIEW"
    assert rec.new_rank == 5
    assert rec.rank_delta == 19
    assert rec.status == RecommendationStatus.PROPOSED


# =========================================================================
# 4. JD CHANGE STALE EVALUATION & TENANT ISOLATION
# =========================================================================

def test_jd_change_stale_detection_and_tenant_isolation():
    """Verifies that JD modifications mark evaluations as stale and recommendations remain tenant-isolated."""
    monitor = AutonomousHiringMonitor()

    # Trigger candidate evaluation
    change = CandidateChange(
        organization_id="ORG-BETA",
        workspace_id="WS-HIRING",
        candidate_id="CAND-ALICE",
        significance=ChangeSignificance.MATERIAL,
        security_state="SAFE",
        new_state={"job_id": "JOB-DEV-01", "new_rank": 3, "fit_score": 91.0},
    )
    rec = monitor.process_candidate_change(change)
    assert rec is not None

    # Check Tenant Scoping: Org Alpha cannot see Org Beta recommendations
    assert len(monitor.get_recommendations("ORG-ALPHA")) == 0
    assert len(monitor.get_recommendations("ORG-BETA")) == 1

    # JD requirement changes -> Mark evaluations stale
    monitor.mark_job_evaluations_stale("JOB-DEV-01", reason="Mandatory Python requirement upgraded to Senior level")
    eval_state = monitor._evaluations["CAND-ALICE:JOB-DEV-01"]
    assert eval_state.is_stale is True
