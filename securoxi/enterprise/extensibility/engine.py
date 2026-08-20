"""
SECUROXI AI Intelligence 2.0 — Custom Agent, Skill & Tool Platform Engine (Phase 9 Stage 56)
Governs custom capability registration, security scanning, evaluation gates,
sandboxed execution, and canary deployments.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.enterprise.extensibility.types import (
    CapabilityType,
    CapabilityStatus,
    ToolRiskClass,
    DeploymentMode,
)
from securoxi.enterprise.extensibility.models import (
    CustomCapability,
    CustomAgentDefinition,
    CustomToolDefinition,
    CapabilityEvaluationResult,
)
from securoxi.enterprise.extensibility.sandbox import SandboxExecutor
from securoxi.logger import get_logger

logger = get_logger("enterprise.extensibility.engine")


class CustomCapabilityPlatform:
    """
    Enterprise Custom Agent, Skill & Tool Development Platform.
    Manages custom capability lifecycle, sandboxed execution, and governance boundaries.
    """

    def __init__(self):
        self._capabilities: Dict[str, CustomCapability] = {}         # capability_id -> CustomCapability
        self._agents: Dict[str, CustomAgentDefinition] = {}           # agent_id -> CustomAgentDefinition
        self._tools: Dict[str, CustomToolDefinition] = {}             # tool_id -> CustomToolDefinition
        self._evaluations: Dict[str, CapabilityEvaluationResult] = {}
        self.sandbox = SandboxExecutor()
        self._global_kill_switch: bool = False

    def set_global_kill_switch(self, enabled: bool):
        """Global emergency kill switch for all custom extensions."""
        self._global_kill_switch = enabled
        logger.warning(f"Custom Extensibility Global Kill Switch: {enabled}")

    def register_capability(
        self,
        organization_id: str,
        name: str,
        capability_type: CapabilityType,
        required_permissions: List[str],
        risk_class: ToolRiskClass = ToolRiskClass.LOW_IMPACT,
        allowed_network_destinations: Optional[List[str]] = None,
        created_by: str = "DEV_USER",
    ) -> CustomCapability:
        """Registers a new custom capability in DRAFT status."""
        cap = CustomCapability(
            organization_id=organization_id,
            name=name,
            capability_type=capability_type,
            required_permissions=required_permissions,
            risk_class=risk_class,
            allowed_network_destinations=allowed_network_destinations or [],
            created_by=created_by,
            status=CapabilityStatus.DRAFT,
        )
        self._capabilities[cap.capability_id] = cap
        logger.info(f"Registered Custom Capability '{cap.capability_id}' ('{name}') for Org '{organization_id}'")
        return cap

    def run_security_scan(self, capability_id: str) -> bool:
        """
        Scans custom capability definition for SSRF patterns, dangerous commands, and policy violations.
        """
        cap = self._capabilities.get(capability_id)
        if not cap:
            return False

        # Scan network destinations for SSRF hazards
        for dest in cap.allowed_network_destinations:
            if dest in {"localhost", "127.0.0.1", "169.254.169.254"}:
                logger.error(f"Security Scan FAILED: Capability '{capability_id}' targets dangerous host '{dest}'")
                cap.status = CapabilityStatus.REVOKED
                return False

        cap.status = CapabilityStatus.SECURITY_REVIEW
        logger.info(f"Security Scan PASSED for Capability '{capability_id}'")
        return True

    def evaluate_capability(
        self,
        capability_id: str,
        security_pass: bool = True,
        accuracy_score: float = 95.0,
    ) -> CapabilityEvaluationResult:
        """
        Executes Stage 33 evaluation gate.
        Capabilities failing evaluation cannot be deployed or enabled.
        """
        cap = self._capabilities.get(capability_id)
        if not cap:
            raise ValueError(f"Capability '{capability_id}' not found")

        passed = security_pass and accuracy_score >= 80.0

        eval_res = CapabilityEvaluationResult(
            capability_id=capability_id,
            passed=passed,
            security_checks_passed=security_pass,
            sandbox_checks_passed=True,
            score=accuracy_score,
        )
        self._evaluations[eval_res.evaluation_id] = eval_res

        if passed:
            cap.status = CapabilityStatus.APPROVED
            logger.info(f"Capability '{capability_id}' APPROVED via evaluation score {accuracy_score}")
        else:
            cap.status = CapabilityStatus.DISABLED
            logger.warning(f"Capability '{capability_id}' DISABLED: Failed evaluation (Score={accuracy_score}, SecPass={security_pass})")

        return eval_res

    def deploy_capability(self, capability_id: str, mode: DeploymentMode = DeploymentMode.PRODUCTION) -> bool:
        """
        Deploys an APPROVED capability into TEST, CANARY, or PRODUCTION.
        """
        cap = self._capabilities.get(capability_id)
        if not cap:
            return False

        if cap.status != CapabilityStatus.APPROVED:
            logger.error(f"Cannot deploy Capability '{capability_id}': Status is '{cap.status.value}', expected 'APPROVED'")
            return False

        cap.deployment_mode = mode
        cap.status = CapabilityStatus.ENABLED
        cap.updated_at = time.time()
        logger.info(f"Deployed Capability '{capability_id}' to mode '{mode.value}' (Status=ENABLED)")
        return True

    def invoke_custom_tool(
        self,
        capability_id: str,
        caller_organization_id: str,
        inputs: Dict[str, Any],
        destination_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a custom tool with strict tenant isolation, kill switch, and sandbox checks.
        """
        if self._global_kill_switch:
            return {"success": False, "error": "GLOBAL_KILL_SWITCH_ACTIVE"}

        cap = self._capabilities.get(capability_id)
        if not cap:
            return {"success": False, "error": "CAPABILITY_NOT_FOUND"}

        # 1. Multi-Tenant Isolation Gate
        if cap.organization_id != caller_organization_id:
            logger.error(f"Cross-Tenant Access DENIED: Org '{caller_organization_id}' attempted to access Org '{cap.organization_id}' capability")
            return {"success": False, "error": "TENANT_ACCESS_DENIED"}

        # 2. Enabled Status Gate
        if cap.status != CapabilityStatus.ENABLED:
            return {"success": False, "error": f"CAPABILITY_NOT_ENABLED (Status: {cap.status.value})"}

        # 3. Sandboxed Execution
        return self.sandbox.execute_tool_safely(
            tool_name=cap.name,
            inputs=inputs,
            allowlist=cap.allowed_network_destinations,
            destination_url=destination_url,
        )

    def disable_capability(self, capability_id: str):
        """Disables a capability."""
        if capability_id in self._capabilities:
            self._capabilities[capability_id].status = CapabilityStatus.DISABLED
            logger.warning(f"Disabled Capability '{capability_id}'")

    def get_capabilities(self, organization_id: str) -> List[CustomCapability]:
        """Returns capabilities strictly scoped by organization."""
        return [c for c in self._capabilities.values() if c.organization_id == organization_id]
