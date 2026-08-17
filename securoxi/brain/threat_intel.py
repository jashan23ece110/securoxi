"""
SECUROXI AI Phase 3 Stage 2 — Threat Intelligence & Attack Graph Model
Defines Threat Intelligence taxonomies, tactics, techniques, attack chain relationships, and graph models.
"""

import time
import uuid
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


class ThreatCategory(str, Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    INSTRUCTION_HIJACKING = "INSTRUCTION_HIJACKING"
    RANKING_MANIPULATION = "RANKING_MANIPULATION"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    TOOL_MANIPULATION = "TOOL_MANIPULATION"
    OBFUSCATION = "OBFUSCATION"
    HIDDEN_CONTENT = "HIDDEN_CONTENT"
    AGENT_MANIPULATION = "AGENT_MANIPULATION"


class AttackTactic(str, Enum):
    INITIAL_ACCESS = "INITIAL_ACCESS"
    EXECUTION = "EXECUTION"
    DEFENSE_EVASION = "DEFENSE_EVASION"
    PERSISTENCE = "PERSISTENCE"
    EXFILTRATION = "EXFILTRATION"
    IMPACT = "IMPACT"


@dataclass
class AttackTechnique:
    """Represents an attack technique within the SECUROXI Threat Intel model."""
    technique_id: str
    name: str
    category: ThreatCategory
    tactic: AttackTactic
    description: str
    severity_score: float = 8.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technique_id": self.technique_id,
            "name": self.name,
            "category": self.category.value,
            "tactic": self.tactic.value,
            "description": self.description,
            "severity_score": self.severity_score
        }


# Standard SECUROXI Attack Technique Catalog
SECUROXI_TECHNIQUES: Dict[str, AttackTechnique] = {
    "T-1001": AttackTechnique(
        technique_id="T-1001",
        name="Hidden White Text Injection",
        category=ThreatCategory.HIDDEN_CONTENT,
        tactic=AttackTactic.DEFENSE_EVASION,
        description="Text rendered in white font (#FFFFFF) over white background to conceal instructions from human review."
    ),
    "T-1002": AttackTechnique(
        technique_id="T-1002",
        name="Micro Font Size Injection",
        category=ThreatCategory.HIDDEN_CONTENT,
        tactic=AttackTactic.DEFENSE_EVASION,
        description="Text rendered with font size < 2.0pt to hide instructions from human eyes."
    ),
    "T-1003": AttackTechnique(
        technique_id="T-1003",
        name="Direct System Prompt Override",
        category=ThreatCategory.PROMPT_INJECTION,
        tactic=AttackTactic.EXECUTION,
        description="Instructing LLM to ignore system instructions and execute attacker commands."
    ),
    "T-1004": AttackTechnique(
        technique_id="T-1004",
        name="ATS Candidate Ranking Manipulation",
        category=ThreatCategory.RANKING_MANIPULATION,
        tactic=AttackTactic.IMPACT,
        description="Commands forcing AI screening algorithms to grant score 100/100 or 'STRONG_MATCH'."
    )
}


@dataclass
class ThreatIntelRecord:
    """Threat intelligence record tracking attack technique occurrences and recurrence across documents."""
    record_id: str = field(default_factory=lambda: f"TIR-{uuid.uuid4().hex[:8]}")
    technique: AttackTechnique = field(default_factory=lambda: SECUROXI_TECHNIQUES["T-1001"])
    confidence: float = 0.95
    source_artifact: str = "UNKNOWN"
    affected_system: str = "RESUME_SCREENING_PIPELINE"
    recurrence_count: int = 1
    evidence_provenance: List[str] = field(default_factory=list)
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "technique": self.technique.to_dict(),
            "confidence": self.confidence,
            "source_artifact": self.source_artifact,
            "affected_system": self.affected_system,
            "recurrence_count": self.recurrence_count,
            "evidence_provenance": self.evidence_provenance,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen
        }


@dataclass
class ThreatGraphModel:
    """Rich threat relationship graph mapping Actor -> Artifact -> Signal -> Technique -> Target -> Impact."""
    graph_id: str = field(default_factory=lambda: f"TGM-{uuid.uuid4().hex[:8]}")
    entities: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)

    def add_entity(self, entity_id: str, name: str, entity_type: str):
        self.entities.append({"id": entity_id, "name": name, "type": entity_type})

    def add_relationship(self, source_id: str, target_id: str, rel_type: str):
        self.relationships.append({"source": source_id, "target": target_id, "relationship": rel_type})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "entities": self.entities,
            "relationships": self.relationships
        }
