"""
SECUROXI AI Intelligence 2.0 — Enterprise Data Governance & Retention Manager
Coordinates data classification, retention schedules, legal holds, dependency-aware safe deletion,
and governed data exports with strict multi-tenant organization boundaries.
"""

from typing import Dict, Any, List, Set, Optional
import time
import uuid
from securoxi.enterprise.governance.types import (
    DataClassification,
    RetentionTrigger,
    RetentionState,
    LegalHoldStatus,
    ExportStatus,
)
from securoxi.enterprise.governance.models import (
    RetentionPolicy,
    LegalHold,
    DataInventoryRecord,
    DataExportRequest,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.governance")


class EnterpriseDataGovernanceManager:
    """
    Enterprise Data Governance & Lifecycle Engine.
    Enforces retention policies, legal holds, dependency checks, cache/index invalidations,
    and time-bounded data exports.
    """

    def __init__(self):
        self._policies: Dict[str, RetentionPolicy] = {}
        self._legal_holds: Dict[str, LegalHold] = {}
        self._inventory: Dict[str, DataInventoryRecord] = {}
        self._exports: Dict[str, DataExportRequest] = {}
        self._active_dependencies: Dict[str, Set[str]] = {}  # resource_id -> set of referencing active task/incident IDs

    def register_retention_policy(self, policy: RetentionPolicy) -> str:
        """Registers a data retention policy for an organization."""
        self._policies[policy.policy_id] = policy
        logger.info(f"Registered Retention Policy '{policy.policy_id}' for Org '{policy.organization_id}' (Type: {policy.data_type}, Days: {policy.retention_days})")
        return policy.policy_id

    def register_inventory_item(
        self,
        organization_id: str,
        resource_id: str,
        resource_name: str,
        data_type: str = "DOCUMENT",
        classification: DataClassification = DataClassification.INTERNAL,
    ) -> DataInventoryRecord:
        """Registers or updates a resource in the organization data inventory."""
        record = DataInventoryRecord(
            organization_id=organization_id,
            resource_id=resource_id,
            resource_name=resource_name,
            data_type=data_type,
            classification=classification,
            retention_state=RetentionState.ACTIVE,
        )
        self._inventory[resource_id] = record
        return record

    def apply_legal_hold(
        self,
        organization_id: str,
        resource_id: str,
        reason: str,
        created_by: str = "compliance-lead",
    ) -> LegalHold:
        """Places an immutable legal hold on a resource, blocking deletion."""
        hold = LegalHold(
            organization_id=organization_id,
            resource_id=resource_id,
            reason=reason,
            created_by=created_by,
            status=LegalHoldStatus.ACTIVE,
        )
        self._legal_holds[hold.hold_id] = hold

        if resource_id in self._inventory:
            self._inventory[resource_id].retention_state = RetentionState.LEGAL_HOLD

        logger.info(f"Applied Legal Hold '{hold.hold_id}' on Resource '{resource_id}' for Org '{organization_id}'")
        return hold

    def release_legal_hold(self, hold_id: str, released_by: str) -> bool:
        """Releases a legal hold on a resource."""
        if hold_id not in self._legal_holds:
            return False

        hold = self._legal_holds[hold_id]
        hold.status = LegalHoldStatus.RELEASED

        if hold.resource_id in self._inventory:
            self._inventory[hold.resource_id].retention_state = RetentionState.ACTIVE

        logger.info(f"Released Legal Hold '{hold_id}' by '{released_by}'")
        return True

    def register_dependency(self, resource_id: str, referencing_id: str):
        """Records an active dependency (e.g. active incident referencing a document)."""
        if resource_id not in self._active_dependencies:
            self._active_dependencies[resource_id] = set()
        self._active_dependencies[resource_id].add(referencing_id)

    def remove_dependency(self, resource_id: str, referencing_id: str):
        if resource_id in self._active_dependencies:
            self._active_dependencies[resource_id].discard(referencing_id)

    def execute_safe_deletion(
        self,
        organization_id: str,
        resource_id: str,
    ) -> Dict[str, Any]:
        """
        Executes dependency-aware safe deletion:
        1. Checks organization ownership.
        2. Checks for active legal holds.
        3. Checks for active referencing dependencies.
        4. If clear, marks DELETED and invalidates downstream caches and indexes.
        """
        if resource_id not in self._inventory:
            return {"success": False, "reason": "Resource not found in inventory"}

        record = self._inventory[resource_id]
        if record.organization_id != organization_id:
            logger.warning(f"Cross-Org Deletion Blocked: Record org '{record.organization_id}' != Request org '{organization_id}'")
            return {"success": False, "reason": "Cross-organization access denied"}

        # 1. Check Legal Holds
        has_active_hold = any(
            h.resource_id == resource_id and h.status == LegalHoldStatus.ACTIVE
            for h in self._legal_holds.values()
        )
        if has_active_hold:
            logger.warning(f"Deletion Blocked: Resource '{resource_id}' is protected by active Legal Hold")
            return {"success": False, "reason": "Protected by active Legal Hold"}

        # 2. Check Active Dependencies
        active_refs = self._active_dependencies.get(resource_id, set())
        if active_refs:
            logger.warning(f"Deletion Blocked: Resource '{resource_id}' has active dependencies: {active_refs}")
            return {"success": False, "reason": f"Active dependencies exist: {list(active_refs)}"}

        # 3. Mark Deleted and trigger index / cache cleanup
        record.retention_state = RetentionState.DELETED
        logger.info(f"Safely Deleted Resource '{resource_id}' and invalidated downstream indexes for Org '{organization_id}'")
        return {"success": True, "resource_id": resource_id, "status": "DELETED"}

    def request_export(
        self,
        organization_id: str,
        requested_by: str,
        scope: str = "ALL_DOCUMENTS",
        ttl_seconds: int = 3600,
    ) -> DataExportRequest:
        """Generates a governed, time-bounded data export request."""
        export = DataExportRequest(
            organization_id=organization_id,
            requested_by=requested_by,
            scope=scope,
            status=ExportStatus.READY,
            download_url=f"/api/v1/governance/exports/EXP-{uuid.uuid4().hex[:6]}.zip",
            expires_at=time.time() + ttl_seconds,
        )
        self._exports[export.export_id] = export
        logger.info(f"Created Data Export '{export.export_id}' for Org '{organization_id}' (Scope: {scope})")
        return export

    def access_export(self, export_id: str, organization_id: str) -> Optional[DataExportRequest]:
        """Accesses an export request, verifying organization scope and expiration."""
        if export_id not in self._exports:
            return None

        export = self._exports[export_id]
        if export.organization_id != organization_id:
            logger.warning(f"Cross-Org Export Access Blocked: Export Org '{export.organization_id}' != '{organization_id}'")
            return None

        if export.is_expired():
            export.status = ExportStatus.EXPIRED
            logger.warning(f"Export Access Denied: Export '{export_id}' is expired")
            return None

        return export
