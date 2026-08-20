"""
SECUROXI AI Intelligence 2.0 — Custom Agent, Skill & Tool Platform Models (Phase 9 Stage 56)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
from securoxi.enterprise.extensibility.types import (
    CapabilityType,
    CapabilityStatus,
    ToolRiskClass,
    DeploymentMode,
)


@dataclass
class CustomCapability:
    """Canonical custom capability metadata."""
    capability_id: str = field(default_factory=lambda: f"CAP-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: Optional[str] = None
    name: str = "Custom ATS Integration Tool"
    description: str = "Custom connector tool for fetching candidate records"
    capability_type: CapabilityType = CapabilityType.CUSTOM_TOOL
    version: int = 1
    status: CapabilityStatus = CapabilityStatus.DRAFT
    deployment_mode: DeploymentMode = DeploymentMode.DRAFT
    required_permissions: List[str] = field(default_factory=list)
    risk_class: ToolRiskClass = ToolRiskClass.LOW_IMPACT
    autonomy_limit: str = "L2_HUMAN_APPROVAL_REQUIRED"
    dependencies: List[str] = field(default_factory=list)
    allowed_network_destinations: List[str] = field(default_factory=list)
    created_by: str = "DEV_USER"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class CustomAgentDefinition:
    """Custom Agent specification."""
    agent_id: str = field(default_factory=lambda: f"AGT-{uuid.uuid4().hex[:8].upper()}")
    capability_id: str = "CAP-DEFAULT"
    organization_id: str = "ORG-DEFAULT"
    workspace_id: Optional[str] = None
    name: str = "Custom Screening Assistant"
    role: str = "Specialized candidate evaluation agent"
    allowed_tools: List[str] = field(default_factory=list)
    allowed_data_sources: List[str] = field(default_factory=list)
    model_policy: str = "gpt-4o-mini"
    max_tool_calls: int = 10
    system_prompt_reference: str = "PROMPT-REF-001"


@dataclass
class CustomToolDefinition:
    """Custom Tool specification."""
    tool_id: str = field(default_factory=lambda: f"TOOL-{uuid.uuid4().hex[:8].upper()}")
    capability_id: str = "CAP-DEFAULT"
    organization_id: str = "ORG-DEFAULT"
    operation_name: str = "fetch_external_profile"
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    side_effecting: bool = False
    timeout_seconds: float = 30.0
    idempotent: bool = True
    verification_method: Optional[str] = None


@dataclass
class CapabilityEvaluationResult:
    """Stage 33 regression & safety evaluation outcome for a custom capability."""
    evaluation_id: str = field(default_factory=lambda: f"EVAL-{uuid.uuid4().hex[:8].upper()}")
    capability_id: str = "CAP-DEFAULT"
    passed: bool = True
    security_checks_passed: bool = True
    sandbox_checks_passed: bool = True
    score: float = 100.0
    evaluated_at: float = field(default_factory=time.time)
