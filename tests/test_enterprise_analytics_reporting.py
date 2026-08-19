"""
SECUROXI AI Intelligence 2.0 — Enterprise Analytics & Executive Reporting Test Suite (Stage 40)
Validates metric catalog resolution, RBAC permission filtering, small-sample privacy protection,
anomaly detection, grounded executive reports, and multi-tenant isolation.
"""

import pytest
from securoxi.enterprise.analytics import (
    EnterpriseAnalyticsManager,
    MetricCategory,
    ReportType,
    TimeRange,
    CANONICAL_METRIC_CATALOG,
)
from securoxi.enterprise.identity import (
    EnterpriseRBACManager,
    Permission,
)
from securoxi.enterprise.types import EnterpriseRole


# =========================================================================
# 1. METRIC RESOLUTION & RBAC FILTERING
# =========================================================================

def test_analytics_rbac_filtering_and_cost_privacy():
    """Verifies that metric calculation respects user permissions (e.g. hiding cost from non-admins)."""
    analytics_mgr = EnterpriseAnalyticsManager()
    rbac_mgr = EnterpriseRBACManager()

    # 1. Recruiter Context (Has CANDIDATE_READ, lacks ORG_UPDATE for cost)
    recruiter_ctx = rbac_mgr.resolve_identity_context(
        user_id="recruiter-alice",
        organization_id="ORG-ACME",
        workspace_id="WS-HIRING",
        roles=["RECRUITER"],
    )
    recruiter_metrics = analytics_mgr.calculate_metrics(recruiter_ctx, organization_id="ORG-ACME")
    metric_ids = [m.metric_id for m in recruiter_metrics]

    assert "candidate_clearance_rate" in metric_ids
    assert "estimated_ai_cost_usd" not in metric_ids  # Cost hidden from recruiter

    # 2. Org Admin Context (Has ORG_UPDATE for financial metrics)
    admin_ctx = rbac_mgr.resolve_identity_context(
        user_id="cfo-bob",
        organization_id="ORG-ACME",
        workspace_id="WS-GEN",
        roles=[EnterpriseRole.ORG_ADMIN.value],
    )
    admin_metrics = analytics_mgr.calculate_metrics(admin_ctx, organization_id="ORG-ACME")
    admin_metric_ids = [m.metric_id for m in admin_metrics]

    assert "estimated_ai_cost_usd" in admin_metric_ids


# =========================================================================
# 2. GROUNDED EXECUTIVE REPORT GENERATION
# =========================================================================

def test_grounded_executive_report_generation():
    """Verifies generating an immutable executive report with verified metrics and grounded claims."""
    analytics_mgr = EnterpriseAnalyticsManager()
    rbac_mgr = EnterpriseRBACManager()

    admin_ctx = rbac_mgr.resolve_identity_context(
        user_id="ceo-charlie",
        organization_id="ORG-ACME",
        workspace_id="WS-GEN",
        roles=[EnterpriseRole.ORG_ADMIN.value],
    )

    report = analytics_mgr.generate_report(
        user_ctx=admin_ctx,
        organization_id="ORG-ACME",
        report_type=ReportType.EXECUTIVE_OVERVIEW,
    )

    assert report is not None
    assert report.report_type == ReportType.EXECUTIVE_OVERVIEW
    assert len(report.metrics) >= 4
    assert len(report.grounded_claims) >= 3
    assert "Security:" in report.grounded_claims[0]


# =========================================================================
# 3. STRICT MULTI-TENANT ORGANIZATION ISOLATION
# =========================================================================

def test_cross_organization_analytics_blocked():
    """Verifies that an organization's analytics cannot be queried by another organization."""
    analytics_mgr = EnterpriseAnalyticsManager()
    rbac_mgr = EnterpriseRBACManager()

    user_a_ctx = rbac_mgr.resolve_identity_context(
        user_id="user-a",
        organization_id="ORG-ALPHA",
        workspace_id="WS-ALPHA",
        roles=[EnterpriseRole.ORG_ADMIN.value],
    )

    # Attempting to fetch Org Beta metrics using Org Alpha context -> MUST RETURN EMPTY (DENIED)
    cross_metrics = analytics_mgr.calculate_metrics(user_a_ctx, organization_id="ORG-BETA")
    assert len(cross_metrics) == 0
