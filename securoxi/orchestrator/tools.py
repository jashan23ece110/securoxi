"""
SECUROXI AI Intelligence 2.0 — Secure Tool Registry & Tool Authorizer
Provides explicit tool registration, parameter validation, tenant isolation enforcement,
and policy-governed execution authorization.
"""

import time
import inspect
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from securoxi.orchestrator.types import TrustLevel, ExecutionType
from securoxi.orchestrator.errors import (
    ToolNotFoundError,
    AuthorizationError,
    TenantAccessError,
    ToolValidationError,
    PolicyDeniedError,
    ToolTimeoutError,
)
from securoxi.brain.policy_engine import SecuroxiPolicyEngine, PolicyContext, PolicyDecisionAction


@dataclass
class ToolParameter:
    """Specification of an individual tool input parameter."""
    name: str
    param_type: str = "string"  # "string", "int", "float", "bool", "list", "dict"
    description: str = ""
    required: bool = True
    default: Any = None


@dataclass
class ToolDefinition:
    """Strongly-typed declarative definition of an orchestrator capability."""
    tool_id: str
    name: str
    description: str
    handler: Callable[..., Any]
    parameters: List[ToolParameter] = field(default_factory=list)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    timeout_sec: float = 30.0
    required_permissions: List[str] = field(default_factory=list)
    tenant_scope: Optional[str] = None  # None = multi-tenant capable; otherwise specific tenant ID
    trust_level: TrustLevel = TrustLevel.LOW_RISK
    execution_type: ExecutionType = ExecutionType.DETERMINISTIC
    is_idempotent: bool = True
    max_retries: int = 3
    version: str = "1.0.0"

    def validate_inputs(self, kwargs: Dict[str, Any]):
        """Validates provided arguments against the declared parameter specifications."""
        for param in self.parameters:
            if param.name not in kwargs or kwargs[param.name] is None:
                if param.required:
                    raise ToolValidationError(
                        f"Missing required parameter '{param.name}' for tool '{self.tool_id}'"
                    )
                else:
                    kwargs[param.name] = param.default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "parameters": [
                {
                    "name": p.name,
                    "param_type": p.param_type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                }
                for p in self.parameters
            ],
            "output_schema": self.output_schema,
            "timeout_sec": self.timeout_sec,
            "required_permissions": self.required_permissions,
            "tenant_scope": self.tenant_scope,
            "trust_level": self.trust_level.value,
            "execution_type": self.execution_type.value,
            "is_idempotent": self.is_idempotent,
            "max_retries": self.max_retries,
            "version": self.version,
        }


class ToolRegistry:
    """Central registry of authorized orchestrator tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        """Registers a tool definition."""
        self._tools[tool.tool_id] = tool

    def get(self, tool_id: str) -> ToolDefinition:
        """Retrieves a registered tool by tool_id. Raises ToolNotFoundError if missing."""
        if tool_id not in self._tools:
            raise ToolNotFoundError(f"Tool '{tool_id}' is not registered in ToolRegistry.")
        return self._tools[tool_id]

    def list_tools(self, tenant_id: Optional[str] = None) -> List[ToolDefinition]:
        """Lists all registered tools accessible to a given tenant."""
        if not tenant_id:
            return list(self._tools.values())
        return [
            t for t in self._tools.values()
            if t.tenant_scope is None or t.tenant_scope == tenant_id
        ]

    def unregister(self, tool_id: str):
        if tool_id in self._tools:
            del self._tools[tool_id]


class ToolAuthorizer:
    """Enforces multi-tenant boundaries, actor permissions, and enterprise policy rules."""

    def __init__(self, policy_engine: Optional[SecuroxiPolicyEngine] = None):
        self.policy_engine = policy_engine or SecuroxiPolicyEngine()

    def authorize(
        self,
        tool: ToolDefinition,
        tenant_id: str,
        actor_id: str,
        actor_permissions: List[str],
        actor_trust_level: TrustLevel = TrustLevel.LOW_RISK,
        tool_args: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Evaluates whether an actor in a tenant context is authorized to execute the tool.
        Raises specific AuthorizationError, TenantAccessError, or PolicyDeniedError upon failure.
        """
        # 1. Tenant Boundary Check
        if tool.tenant_scope is not None and tool.tenant_scope != tenant_id:
            raise TenantAccessError(
                f"Tenant '{tenant_id}' is not authorized to invoke tool '{tool.tool_id}' scoped to tenant '{tool.tenant_scope}'",
                details={"requesting_tenant": tenant_id, "tool_tenant_scope": tool.tenant_scope}
            )

        # 2. Permission Check
        if tool.required_permissions:
            missing_perms = [p for p in tool.required_permissions if p not in actor_permissions and "*" not in actor_permissions]
            if missing_perms:
                raise AuthorizationError(
                    f"Actor '{actor_id}' lacks required permissions {missing_perms} for tool '{tool.tool_id}'",
                    details={"missing_permissions": missing_perms, "actor_permissions": actor_permissions}
                )

        # 3. Trust Level Check
        # HIGH_IMPACT tools cannot be executed by UNTRUSTED actors
        if tool.trust_level == TrustLevel.HIGH_IMPACT and actor_trust_level == TrustLevel.UNTRUSTED:
            raise AuthorizationError(
                f"Untrusted actor '{actor_id}' cannot invoke HIGH_IMPACT tool '{tool.tool_id}'",
                details={"actor_trust": actor_trust_level.value, "tool_trust": tool.trust_level.value}
            )

        # 4. Deterministic Policy Engine Gate for HIGH_IMPACT operations
        if tool.trust_level == TrustLevel.HIGH_IMPACT:
            policy_ctx = PolicyContext(
                verdict="CONTROLLED_OPERATION",
                risk_score=50.0,
                source="AGENT_TOOL_CALL",
                target=tool.tool_id,
                metadata={"actor_id": actor_id, "tenant_id": tenant_id, "args": tool_args or {}}
            )
            decision = self.policy_engine.evaluate_policy(policy_ctx)
            if decision.action in {PolicyDecisionAction.BLOCK, PolicyDecisionAction.QUARANTINE}:
                raise PolicyDeniedError(
                    f"Policy Engine rejected invocation of tool '{tool.tool_id}': {decision.explanation}",
                    details={"decision": decision.to_dict()}
                )

        return True
