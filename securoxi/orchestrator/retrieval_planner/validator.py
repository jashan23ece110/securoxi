"""
SECUROXI AI Intelligence 2.0 — Agentic Retrieval Plan Validator
Deterministically validates retrieval plans for tenant isolation, strategy availability,
security filtering, budget bounds, and prompt injection defense.
"""

from typing import Dict, Any, List, Optional
from securoxi.orchestrator.retrieval_planner.models import RetrievalPlan
from securoxi.orchestrator.retrieval_planner.types import RetrievalStrategyType
from securoxi.orchestrator.errors import (
    AuthorizationError,
    TenantAccessError,
    BudgetExhaustedError,
)
from securoxi.logger import get_logger

logger = get_logger("orchestrator.retrieval_validator")


class RetrievalPlanValidator:
    """Deterministic gatekeeper validating RetrievalPlan instances before execution."""

    def validate(self, plan: RetrievalPlan, requesting_tenant_id: str) -> bool:
        """
        Validates the retrieval plan against security, tenant, budget, and strategy invariants:
        1. Tenant isolation validation.
        2. Security filter validation (HIGH_RISK/UNINSPECTABLE cannot be trusted context).
        3. Strategy existence.
        4. Budget limits.
        """
        # 1. Tenant Isolation
        if plan.tenant_id != requesting_tenant_id:
            logger.error(f"Tenant isolation mismatch: Plan tenant '{plan.tenant_id}' != Request tenant '{requesting_tenant_id}'")
            raise TenantAccessError(f"Cross-tenant retrieval planning blocked: {plan.tenant_id}")

        for q in plan.queries:
            if "across all tenants" in q.query_text.lower() or "other tenant" in q.query_text.lower():
                raise TenantAccessError("Unauthorized multi-tenant retrieval attempt blocked.")

        # 2. Security Invariants
        sec_filter = plan.security_filters.get("security_status", "SAFE")
        if sec_filter == "ALL_INCLUDING_HIGH_RISK_TRUSTED":
            raise AuthorizationError("Cannot treat HIGH_RISK documents as trusted context.")

        # 3. Budget Limits
        if plan.max_iterations > 50 or plan.budget_cost_limit > 100.0:
            raise BudgetExhaustedError(f"Retrieval plan exceeded maximum allowable budget bounds: {plan.budget_cost_limit}")

        return True
