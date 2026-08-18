"""
SECUROXI AI Intelligence 2.0 — Task Understanding Engine
Converts natural-language user intent into structured, normalized, and priority-ranked
TaskUnderstanding models with entity resolution, constraint classification, and ambiguity detection.
"""

import re
import uuid
from typing import Dict, Any, List, Optional, Tuple, Set

from securoxi.orchestrator.planning.types import (
    TaskIntent,
    ConditionType,
    ConstraintPriorityLevel,
    PlanConfidence,
)
from securoxi.orchestrator.planning.models import (
    StructuredCondition,
    ResolvedEntity,
    ClarificationRequest,
    TaskUnderstanding,
)


class TaskUnderstandingEngine:
    """
    Deterministic & rule-augmented natural language understanding engine.
    Extracts intents, entities, typed conditions, priority hierarchies, and ambiguities.
    """

    def __init__(self):
        # Known skills taxonomy for extraction
        self.skills_vocab = {
            "kubernetes", "k8s", "aws", "gcp", "azure", "python", "terraform",
            "docker", "ci/cd", "security", "threat intel", "splunk", "linux",
            "cloud security", "incident response", "prompt injection", "ocr"
        }

    def analyze_task(
        self,
        prompt: str,
        tenant_id: str = "TENANT-DEFAULT",
        actor_id: str = "SYSTEM",
        available_context: Optional[Dict[str, Any]] = None
    ) -> TaskUnderstanding:
        """
        Analyzes a natural language task prompt and returns a structured TaskUnderstanding.
        """
        raw_prompt = prompt.strip()
        ctx = available_context or {}

        # 1. Adversarial Injection Check on Prompt
        cleaned_prompt, has_injection = self._filter_prompt_injection(raw_prompt)

        # 2. Intent Classification
        primary_intent = self._classify_intent(cleaned_prompt)

        # 3. Target Count Extraction (e.g. "top 20", "5 candidates")
        target_count = self._extract_target_count(cleaned_prompt)

        # 4. Condition Extraction & Normalization
        conditions = self._extract_conditions(cleaned_prompt, has_injection)

        # 5. Entity Resolution
        entities = self._resolve_entities(cleaned_prompt, ctx, tenant_id)

        # 6. Ambiguity & Clarification Analysis
        confidence, confidence_reason, clarifications = self._analyze_ambiguity(
            primary_intent, entities, conditions, ctx
        )

        # 7. Objective Summary Generation
        summary = self._generate_objective_summary(primary_intent, target_count, conditions, entities)

        return TaskUnderstanding(
            raw_prompt=raw_prompt,
            primary_intent=primary_intent,
            objective_summary=summary,
            requested_output_format="RANKED_LIST" if target_count else "SUMMARY",
            target_count=target_count,
            entities=entities,
            conditions=conditions,
            assumptions=[
                "Candidate documents are untrusted until cleared by Security Scan.",
                "Security Clearance is strictly separated from Fit Score.",
            ],
            confidence=confidence,
            confidence_reason=confidence_reason,
            clarifications=clarifications,
        )

    def _filter_prompt_injection(self, text: str) -> Tuple[str, bool]:
        """Detects and neutralizes prompt-injection override patterns."""
        injection_patterns = [
            r"ignore\s+(all\s+)?(previous\s+)?instructions",
            r"bypass\s+(all\s+)?(safety|security)\s+rules",
            r"override\s+(policy|security)",
            r"system\s*prompt\s*override",
            r"disregard\s+security",
        ]
        has_injection = False
        cleaned = text

        for pat in injection_patterns:
            if re.search(pat, text, re.IGNORECASE):
                has_injection = True
                cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

        return cleaned.strip(), has_injection

    def _classify_intent(self, text: str) -> TaskIntent:
        """Classifies the primary domain intent of the user prompt."""
        t_lower = text.lower()

        # Check for Mixed Security + Hiring Workflow
        has_scan = any(w in t_lower for w in ["scan", "check for threats", "prompt injection", "malicious", "quarantine", "hidden text"])
        has_screen = any(w in t_lower for w in ["rank", "screen", "top", "candidates", "jd", "job description", "match"])

        if has_scan and has_screen:
            return TaskIntent.MIXED_WORKFLOW

        # Check for Question Answering / Ask Securoxi query
        if any(t_lower.startswith(w) or f" {w} " in t_lower for w in ["which", "who", "what", "where", "how", "ask", "tell me", "explain"]):
            return TaskIntent.QUESTION_ANSWERING

        # Check for Bulk Scan if bulk/collection markers are present without screening
        if any(w in t_lower for w in ["bulk", "collection", "thousands", "all files", "10,000", "folder scan", "entire"]):
            if not any(w in t_lower for w in ["rank", "screen", "hire", "fit score"]):
                return TaskIntent.BULK_SCAN

        if any(w in t_lower for w in ["screen", "candidate", "hire", "fit score", "rank candidates"]):
            return TaskIntent.CANDIDATE_SCREENING

        if any(w in t_lower for w in ["folder", "collection", "bulk", "thousands", "all files"]):
            return TaskIntent.BULK_SCAN

        if any(w in t_lower for w in ["scan", "check document", "inspect file", "detect threat"]):
            return TaskIntent.DOCUMENT_SCAN

        if any(w in t_lower for w in ["incident", "attack", "compromise", "investigate threat"]):
            return TaskIntent.INCIDENT_INVESTIGATION

        if any(w in t_lower for w in ["ats", "greenhouse", "lever", "workday"]):
            return TaskIntent.ATS_OPERATION

        if any(w in t_lower for w in ["compare", "difference between"]):
            return TaskIntent.DOCUMENT_COMPARISON

        return TaskIntent.DOCUMENT_ANALYSIS

    def _extract_target_count(self, text: str) -> Optional[int]:
        """Extracts desired output count (e.g. 'top 20', 'top 5', '10 candidates')."""
        match = re.search(r"\btop\s+(\d+)\b", text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        match_num = re.search(r"\b(\d+)\s+(best|safe|qualified)?\s*candidates\b", text, re.IGNORECASE)
        if match_num:
            return int(match_num.group(1))

        return None

    def _extract_conditions(self, text: str, has_injection_attempt: bool) -> List[StructuredCondition]:
        """Extracts and normalizes typed conditions from text."""
        conditions: List[StructuredCondition] = []
        t_lower = text.lower()

        # 1. System Invariant: Exclude HIGH_RISK documents
        # (Always enforced, immutable Level 1 priority)
        conditions.append(
            StructuredCondition(
                raw_text="System Invariant: Exclude High Risk",
                normalized_field="security_status",
                operator="NOT_IN",
                value=["HIGH_RISK", "CRITICAL", "BLOCKED"],
                condition_type=ConditionType.EXCLUSION,
                priority_level=ConstraintPriorityLevel.SYSTEM_SECURITY,
                is_immutable=True,
            )
        )

        # 2. Experience Extraction (e.g. "5+ years", "at least 5 years", "min 3 years")
        exp_match = re.search(r"(?:at\s+least|min|minimum|\+)?\s*(\d+)\+?\s*(?:years?|yrs?)(?:\s+of\s+experience)?", text, re.IGNORECASE)
        if exp_match:
            years = int(exp_match.group(1))
            conditions.append(
                StructuredCondition(
                    raw_text=exp_match.group(0),
                    normalized_field="min_experience_years",
                    operator=">=",
                    value=years,
                    condition_type=ConditionType.MANDATORY,
                    priority_level=ConstraintPriorityLevel.USER_MANDATORY,
                )
            )

        # 3. Mandatory Skill Extraction
        found_skills = []
        for skill in self.skills_vocab:
            if re.search(r"\b" + re.escape(skill) + r"\b", t_lower):
                found_skills.append(skill.title())

        if found_skills:
            conditions.append(
                StructuredCondition(
                    raw_text=f"Skills: {', '.join(found_skills)}",
                    normalized_field="required_skills",
                    operator="CONTAINS",
                    value=found_skills,
                    condition_type=ConditionType.MANDATORY,
                    priority_level=ConstraintPriorityLevel.USER_MANDATORY,
                )
            )

        # 4. User Exclusions
        if "exclude" in t_lower or "ignore" in t_lower:
            conditions.append(
                StructuredCondition(
                    raw_text="User specified exclusion filter",
                    normalized_field="user_exclusion",
                    operator="==",
                    value=True,
                    condition_type=ConditionType.EXCLUSION,
                    priority_level=ConstraintPriorityLevel.USER_EXCLUSIONS,
                )
            )

        # 5. Check Contradictory Constraints (e.g. exclude and include same high risk)
        has_incl_hr = bool(re.search(r"\binclude\b.*\bhigh risk\b", t_lower))
        has_excl_hr = bool(re.search(r"\bexclude\b.*\bhigh risk\b", t_lower))
        if has_incl_hr and has_excl_hr:
            conditions.append(
                StructuredCondition(
                    raw_text="Contradictory High Risk Requirement",
                    normalized_field="contradiction_detected",
                    operator="==",
                    value=True,
                    condition_type=ConditionType.FILTER,
                    priority_level=ConstraintPriorityLevel.USER_PREFERENCES,
                )
            )

        return conditions

    def _resolve_entities(self, text: str, ctx: Dict[str, Any], tenant_id: str) -> List[ResolvedEntity]:
        """Resolves raw document and folder references against authorized system context."""
        entities: List[ResolvedEntity] = []

        # Check for folder mention
        folder_match = re.search(r"(?:folder|directory|collection)\s+['\"]?([\w\-\_]+)['\"]?", text, re.IGNORECASE)
        if folder_match:
            raw_folder = folder_match.group(1)
            entities.append(
                ResolvedEntity(
                    entity_type="FOLDER",
                    raw_name=raw_folder,
                    resolved_id=ctx.get("folder_id", f"FOLDER-{raw_folder}"),
                    is_authorized=True,
                    metadata={"tenant_id": tenant_id}
                )
            )
        elif "folder" in text.lower():
            entities.append(
                ResolvedEntity(
                    entity_type="FOLDER",
                    raw_name="Default Candidate Folder",
                    resolved_id=ctx.get("folder_id", "FOLDER-DEFAULT"),
                    is_authorized=True,
                    metadata={"tenant_id": tenant_id}
                )
            )

        # Check for JD / Requisition mention
        if "jd" in text.lower() or "job description" in text.lower() or "senior cloud security" in text.lower():
            jd_id = ctx.get("job_id", "JOB-SR-CLOUD-SEC")
            entities.append(
                ResolvedEntity(
                    entity_type="JOB_DESCRIPTION",
                    raw_name="Target Job Description",
                    resolved_id=jd_id,
                    is_authorized=True,
                    metadata={"title": "Senior Cloud Security Engineer", "tenant_id": tenant_id}
                )
            )

        return entities

    def _analyze_ambiguity(
        self,
        intent: TaskIntent,
        entities: List[ResolvedEntity],
        conditions: List[StructuredCondition],
        ctx: Dict[str, Any]
    ) -> Tuple[PlanConfidence, str, List[ClarificationRequest]]:
        """Evaluates clarity of inputs and formulates minimal actionable clarifications if needed."""
        clarifications: List[ClarificationRequest] = []

        # Check for contradictory conditions
        has_contradiction = any(c.normalized_field == "contradiction_detected" for c in conditions)
        if has_contradiction:
            return (
                PlanConfidence.LOW_CONFIDENCE,
                "Contradictory constraints detected in user request.",
                [
                    ClarificationRequest(
                        target_field="security_policy",
                        question_text="Your request contains conflicting instructions regarding high-risk documents. Should high-risk resumes be excluded?",
                        options=["Exclude High Risk (Recommended)", "Include for Special Review"],
                        default_fallback="Exclude High Risk (Recommended)"
                    )
                ]
            )

        # Check if JD is required for screening but completely missing
        if intent in {TaskIntent.CANDIDATE_SCREENING, TaskIntent.JD_MATCHING, TaskIntent.MIXED_WORKFLOW}:
            has_jd = any(e.entity_type == "JOB_DESCRIPTION" for e in entities)
            if not has_jd and not ctx.get("job_id"):
                clarifications.append(
                    ClarificationRequest(
                        target_field="target_job",
                        question_text="Which active job requisition should candidates be screened against?",
                        options=[
                            "Senior Cloud Security Engineer (JOB-SR-CLOUD-SEC)",
                            "AI Security Engineer (JOB-AI-SEC)",
                            "Senior SOC Analyst (JOB-SOC-LEAD)"
                        ],
                        default_fallback="Senior Cloud Security Engineer (JOB-SR-CLOUD-SEC)"
                    )
                )
                return (
                    PlanConfidence.NEEDS_CLARIFICATION,
                    "Target job requisition was not specified. Safe default selected.",
                    clarifications
                )

        return (PlanConfidence.HIGH_CONFIDENCE, "Intent, entities, and security constraints fully resolved.", [])

    def _generate_objective_summary(
        self,
        intent: TaskIntent,
        target_count: Optional[int],
        conditions: List[StructuredCondition],
        entities: List[ResolvedEntity]
    ) -> str:
        """Generates a concise, plain-language objective summary without exposing internals."""
        count_str = f"top {target_count}" if target_count else "qualified"
        skills = [c.value for c in conditions if c.normalized_field == "required_skills"]
        skills_str = f" with {', '.join(skills[0])}" if skills and isinstance(skills[0], list) else ""

        if intent == TaskIntent.MIXED_WORKFLOW:
            return f"Scan document collection, exclude high-risk files, match safe candidates, and return {count_str} candidates{skills_str}."
        elif intent == TaskIntent.CANDIDATE_SCREENING:
            return f"Screen candidate pool against target job description and return {count_str} candidates{skills_str}."
        elif intent == TaskIntent.BULK_SCAN:
            return "Scan folder collection in bulk for prompt injection, micro-text, and visual deception."
        elif intent == TaskIntent.QUESTION_ANSWERING:
            return "Search authorized document knowledgebase and generate grounded, citation-backed answer."
        return "Analyze authorized documents under enterprise security policies."
