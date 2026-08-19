"""
SECUROXI AI Intelligence 2.0 — Enterprise Customer Configuration & Policy Models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
import time
import uuid
from securoxi.enterprise.config.types import (
    ConfigCategory,
    ConfigValueType,
    AIBehaviorProfile,
)


@dataclass
class SettingDefinition:
    """Canonical platform definition and boundary for a configuration setting."""
    key: str
    category: ConfigCategory
    value_type: ConfigValueType
    default_value: Any
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    is_configurable: bool = True
    description: str = ""


@dataclass
class ConfigurationEntry:
    """Customer-configured setting override."""
    key: str
    value: Any
    organization_id: str = "ORG-DEFAULT"
    workspace_id: Optional[str] = None
    updated_by: str = "admin@enterprise.com"
    updated_at: float = field(default_factory=time.time)


@dataclass
class ConfigurationVersion:
    """Immutable audit record for configuration changes."""
    version_id: str = field(default_factory=lambda: f"CFG-VER-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: Optional[str] = None
    key: str = ""
    previous_value: Any = None
    new_value: Any = None
    reason: str = "Customer policy update"
    actor: str = "admin@enterprise.com"
    timestamp: float = field(default_factory=time.time)


@dataclass
class SimulationResult:
    """Outcome of a configuration dry-run simulation."""
    key: str
    current_value: Any
    proposed_value: Any
    effective_value: Any
    affected_workflows: List[str] = field(default_factory=list)
    impact_summary: str = ""
