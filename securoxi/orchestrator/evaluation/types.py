"""
SECUROXI AI Intelligence 2.0 — Continuous Evaluation & Quality Gate Enums & Types
"""

from enum import Enum


class EvaluationLevel(str, Enum):
    LEVEL_1_FAST = "LEVEL_1_FAST"          # Local/PR fast unit & contract checks
    LEVEL_2_STANDARD = "LEVEL_2_STANDARD"  # Integration, security, RAG, and hiring suites
    LEVEL_3_DEEP = "LEVEL_3_DEEP"          # Complete red-team corpus, stress, & performance
    LEVEL_4_CANARY = "LEVEL_4_CANARY"      # Shadow & live canary monitoring


class GateStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class GateType(str, Enum):
    SECURITY_GATE = "SECURITY_GATE"        # Hard gate: 0 prompt injection / tenant bypasses
    GROUNDING_GATE = "GROUNDING_GATE"      # Citation correctness and zero unsupported claims
    HIRING_GATE = "HIRING_GATE"            # Strict mandatory criteria satisfaction and ranking
    PERFORMANCE_GATE = "PERFORMANCE_GATE"  # Latency P95 and budget adherence
    CONTRACT_GATE = "CONTRACT_GATE"        # Schema and API invariant validation
