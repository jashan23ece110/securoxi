"""
SECUROXI AI Phase 3 Stage 4 — Enterprise Security Policy & Decision Engine
Evaluates deterministic, prioritized, and auditable enterprise security policies.
Supports risk thresholds, source constraints, document rules, ATS rules, and fail-safe fallback protection.
"""

import time
import uuid
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from securoxi.logger import get_logger


class PolicyDecisionAction(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"
    QUARANTINE = "QUARANTINE"
    ALERT = "ALERT"


@dataclass
class PolicyContext:
    """Security context presented to the Policy Engine for evaluation."""
    verdict: str  # "SAFE", "SUSPICIOUS", "HIGH_RISK"
    risk_score: float
    source: str  # "RESUME_UPLOAD", "ATS_WEBHOOK", "AGENT_TOOL_CALL"
    target: str  # "CANDIDATE_SCREENING", "ATS_DATABASE"
    findings_count: int = 0
    threat_types: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "risk_score": self.risk_score,
            "source": self.source,
            "target": self.target,
            "findings_count": self.findings_count,
            "threat_types": self.threat_types,
            "metadata": self.metadata
        }


@dataclass
class PolicyRule:
    """Declarative security policy rule."""
    rule_id: str
    priority: int  # Higher number = higher evaluation priority (e.g. 100 > 10)
    name: str
    description: str
    action: PolicyDecisionAction
    condition: Callable[[PolicyContext], bool]
    version: str = "1.0.0"

    def matches(self, ctx: PolicyContext) -> bool:
        return self.condition(ctx)



@dataclass
class EnterprisePolicyDecision:
    """Auditable policy decision result."""
    decision_id: str = field(default_factory=lambda: f"POL-{uuid.uuid4().hex[:8]}")
    action: PolicyDecisionAction = PolicyDecisionAction.QUARANTINE
    rule_id: str = "DEFAULT_FALLSAFE"
    rule_priority: int = 0
    explanation: str = "Default fail-safe policy applied."
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    evaluated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action": self.action.value,
            "rule_id": self.rule_id,
            "rule_priority": self.rule_priority,
            "explanation": self.explanation,
            "context_snapshot": self.context_snapshot,
            "version": self.version,
            "evaluated_at": self.evaluated_at
        }


class SecuroxiPolicyEngine:
    """
    Deterministic & Auditable Enterprise Security Policy Engine.
    Evaluates registered policy rules in strict priority order.
    """

    def __init__(self):
        self.logger = get_logger("securoxi.brain.policy")
        self.rules: List[PolicyRule] = []
        self._load_default_enterprise_rules()

    def register_rule(self, rule: PolicyRule):
        """Register a new policy rule and sort rules by priority descending."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        self.logger.info(f"Registered policy rule '{rule.rule_id}' (Priority {rule.priority})")

    def evaluate_policy(self, ctx: PolicyContext) -> EnterprisePolicyDecision:
        """
        Evaluates context against registered rules in priority order.
        Returns the highest-priority matching rule decision.
        Fail-safe fallback to QUARANTINE if no rules match or evaluation fails.
        """
        try:
            for rule in self.rules:
                if rule.matches(ctx):
                    self.logger.info(f"Policy Rule FIRED [{rule.rule_id}] -> {rule.action.value}")
                    return EnterprisePolicyDecision(
                        action=rule.action,
                        rule_id=rule.rule_id,
                        rule_priority=rule.priority,
                        explanation=f"Rule '{rule.name}' matched context: {rule.description}",
                        context_snapshot=ctx.to_dict(),
                        version=rule.version
                    )

            # Fallback if no rules match
            self.logger.warning("No policy rules matched context. Applying default fail-safe QUARANTINE.")
            return EnterprisePolicyDecision(
                action=PolicyDecisionAction.QUARANTINE,
                rule_id="DEFAULT_FALLBACK_NO_MATCH",
                rule_priority=0,
                explanation="No explicit rule matched context. Defaulting to fail-safe QUARANTINE.",
                context_snapshot=ctx.to_dict()
            )

        except Exception as err:
            self.logger.error(f"Policy Engine evaluation exception: {err}. Applying Emergency FAIL-SAFE BLOCK.")
            return EnterprisePolicyDecision(
                action=PolicyDecisionAction.BLOCK,
                rule_id="EMERGENCY_FAILSAFE_ERROR",
                rule_priority=999,
                explanation=f"Policy engine encountered evaluation exception ({err}). Fail-safe BLOCK enforced.",
                context_snapshot=ctx.to_dict()
            )

    def _load_default_enterprise_rules(self):
        """Loads default enterprise security policies."""
        # Priority 100: High Risk ATS Document -> BLOCK
        self.register_rule(PolicyRule(
            rule_id="RULE-100-HIGH-RISK-BLOCK",
            priority=100,
            name="Block High Risk ATS Documents",
            description="High risk verdict documents targeted at ATS screening must be BLOCKED.",
            action=PolicyDecisionAction.BLOCK,
            condition=lambda c: c.verdict == "HIGH_RISK" or c.risk_score >= 80.0
        ))

        # Priority 90: Visual Deception / Prompt Injection -> QUARANTINE
        self.register_rule(PolicyRule(
            rule_id="RULE-090-PROMPT-INJECTION-QUARANTINE",
            priority=90,
            name="Quarantine Active Injections",
            description="Active prompt injection or visual deception findings require immediate QUARANTINE.",
            action=PolicyDecisionAction.QUARANTINE,
            condition=lambda c: any(t in ["PROMPT_INJECTION", "VISUAL_DECEPTION"] for t in c.threat_types)
        ))

        # Priority 50: Suspicious Document -> REVIEW
        self.register_rule(PolicyRule(
            rule_id="RULE-050-SUSPICIOUS-HUMAN-REVIEW",
            priority=50,
            name="Require Review for Suspicious Documents",
            description="Suspicious documents require human security review.",
            action=PolicyDecisionAction.REVIEW,
            condition=lambda c: c.verdict == "SUSPICIOUS" or c.risk_score >= 30.0
        ))

        # Priority 10: Safe Document -> ALLOW
        self.register_rule(PolicyRule(
            rule_id="RULE-010-SAFE-ALLOW",
            priority=10,
            name="Allow Safe Documents",
            description="Safe documents passing all security checks are ALLOWED.",
            action=PolicyDecisionAction.ALLOW,
            condition=lambda c: c.verdict == "SAFE" and c.risk_score < 30.0
        ))
