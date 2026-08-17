"""
SECUROXI AI Phase 3 Stage 9 — Enterprise Control Plane, Governance & Observability Engine
Implements Multi-Tenancy Isolation, Role-Based Access Control (RBAC), API Key Management,
Data Retention Controls, and System Observability Metrics.
"""

import time
import uuid
import hashlib
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from securoxi.logger import get_logger


class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SECURITY_ADMIN = "SECURITY_ADMIN"
    RECRUITER = "RECRUITER"
    AUDITOR = "AUDITOR"


class ControlPlanePermission(str, Enum):
    READ_SCAN = "READ_SCAN"
    WRITE_SCAN = "WRITE_SCAN"
    MANAGE_POLICY = "MANAGE_POLICY"
    RESOLVE_INCIDENT = "RESOLVE_INCIDENT"
    MANAGE_TENANTS = "MANAGE_TENANTS"
    READ_AUDIT_LOGS = "READ_AUDIT_LOGS"


ROLE_PERMISSIONS: Dict[UserRole, Set[ControlPlanePermission]] = {
    UserRole.SUPER_ADMIN: {
        ControlPlanePermission.READ_SCAN,
        ControlPlanePermission.WRITE_SCAN,
        ControlPlanePermission.MANAGE_POLICY,
        ControlPlanePermission.RESOLVE_INCIDENT,
        ControlPlanePermission.MANAGE_TENANTS,
        ControlPlanePermission.READ_AUDIT_LOGS
    },
    UserRole.SECURITY_ADMIN: {
        ControlPlanePermission.READ_SCAN,
        ControlPlanePermission.WRITE_SCAN,
        ControlPlanePermission.MANAGE_POLICY,
        ControlPlanePermission.RESOLVE_INCIDENT,
        ControlPlanePermission.READ_AUDIT_LOGS
    },
    UserRole.RECRUITER: {
        ControlPlanePermission.READ_SCAN,
        ControlPlanePermission.WRITE_SCAN
    },
    UserRole.AUDITOR: {
        ControlPlanePermission.READ_SCAN,
        ControlPlanePermission.READ_AUDIT_LOGS
    }
}


@dataclass
class OrganizationTenant:
    """Enterprise Tenant Object for multi-tenancy isolation."""
    tenant_id: str
    name: str
    retention_days: int = 90
    created_at: float = field(default_factory=time.time)
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "retention_days": self.retention_days,
            "created_at": self.created_at,
            "is_active": self.is_active
        }


@dataclass
class APIKeyRecord:
    """API Key credentials record."""
    key_id: str
    tenant_id: str
    key_hash: str
    role: UserRole
    created_at: float = field(default_factory=time.time)
    is_active: bool = True


class EnterpriseControlPlane:
    """
    Enterprise Governance, RBAC, Multi-Tenancy & Observability Manager.
    """

    def __init__(self):
        self.logger = get_logger("securoxi.control_plane")
        self.tenants: Dict[str, OrganizationTenant] = {}
        self.api_keys: Dict[str, APIKeyRecord] = {}
        self.metrics_summary = {
            "total_scans": 0,
            "threats_detected": 0,
            "active_incidents": 0,
            "total_latency_ms": 0.0
        }
        self._initialize_default_tenant()

    def _initialize_default_tenant(self):
        default_tenant = OrganizationTenant(tenant_id="TENANT-DEFAULT", name="Default Enterprise Corp", retention_days=90)
        self.tenants[default_tenant.tenant_id] = default_tenant

    def create_tenant(self, name: str, retention_days: int = 90) -> OrganizationTenant:
        tenant_id = f"TENANT-{uuid.uuid4().hex[:8]}"
        tenant = OrganizationTenant(tenant_id=tenant_id, name=name, retention_days=retention_days)
        self.tenants[tenant_id] = tenant
        self.logger.info(f"Created Enterprise Tenant '{tenant_id}' ({name})")
        return tenant

    def create_api_key(self, tenant_id: str, role: UserRole) -> (str, APIKeyRecord):
        if tenant_id not in self.tenants:
            raise KeyError(f"Tenant '{tenant_id}' does not exist.")

        raw_key = f"securoxi_live_{uuid.uuid4().hex}"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        key_id = f"KEY-{uuid.uuid4().hex[:8]}"

        record = APIKeyRecord(key_id=key_id, tenant_id=tenant_id, key_hash=key_hash, role=role)
        self.api_keys[key_hash] = record
        self.logger.info(f"Generated API Key '{key_id}' for Tenant '{tenant_id}' with Role '{role.value}'")
        return raw_key, record

    def check_permission(self, raw_api_key: str, required_perm: ControlPlanePermission) -> (bool, str, UserRole):
        """Verifies API key validity and RBAC permissions."""
        key_hash = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
        record = self.api_keys.get(key_hash)

        if not record or not record.is_active:
            return False, "UNAUTHORIZED: Invalid or revoked API key", UserRole.RECRUITER

        tenant = self.tenants.get(record.tenant_id)
        if not tenant or not tenant.is_active:
            return False, "UNAUTHORIZED: Inactive or suspended tenant", record.role

        allowed_perms = ROLE_PERMISSIONS.get(record.role, set())
        if required_perm not in allowed_perms:
            return False, f"FORBIDDEN: Role '{record.role.value}' lacks required permission '{required_perm.value}'", record.role

        return True, record.tenant_id, record.role

    def record_scan_metrics(self, latency_ms: float, has_threat: bool):
        self.metrics_summary["total_scans"] += 1
        self.metrics_summary["total_latency_ms"] += latency_ms
        if has_threat:
            self.metrics_summary["threats_detected"] += 1

    def get_system_metrics(self) -> Dict[str, Any]:
        scans = self.metrics_summary["total_scans"]
        avg_latency = (self.metrics_summary["total_latency_ms"] / scans) if scans > 0 else 0.0
        detection_rate = (self.metrics_summary["threats_detected"] / scans * 100.0) if scans > 0 else 0.0

        return {
            "total_tenants": len(self.tenants),
            "total_active_keys": sum(1 for k in self.api_keys.values() if k.is_active),
            "total_scans_processed": scans,
            "threats_detected": self.metrics_summary["threats_detected"],
            "detection_rate_pct": round(detection_rate, 2),
            "average_scan_latency_ms": round(avg_latency, 2),
            "system_health": "HEALTHY"
        }
