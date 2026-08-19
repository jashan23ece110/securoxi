"""
SECUROXI AI Intelligence 2.0 — Enterprise Customer Configuration & Policy Types
"""

from enum import Enum


class ConfigCategory(str, Enum):
    SECURITY = "SECURITY"
    HIRING = "HIRING"
    RETRIEVAL = "RETRIEVAL"
    TASKS = "TASKS"
    AI_INTELLIGENCE = "AI_INTELLIGENCE"
    GOVERNANCE = "GOVERNANCE"
    INTEGRATIONS = "INTEGRATIONS"


class ConfigValueType(str, Enum):
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"
    LIST = "LIST"


class AIBehaviorProfile(str, Enum):
    FAST = "FAST"
    BALANCED = "BALANCED"
    DEEP = "DEEP"
