"""
SECUROXI AI Intelligence 2.0 — Platform Configuration Registry & Safety Invariants
Defines permitted customer-configurable keys, safe bounds, and immutable security invariants.
"""

from typing import Dict, Set
from securoxi.enterprise.config.types import (
    ConfigCategory,
    ConfigValueType,
    AIBehaviorProfile,
)
from securoxi.enterprise.config.models import SettingDefinition


FORBIDDEN_SETTINGS: Set[str] = {
    "security_authority",
    "tenant_isolation",
    "audit_integrity",
    "policy_bypass",
    "evidence_verification_requirement",
    "mark_high_risk_as_safe",
    "disable_prompt_injection_detection",
    "grant_agent_admin_privilege",
}


PLATFORM_SETTING_REGISTRY: Dict[str, SettingDefinition] = {
    "max_retrieval_hops": SettingDefinition(
        key="max_retrieval_hops",
        category=ConfigCategory.RETRIEVAL,
        value_type=ConfigValueType.INTEGER,
        default_value=3,
        min_value=1,
        max_value=20,
        is_configurable=True,
        description="Maximum multi-hop retrieval depth for Agentic RAG workflows",
    ),
    "default_task_budget_usd": SettingDefinition(
        key="default_task_budget_usd",
        category=ConfigCategory.TASKS,
        value_type=ConfigValueType.FLOAT,
        default_value=10.0,
        min_value=1.0,
        max_value=100.0,
        is_configurable=True,
        description="Cost ceiling per autonomous task run",
    ),
    "shortlist_default_size": SettingDefinition(
        key="shortlist_default_size",
        category=ConfigCategory.HIRING,
        value_type=ConfigValueType.INTEGER,
        default_value=20,
        min_value=1,
        max_value=100,
        is_configurable=True,
        description="Target candidate shortlist volume for hiring screenings",
    ),
    "require_ats_write_approval": SettingDefinition(
        key="require_ats_write_approval",
        category=ConfigCategory.GOVERNANCE,
        value_type=ConfigValueType.BOOLEAN,
        default_value=True,
        is_configurable=True,
        description="Enforces human approval before mutating candidate stages in connected ATS",
    ),
    "ai_behavior_profile": SettingDefinition(
        key="ai_behavior_profile",
        category=ConfigCategory.AI_INTELLIGENCE,
        value_type=ConfigValueType.STRING,
        default_value=AIBehaviorProfile.BALANCED.value,
        allowed_values=[p.value for p in AIBehaviorProfile],
        is_configurable=True,
        description="AI reasoning depth and latency profile (FAST, BALANCED, DEEP)",
    ),
    "security_review_threshold": SettingDefinition(
        key="security_review_threshold",
        category=ConfigCategory.SECURITY,
        value_type=ConfigValueType.FLOAT,
        default_value=0.75,
        min_value=0.50,  # Platform Floor: cannot lower sensitivity below 0.50
        max_value=0.95,
        is_configurable=True,
        description="Sensitivity threshold for flagging suspicious candidate resumes for human review",
    ),
}
