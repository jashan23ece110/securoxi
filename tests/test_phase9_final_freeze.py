"""
SECUROXI AI Intelligence 2.0 — Phase 9 Final Platform Validation & Freeze Test Suite (Stage 61)
Comprehensive end-to-end integration and adversarial security regression suite covering:
- Enterprise Control Plane & Unified Policy Fabric (Stage 54)
- Declarative Workflow Composer & Automation Studio (Stage 55)
- Sandboxed Custom Agent / Skill / Tool Platform (Stage 56)
- Governed Enterprise Marketplace & Supply-Chain Security (Stage 57)
- Privacy-Preserving Cross-Organization Benchmarking (Stage 58)
- Autonomous Platform Operations & Self-Healing (Stage 59)
- Enterprise Partner Ecosystem & Delegated Authorization (Stage 60)
"""

import pytest
from securoxi.enterprise.controlplane import (
    EnterpriseControlPlane,
    PolicyDefinition,
    PolicyDomain,
    PolicyStatus,
    CapabilityDefinition,
    CapabilityStatus,
    EvaluationGateState,
    ControlPlaneDecision,
)
from securoxi.enterprise.workflow import (
    EnterpriseWorkflowComposer,
    WorkflowNode,
    WorkflowEdge,
    NodeType,
    TriggerType,
    WorkflowStatus,
    RunStatus,
)
from securoxi.enterprise.extensibility import (
    CustomCapabilityPlatform,
    CapabilityType,
    CapabilityStatus as ExtCapabilityStatus,
    ToolRiskClass,
    DeploymentMode,
)
from securoxi.enterprise.marketplace import (
    EnterpriseMarketplaceEngine,
    PackageType,
    PackageStatus,
    VisibilityScope,
    PackageRiskLevel,
)
from securoxi.enterprise.benchmarking import (
    CrossOrgBenchmarkingEngine,
    ParticipationState,
    BenchmarkDomain,
    ConfidenceLevel,
)
from securoxi.enterprise.operations import (
    AutonomousPlatformOperationsEngine,
    RemediationActionType,
    RemediationRisk,
    ServiceHealthStatus,
)
from securoxi.enterprise.ecosystem import (
    EnterprisePartnerEcosystemEngine,
    PartnerType,
    PartnerVerificationStatus,
    PartnerScope,
)


# =========================================================================
# 1. COMPLETE END-TO-END ENTERPRISE ECOSYSTEM JOURNEY
# =========================================================================

def test_phase9_full_enterprise_ecosystem_journey():
    """
    Validates complete lifecycle: Partner registration -> Custom tool development
    -> Security scan & evaluation gate -> Marketplace publishing -> Customer delegation & install
    -> Workflow execution -> Governed action -> Self-healing platform observation.
    """
    # 1. Partner Onboarding & Verification (Stage 60)
    eco = EnterprisePartnerEcosystemEngine()
    partner = eco.register_partner("Tier1 Integrator", PartnerType.TECHNOLOGY_PARTNER)
    eco.verify_partner(partner.partner_id, PartnerVerificationStatus.APPROVED)

    # 2. Customer creates explicit scoped delegation (Stage 60)
    delegation = eco.create_customer_delegation(
        customer_organization_id="ORG-ENTERPRISE",
        partner_id=partner.partner_id,
        allowed_workspaces=["WS-HIRING"],
        granted_scopes=[PartnerScope.API_READ, PartnerScope.WORKFLOW_CREATE, PartnerScope.MARKETPLACE_PUBLISH],
    )
    assert delegation.status.value == "ACTIVE"

    # 3. Custom Tool Definition & Sandboxed Security Scan (Stage 56)
    ext_platform = CustomCapabilityPlatform()
    cap = ext_platform.register_capability(
        organization_id="ORG-ENTERPRISE",
        name="Greenhouse Sync Tool",
        capability_type=CapabilityType.CUSTOM_TOOL,
        required_permissions=["candidate:read", "ats:sync"],
        allowed_network_destinations=["api.greenhouse.io"],
    )
    assert ext_platform.run_security_scan(cap.capability_id) is True
    eval_res = ext_platform.evaluate_capability(cap.capability_id, security_pass=True, accuracy_score=98.0)
    assert eval_res.passed is True
    assert cap.status == ExtCapabilityStatus.APPROVED
    assert ext_platform.deploy_capability(cap.capability_id, DeploymentMode.PRODUCTION) is True
    assert cap.status == ExtCapabilityStatus.ENABLED

    # 4. Marketplace Publishing & Cryptographic Admission (Stage 57)
    mkt = EnterpriseMarketplaceEngine()
    pkg = mkt.publish_package(
        publisher_organization_id="ORG-ENTERPRISE",
        name="Enterprise Greenhouse Integration Pack",
        package_type=PackageType.CUSTOM_CONNECTOR,
        risk_level=PackageRiskLevel.HIGH,
        visibility=VisibilityScope.ORGANIZATION,
        is_signed=True,
    )
    assert mkt.run_security_scan(pkg.package_id) is True
    mkt_eval = mkt.evaluate_package(pkg.package_id, security_pass=True, accuracy_score=96.0)
    assert mkt_eval.passed is True
    assert pkg.status == PackageStatus.PUBLISHED

    # 5. Governed Installation requiring Stage 23 Human Approval (Stage 57)
    inst_res = mkt.install_package(
        caller_organization_id="ORG-ENTERPRISE",
        workspace_id="WS-HIRING",
        package_id=pkg.package_id,
        installed_by="RECRUITER_ADMIN",
        approved_by="SEC_DIRECTOR",
    )
    assert inst_res["success"] is True

    # 6. Declarative Workflow Composition & Deterministic Execution (Stage 55)
    composer = EnterpriseWorkflowComposer()
    nodes = [
        WorkflowNode(node_id="N-TRIG", node_type=NodeType.TRIGGER, capability_name="EventTrigger"),
        WorkflowNode(node_id="N-SEC", node_type=NodeType.SECURITY_SCAN, capability_name="SecurityAgent"),
        WorkflowNode(node_id="N-SCREEN", node_type=NodeType.HIRING_SCREEN, capability_name="HiringAgent"),
    ]
    edges = [
        WorkflowEdge(source_node_id="N-TRIG", target_node_id="N-SEC"),
        WorkflowEdge(source_node_id="N-SEC", target_node_id="N-SCREEN"),
    ]
    wf = composer.create_workflow(
        organization_id="ORG-ENTERPRISE",
        workspace_id="WS-HIRING",
        name="Governed Hiring Pipeline",
        trigger_type=TriggerType.EVENT,
        nodes=nodes,
        edges=edges,
    )
    val = composer.validate_workflow(wf.workflow_id)
    assert val["valid"] is True

    sim_res = composer.simulate_workflow(wf.workflow_id, sample_payload={"candidate_id": "C-123"})
    assert sim_res.is_simulation is True
    assert len(sim_res.nodes_executed) == 3

    composer.approve_and_activate(wf.workflow_id, "SEC_ADMIN")
    run = composer.execute_workflow(
        workflow_id=wf.workflow_id,
        payload={"candidate_id": "C-123", "security_state": "SAFE"},
    )
    assert run.status == RunStatus.COMPLETED

    # 7. Autonomous Operations Observation & Remediation (Stage 59)
    ops = AutonomousPlatformOperationsEngine()
    ops.ingest_health("hiring_workflow_worker", latency_p95_ms=650.0, queue_depth=1500)
    anomalies = ops.detect_anomalies()
    assert len(anomalies) == 1
    anom = anomalies[0]
    prop = ops.propose_remediation(anom.anomaly_id, RemediationActionType.CLEAR_SAFE_CACHE, RemediationRisk.LOW_SAFE_AUTO)
    rem_res = ops.execute_remediation(prop.proposal_id)
    assert rem_res["success"] is True
    assert ops._services["hiring_workflow_worker"].status == ServiceHealthStatus.HEALTHY


# =========================================================================
# 2. CROSS-TENANT ISOLATION & AUTHORITY DEFENSE
# =========================================================================

def test_phase9_cross_tenant_isolation_and_authority_defense():
    """Verifies complete multi-tenant barriers across ecosystem, marketplace, and control plane."""
    # 1. Cross-Tenant Marketplace Access -> Strictly Denied
    mkt = EnterpriseMarketplaceEngine()
    pkg_alpha = mkt.publish_package(
        publisher_organization_id="ORG-ALPHA",
        name="Alpha Confidential Agent",
        package_type=PackageType.CUSTOM_AGENT,
        visibility=VisibilityScope.PRIVATE,
    )
    mkt.evaluate_package(pkg_alpha.package_id, security_pass=True, accuracy_score=92.0)

    # Tenant Beta attempts installation -> TENANT_ACCESS_DENIED
    res_cross = mkt.install_package(
        caller_organization_id="ORG-BETA",
        workspace_id="WS-BETA",
        package_id=pkg_alpha.package_id,
        installed_by="USER_BETA",
        approved_by="ADMIN_BETA",
    )
    assert res_cross["success"] is False
    assert res_cross["error"] == "TENANT_ACCESS_DENIED"

    # 2. Cross-Tenant Partner Delegation Escape -> Strictly Denied
    eco = EnterprisePartnerEcosystemEngine()
    partner = eco.register_partner("Rogue Partner", PartnerType.SOLUTION_PARTNER)
    eco.verify_partner(partner.partner_id, PartnerVerificationStatus.APPROVED)

    # Partner attempts to access Org Gamma without delegation -> DELEGATION_NOT_FOUND
    res_partner_cross = eco.validate_partner_access(partner.partner_id, "ORG-GAMMA", "WS-GAMMA", PartnerScope.API_READ)
    assert res_partner_cross["authorized"] is False
    assert res_partner_cross["error"] == "DELEGATION_NOT_FOUND"

    # 3. Privacy-Preserving Benchmarking (k-Anonymity Suppression) (Stage 58)
    bench = CrossOrgBenchmarkingEngine()
    bm = bench.register_benchmark(
        domain=BenchmarkDomain.HIRING,
        metric_name="candidate_screen_speed",
        min_sample_size=5,
    )
    # Only 2 organizations participate (< 5) -> Must suppress
    bench.set_participation("ORG-1", ParticipationState.PARTICIPATING)
    bench.set_participation("ORG-2", ParticipationState.PARTICIPATING)
    bench.submit_metric("ORG-1", "candidate_screen_speed", 2.5)
    bench.submit_metric("ORG-2", "candidate_screen_speed", 3.1)
    ds = bench.compute_benchmark(bm.benchmark_id)
    assert ds.is_suppressed is True

    comp_res = bench.get_benchmark_comparison("ORG-1", "candidate_screen_speed")
    assert comp_res.status == "BENCHMARK_UNAVAILABLE"
    assert comp_res.confidence == ConfidenceLevel.INSUFFICIENT_DATA


# =========================================================================
# 3. SUPPLY-CHAIN DEFENSE & INCIDENT CONTAINMENT
# =========================================================================

def test_phase9_supply_chain_defense_and_incident_containment():
    """Verifies instant supply-chain revocation, SSRF blocking, and partner offboarding."""
    # 1. SSRF Attack in Custom Capability Platform -> Auto-Revocation (Stage 56)
    ext_platform = CustomCapabilityPlatform()
    cap_malicious = ext_platform.register_capability(
        organization_id="ORG-TEST",
        name="Internal Scanner",
        capability_type=CapabilityType.CUSTOM_TOOL,
        required_permissions=["admin"],
        allowed_network_destinations=["169.254.169.254"],
    )
    assert ext_platform.run_security_scan(cap_malicious.capability_id) is False
    assert cap_malicious.status == ExtCapabilityStatus.REVOKED

    # 2. Marketplace Supply-Chain Revocation (Stage 57)
    mkt = EnterpriseMarketplaceEngine()
    pkg = mkt.publish_package(
        publisher_organization_id="ORG-VENDOR",
        name="Vulnerable ATS Plugin",
        package_type=PackageType.CUSTOM_TOOL,
        visibility=VisibilityScope.PUBLIC,
        is_signed=True,
    )
    mkt.evaluate_package(pkg.package_id, security_pass=True, accuracy_score=90.0)
    inst = mkt.install_package("ORG-CLIENT", "WS-MAIN", pkg.package_id)
    assert inst["success"] is True

    # Vulnerability discovered -> Trigger emergency revocation
    mkt.revoke_package(pkg.package_id, reason="Zero-Day Remote Vulnerability")
    assert pkg.status == PackageStatus.REVOKED
    assert len(mkt.get_installations("ORG-CLIENT")) == 0

    # 3. Partner Offboarding -> Full Delegation Termination (Stage 60)
    eco = EnterprisePartnerEcosystemEngine()
    compromised_partner = eco.register_partner("Compromised Corp", PartnerType.INTEGRATION_PARTNER)
    eco.verify_partner(compromised_partner.partner_id, PartnerVerificationStatus.APPROVED)
    del_inst = eco.create_customer_delegation("ORG-VICTIM", compromised_partner.partner_id)
    assert del_inst.status.value == "ACTIVE"

    # Offboard compromised partner
    eco.offboard_partner(compromised_partner.partner_id)
    assert compromised_partner.verification_status == PartnerVerificationStatus.REVOKED
    assert del_inst.status.value == "REVOKED"
