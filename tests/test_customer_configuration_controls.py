"""
SECUROXI AI Intelligence 2.0 — Customer Configuration & Policy Controls Test Suite (Stage 42)
Validates bounded customer settings, hierarchical inheritance, rejection of forbidden invariants,
dry-run simulations, and multi-tenant isolation.
"""

import pytest
from securoxi.enterprise.config import (
    EnterpriseConfigurationManager,
    FORBIDDEN_SETTINGS,
    PLATFORM_SETTING_REGISTRY,
)
from securoxi.enterprise.identity import (
    EnterpriseRBACManager,
    Permission,
)
from securoxi.enterprise.types import EnterpriseRole


# =========================================================================
# 1. BOUNDED CONFIGURATION & HIERARCHICAL INHERITANCE
# =========================================================================

def test_bounded_configuration_and_workspace_inheritance():
    """Verifies setting values within bounds and workspace override resolution."""
    cfg_mgr = EnterpriseConfigurationManager()
    rbac_mgr = EnterpriseRBACManager()

    admin_ctx = rbac_mgr.resolve_identity_context(
        user_id="admin-alice",
        organization_id="ORG-ACME",
        workspace_id="WS-HIRING",
        roles=[EnterpriseRole.ORG_ADMIN.value],
    )

    # 1. Update Organization setting (max_retrieval_hops = 5)
    res_org = cfg_mgr.set_configuration(
        user_ctx=admin_ctx,
        organization_id="ORG-ACME",
        key="max_retrieval_hops",
        value=5,
    )
    assert res_org["success"] is True

    # Check effective value at org level
    assert cfg_mgr.get_effective_value("ORG-ACME", "max_retrieval_hops") == 5

    # 2. Update Workspace override (max_retrieval_hops = 8 for WS-RESEARCH)
    res_ws = cfg_mgr.set_configuration(
        user_ctx=admin_ctx,
        organization_id="ORG-ACME",
        key="max_retrieval_hops",
        value=8,
        workspace_id="WS-RESEARCH",
    )
    assert res_ws["success"] is True

    # Check effective values
    assert cfg_mgr.get_effective_value("ORG-ACME", "max_retrieval_hops", workspace_id="WS-RESEARCH") == 8
    assert cfg_mgr.get_effective_value("ORG-ACME", "max_retrieval_hops", workspace_id="WS-HIRING") == 5


# =========================================================================
# 2. IMMUTABLE SECURITY INVARIANTS PROTECTION
# =========================================================================

def test_immutable_security_invariants_rejected():
    """Verifies that attempts to modify foundational security invariants are strictly blocked."""
    cfg_mgr = EnterpriseConfigurationManager()
    rbac_mgr = EnterpriseRBACManager()

    admin_ctx = rbac_mgr.resolve_identity_context(
        user_id="admin-alice",
        organization_id="ORG-ACME",
        workspace_id="WS-HIRING",
        roles=[EnterpriseRole.ORG_ADMIN.value],
    )

    # Attempt to bypass security / mark high risk as safe -> MUST FAIL
    for forbidden_key in ["security_authority", "policy_bypass", "mark_high_risk_as_safe"]:
        res = cfg_mgr.set_configuration(
            user_ctx=admin_ctx,
            organization_id="ORG-ACME",
            key=forbidden_key,
            value=True,
        )
        assert res["success"] is False
        assert "Platform Invariant" in res["reason"]


# =========================================================================
# 3. RANGE LIMIT ENFORCEMENT & SIMULATION
# =========================================================================

def test_range_limit_and_simulation():
    """Verifies that values exceeding platform safety bounds are rejected and simulations run safely."""
    cfg_mgr = EnterpriseConfigurationManager()
    rbac_mgr = EnterpriseRBACManager()

    admin_ctx = rbac_mgr.resolve_identity_context(
        user_id="admin-alice",
        organization_id="ORG-ACME",
        workspace_id="WS-HIRING",
        roles=[EnterpriseRole.ORG_ADMIN.value],
    )

    # Attempt to set max_retrieval_hops = 5000 (max allowed is 20) -> MUST FAIL
    res_exceed = cfg_mgr.set_configuration(
        user_ctx=admin_ctx,
        organization_id="ORG-ACME",
        key="max_retrieval_hops",
        value=5000,
    )
    assert res_exceed["success"] is False
    assert "exceeds platform maximum" in res_exceed["reason"]

    # Run dry-run simulation
    sim = cfg_mgr.simulate_configuration_change(
        organization_id="ORG-ACME",
        key="max_retrieval_hops",
        proposed_value=6,
    )
    assert sim is not None
    assert sim.effective_value == 6
    assert len(sim.affected_workflows) >= 1
