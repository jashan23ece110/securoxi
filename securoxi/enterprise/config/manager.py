"""
SECUROXI AI Intelligence 2.0 — Enterprise Configuration Manager
Coordinates customer-level policy settings, hierarchical overrides, safety bounds validation,
dry-run simulations, and versioned rollbacks.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.enterprise.config.types import (
    ConfigCategory,
    ConfigValueType,
    AIBehaviorProfile,
)
from securoxi.enterprise.config.models import (
    SettingDefinition,
    ConfigurationEntry,
    ConfigurationVersion,
    SimulationResult,
)
from securoxi.enterprise.config.registry import (
    PLATFORM_SETTING_REGISTRY,
    FORBIDDEN_SETTINGS,
)
from securoxi.enterprise.identity.models import IdentityContext
from securoxi.enterprise.identity.types import Permission
from securoxi.logger import get_logger

logger = get_logger("enterprise.config")


class EnterpriseConfigurationManager:
    """
    Enterprise Policy & Configuration Management Engine.
    Enforces immutable security boundaries, hierarchical inheritance, and auditable versioning.
    """

    def __init__(self):
        self._org_configs: Dict[str, Dict[str, ConfigurationEntry]] = {}  # org_id -> {key: Entry}
        self._ws_configs: Dict[str, Dict[str, ConfigurationEntry]] = {}   # ws_id -> {key: Entry}
        self._versions: Dict[str, List[ConfigurationVersion]] = {}       # org_id -> [Version]

    def get_effective_value(
        self,
        organization_id: str,
        key: str,
        workspace_id: Optional[str] = None,
    ) -> Any:
        """
        Calculates effective configuration through hierarchical inheritance:
        Platform Default -> Organization Setting -> Workspace Override.
        """
        if key not in PLATFORM_SETTING_REGISTRY:
            return None

        setting_def = PLATFORM_SETTING_REGISTRY[key]
        effective = setting_def.default_value

        # 1. Organization Level
        org_map = self._org_configs.get(organization_id, {})
        if key in org_map:
            effective = org_map[key].value

        # 2. Workspace Level Override
        if workspace_id:
            ws_map = self._ws_configs.get(workspace_id, {})
            if key in ws_map:
                effective = ws_map[key].value

        return effective

    def set_configuration(
        self,
        user_ctx: IdentityContext,
        organization_id: str,
        key: str,
        value: Any,
        workspace_id: Optional[str] = None,
        reason: str = "Customer policy adjustment",
    ) -> Dict[str, Any]:
        """
        Validates and updates customer configuration with immutable audit versioning.
        Rejects forbidden invariants and values outside platform safety bounds.
        """
        # 1. Reject Forbidden Invariants
        if key in FORBIDDEN_SETTINGS or key.lower() in FORBIDDEN_SETTINGS:
            logger.warning(f"Configuration Update Blocked: '{key}' is an immutable security invariant")
            return {"success": False, "reason": f"Setting '{key}' cannot be modified by customers (Platform Invariant)"}

        if key not in PLATFORM_SETTING_REGISTRY:
            logger.warning(f"Configuration Update Blocked: Unknown key '{key}'")
            return {"success": False, "reason": f"Unknown configuration setting '{key}'"}

        # 2. RBAC & Organization Check
        if user_ctx.organization_id != organization_id:
            return {"success": False, "reason": "Cross-organization access denied"}

        if not user_ctx.has_permission(Permission.POLICY_MANAGE) and not user_ctx.has_permission(Permission.ORG_UPDATE):
            return {"success": False, "reason": "Missing POLICY_MANAGE or ORG_UPDATE permission"}

        # 3. Validate Value Bounds
        setting_def = PLATFORM_SETTING_REGISTRY[key]
        if setting_def.min_value is not None and value < setting_def.min_value:
            return {"success": False, "reason": f"Value {value} is below platform minimum {setting_def.min_value}"}

        if setting_def.max_value is not None and value > setting_def.max_value:
            return {"success": False, "reason": f"Value {value} exceeds platform maximum {setting_def.max_value}"}

        if setting_def.allowed_values and value not in setting_def.allowed_values:
            return {"success": False, "reason": f"Value {value} is not in allowed choices: {setting_def.allowed_values}"}

        # 4. Record Previous Value and Apply
        prev_value = self.get_effective_value(organization_id, key, workspace_id)
        entry = ConfigurationEntry(
            key=key,
            value=value,
            organization_id=organization_id,
            workspace_id=workspace_id,
            updated_by=user_ctx.user_id,
        )

        if workspace_id:
            if workspace_id not in self._ws_configs:
                self._ws_configs[workspace_id] = {}
            self._ws_configs[workspace_id][key] = entry
        else:
            if organization_id not in self._org_configs:
                self._org_configs[organization_id] = {}
            self._org_configs[organization_id][key] = entry

        # 5. Record Immutable Version
        version = ConfigurationVersion(
            organization_id=organization_id,
            workspace_id=workspace_id,
            key=key,
            previous_value=prev_value,
            new_value=value,
            reason=reason,
            actor=user_ctx.user_id,
        )
        if organization_id not in self._versions:
            self._versions[organization_id] = []
        self._versions[organization_id].append(version)

        logger.info(f"Updated Configuration '{key}' for Org '{organization_id}' (New: {value}, Prev: {prev_value}) by '{user_ctx.user_id}'")
        return {"success": True, "version_id": version.version_id, "effective_value": value}

    def simulate_configuration_change(
        self,
        organization_id: str,
        key: str,
        proposed_value: Any,
        workspace_id: Optional[str] = None,
    ) -> Optional[SimulationResult]:
        """Runs a dry-run simulation of a configuration change."""
        if key not in PLATFORM_SETTING_REGISTRY:
            return None

        current = self.get_effective_value(organization_id, key, workspace_id)
        setting_def = PLATFORM_SETTING_REGISTRY[key]

        # Calculate effective proposed value within safety bounds
        effective_proposed = proposed_value
        if setting_def.min_value is not None:
            effective_proposed = max(effective_proposed, setting_def.min_value)
        if setting_def.max_value is not None:
            effective_proposed = min(effective_proposed, setting_def.max_value)

        workflows = ["Autonomous Task Execution", "Screening Pipeline"]
        if setting_def.category == ConfigCategory.RETRIEVAL:
            workflows = ["Ask SECUROXI", "Agentic RAG", "Forensic Investigation"]

        return SimulationResult(
            key=key,
            current_value=current,
            proposed_value=proposed_value,
            effective_value=effective_proposed,
            affected_workflows=workflows,
            impact_summary=f"Updating {key} from {current} to {effective_proposed} within platform safety limits.",
        )
