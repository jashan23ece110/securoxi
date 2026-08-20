"""
SECUROXI AI Intelligence 2.0 — Custom Agent, Skill & Tool Platform Test Suite (Phase 9 Stage 56)
Validates registration, SSRF security scanning, evaluation gates, sandboxed invocation,
cross-tenant isolation barriers, and global kill switch controls.
"""

import pytest
from securoxi.enterprise.extensibility import (
    CustomCapabilityPlatform,
    CapabilityType,
    CapabilityStatus,
    ToolRiskClass,
    DeploymentMode,
)


# =========================================================================
# 1. REGISTRATION & SSRF SECURITY SCANNING
# =========================================================================

def test_capability_registration_and_security_scan():
    """Verifies that capabilities with dangerous hosts are revoked during security scan."""
    platform = CustomCapabilityPlatform()

    # 1. Register Safe Capability
    cap_safe = platform.register_capability(
        organization_id="ORG-TEST",
        name="Candidate Enrichment Tool",
        capability_type=CapabilityType.CUSTOM_TOOL,
        required_permissions=["candidate:read"],
        allowed_network_destinations=["api.greenhouse.io"],
    )
    assert cap_safe.status == CapabilityStatus.DRAFT
    assert platform.run_security_scan(cap_safe.capability_id) is True
    assert cap_safe.status == CapabilityStatus.SECURITY_REVIEW

    # 2. Register Malicious Capability (targets internal metadata SSRF endpoint)
    cap_ssrf = platform.register_capability(
        organization_id="ORG-TEST",
        name="Malicious Metadata Exfiltrator",
        capability_type=CapabilityType.CUSTOM_TOOL,
        required_permissions=["admin"],
        allowed_network_destinations=["169.254.169.254"],
    )
    assert platform.run_security_scan(cap_ssrf.capability_id) is False
    assert cap_ssrf.status == CapabilityStatus.REVOKED


# =========================================================================
# 2. EVALUATION GATES & DEPLOYMENT LIFECYCLE
# =========================================================================

def test_evaluation_gates_and_deployment():
    """Verifies that capabilities must pass evaluation before deployment."""
    platform = CustomCapabilityPlatform()

    cap = platform.register_capability(
        organization_id="ORG-TEST",
        name="ATS Sync Connector",
        capability_type=CapabilityType.CUSTOM_CONNECTOR,
        required_permissions=["ats:sync"],
    )

    # 1. Cannot deploy DRAFT capability directly
    assert platform.deploy_capability(cap.capability_id, DeploymentMode.PRODUCTION) is False

    # 2. Failed Evaluation -> Status is DISABLED
    eval_fail = platform.evaluate_capability(cap.capability_id, security_pass=False, accuracy_score=50.0)
    assert eval_fail.passed is False
    assert cap.status == CapabilityStatus.DISABLED

    # 3. Passed Evaluation -> Status becomes APPROVED
    eval_pass = platform.evaluate_capability(cap.capability_id, security_pass=True, accuracy_score=95.0)
    assert eval_pass.passed is True
    assert cap.status == CapabilityStatus.APPROVED

    # 4. Deploy Approved Capability -> Status becomes ENABLED
    assert platform.deploy_capability(cap.capability_id, DeploymentMode.PRODUCTION) is True
    assert cap.status == CapabilityStatus.ENABLED


# =========================================================================
# 3. SANDBOXED INVOCATION, TENANT ISOLATION & KILL SWITCH
# =========================================================================

def test_sandboxed_invocation_and_tenant_isolation():
    """Verifies tool execution respects tenant isolation, network allowlists, and kill switch."""
    platform = CustomCapabilityPlatform()

    cap = platform.register_capability(
        organization_id="ORG-ALPHA",
        name="Enrichment Tool",
        capability_type=CapabilityType.CUSTOM_TOOL,
        required_permissions=["read"],
        allowed_network_destinations=["api.enrichment.com"],
    )
    platform.evaluate_capability(cap.capability_id, security_pass=True, accuracy_score=90.0)
    platform.deploy_capability(cap.capability_id, DeploymentMode.PRODUCTION)

    # 1. Cross-Tenant Red Team: Org Beta tries to invoke Org Alpha tool -> DENIED
    res_cross = platform.invoke_custom_tool(
        capability_id=cap.capability_id,
        caller_organization_id="ORG-BETA",
        inputs={"id": "123"},
    )
    assert res_cross["success"] is False
    assert res_cross["error"] == "TENANT_ACCESS_DENIED"

    # 2. Authorized Invocation with Allowed Network Destination -> SUCCESS
    res_auth = platform.invoke_custom_tool(
        capability_id=cap.capability_id,
        caller_organization_id="ORG-ALPHA",
        inputs={"id": "123"},
        destination_url="https://api.enrichment.com/v1/profile",
    )
    assert res_auth["success"] is True

    # 3. Network Policy Violation (Destination not in allowlist) -> BLOCKED
    res_blocked = platform.invoke_custom_tool(
        capability_id=cap.capability_id,
        caller_organization_id="ORG-ALPHA",
        inputs={"id": "123"},
        destination_url="https://unauthorized-evil.com/leak",
    )
    assert res_blocked["success"] is False
    assert res_blocked["error"] == "NETWORK_POLICY_VIOLATION"

    # 4. Global Kill Switch -> BLOCKS ALL
    platform.set_global_kill_switch(True)
    res_kill = platform.invoke_custom_tool(
        capability_id=cap.capability_id,
        caller_organization_id="ORG-ALPHA",
        inputs={"id": "123"},
    )
    assert res_kill["success"] is False
    assert res_kill["error"] == "GLOBAL_KILL_SWITCH_ACTIVE"
