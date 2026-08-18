"""
SECUROXI AI Intelligence 2.0 — Planning Types & Enums
Defines intent taxonomies, condition types, constraint priority levels, and replanning triggers.
"""

from enum import Enum


class TaskIntent(str, Enum):
    """Normalized intent classification for user tasks."""
    DOCUMENT_SCAN = "DOCUMENT_SCAN"
    BULK_SCAN = "BULK_SCAN"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    QUESTION_ANSWERING = "QUESTION_ANSWERING"
    DOCUMENT_COMPARISON = "DOCUMENT_COMPARISON"
    CANDIDATE_SCREENING = "CANDIDATE_SCREENING"
    JD_MATCHING = "JD_MATCHING"
    ATS_OPERATION = "ATS_OPERATION"
    SECURITY_INVESTIGATION = "SECURITY_INVESTIGATION"
    INCIDENT_INVESTIGATION = "INCIDENT_INVESTIGATION"
    REPORT_GENERATION = "REPORT_GENERATION"
    MIXED_WORKFLOW = "MIXED_WORKFLOW"


class ConditionType(str, Enum):
    """Categorization of user and system requirements."""
    MANDATORY = "MANDATORY"              # Hard requirement (e.g. 5+ yrs experience, production K8s)
    PREFERRED = "PREFERRED"              # Soft preference (e.g. security certs, Python)
    EXCLUSION = "EXCLUSION"              # Explicit removal criteria (e.g. exclude HIGH_RISK)
    FILTER = "FILTER"                    # Scoping filter (e.g. only folder X, only US candidates)
    RANKING_SIGNAL = "RANKING_SIGNAL"    # Weighting factor for ranking (e.g. fit score + recency)


class ConstraintPriorityLevel(int, Enum):
    """Deterministic precedence hierarchy for resolving conflicting constraints."""
    SYSTEM_SECURITY = 1      # Level 1: Deterministic Security Engine & Policy Invariants (Highest)
    TENANT_AUTHORIZATION = 2 # Level 2: Tenant boundary and actor permissions
    USER_EXCLUSIONS = 3      # Level 3: Explicit user exclusions (e.g. "Do not include X")
    USER_MANDATORY = 4       # Level 4: Explicit mandatory requirements (e.g. "Must have 5+ yrs")
    POLICY_GATE = 5          # Level 5: Enterprise policy rules
    USER_PREFERENCES = 6     # Level 6: Soft preferences (e.g. "Prefer certs")
    RANKING_HEURISTICS = 7   # Level 7: Scoring weights & heuristics (Lowest)


class PlanConfidence(str, Enum):
    """Confidence assessment for the generated execution plan."""
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"          # All inputs and dependencies resolved
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"  # Minor ambiguity with safe fallback or actionable question
    LOW_CONFIDENCE = "LOW_CONFIDENCE"            # Crucial missing inputs or contradictory constraints


class ReplanReason(str, Enum):
    """Authoritative triggers for initiating adaptive replanning."""
    INPUT_CHANGED = "INPUT_CHANGED"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    OCR_FAILED = "OCR_FAILED"
    WEAK_RETRIEVAL = "WEAK_RETRIEVAL"
    BRANCH_FAILED = "BRANCH_FAILED"
    SECURITY_FINDING_ESCALATED = "SECURITY_FINDING_ESCALATED"
    BUDGET_CONSTRAINED = "BUDGET_CONSTRAINED"
    USER_OVERRIDE = "USER_OVERRIDE"


class PlanningStatus(str, Enum):
    """Lifecycle status of a generated plan."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
