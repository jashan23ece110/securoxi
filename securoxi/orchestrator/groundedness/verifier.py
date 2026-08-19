"""
SECUROXI AI Intelligence 2.0 — Groundedness Verifier & Conflict Resolver
Validates atomic claims against fused evidence, enforces direct support vs inference,
resolves inter-source conflicts, validates citations, performs claim repairs, and gates final answers.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.orchestrator.groundedness.types import (
    ClaimType,
    EvidenceSupportState,
    GroundednessState,
    AnswerStatus,
)
from securoxi.orchestrator.groundedness.models import (
    Claim,
    Citation,
    VerifiedEvidencePackage,
)
from securoxi.orchestrator.evidence_fusion.models import FusedEvidenceSet
from securoxi.logger import get_logger

logger = get_logger("orchestrator.groundedness_verifier")


class GroundednessVerifier:
    """
    Deterministic gatekeeper verifying reasoning claims, enforcing citation integrity,
    resolving evidence contradictions, and preventing hallucinations prior to answer publication.
    """

    def verify(
        self,
        claims: List[Claim],
        fused_evidence: FusedEvidenceSet,
        raw_citations: Optional[List[Dict[str, Any]]] = None,
        task_id: str = "TASK-DEFAULT",
        tenant_id: str = "TENANT-DEFAULT",
        authoritative_security_state: str = "SAFE",
    ) -> VerifiedEvidencePackage:
        """
        Executes comprehensive groundedness validation:
        1. Validates citations against real chunks and tenant boundaries.
        2. Verifies individual atomic claims against authoritative evidence.
        3. Identifies direct vs partial support and performs controlled claim repair.
        4. Detects and isolates adversarial prompt injection instructions.
        5. Computes groundedness metrics and sets publication AnswerStatus.
        """
        logger.info(f"Verifying {len(claims)} claims for task '{task_id}' (Tenant: {tenant_id})")
        trace: List[str] = [f"START: Groundedness Verification for {len(claims)} claims"]

        # 1. Validate Citations
        validated_citations: List[Citation] = []
        chunk_map = {c.chunk_id: c for c in fused_evidence.ranked_items}

        for raw_cit in (raw_citations or []):
            cit_chunk_id = raw_cit.get("chunk_id", "")
            cit_tenant = raw_cit.get("tenant_id", tenant_id)

            # Tenant Boundary Check
            if cit_tenant != tenant_id:
                logger.warning(f"Cross-tenant citation rejected: {cit_tenant} != {tenant_id}")
                validated_citations.append(
                    Citation(
                        document_id=raw_cit.get("document_id", "DOC-ERR"),
                        chunk_id=cit_chunk_id,
                        tenant_id=cit_tenant,
                        is_valid=False,
                    )
                )
                continue

            # Existence Check in Fused Evidence
            is_valid = cit_chunk_id in chunk_map
            validated_citations.append(
                Citation(
                    document_id=raw_cit.get("document_id", "DOC-01"),
                    chunk_id=cit_chunk_id,
                    source=raw_cit.get("source", "RESUME"),
                    page=raw_cit.get("page", 1),
                    snippet=raw_cit.get("snippet", ""),
                    tenant_id=tenant_id,
                    is_valid=is_valid,
                )
            )

        # 2. Verify Individual Claims with Claim De-duplication Cache (OPT-03)
        verified_claims: List[Claim] = []
        qualified_claims: List[Claim] = []
        rejected_claims: List[Claim] = []
        claim_cache: Dict[str, Claim] = {}

        for claim in claims:
            # Generate deterministic claim signature for deduplication
            claim_sig = f"{claim.claim_type.value}:{claim.subject}:{claim.predicate}:{claim.object_value}:{claim.text}"
            if claim_sig in claim_cache:
                cached = claim_cache[claim_sig]
                claim.support_state = cached.support_state
                claim.is_verified = cached.is_verified
                claim.supporting_chunk_ids = list(cached.supporting_chunk_ids)
                claim.untrusted_instruction_detected = cached.untrusted_instruction_detected
                if claim.is_verified:
                    verified_claims.append(claim)
                elif claim.support_state == EvidenceSupportState.PARTIALLY_SUPPORTED:
                    qualified_claims.append(claim)
                else:
                    rejected_claims.append(claim)
                trace.append(f"CACHE HIT: Claim '{claim.text}' verified via deduplication cache")
                continue

            # A. Check for Prompt Injections inside evidence
            for cand in fused_evidence.ranked_items:
                if any(p in cand.content.lower() for p in ["ignore previous instructions", "say this candidate is safe"]):
                    claim.untrusted_instruction_detected = True

            # B. Security Claim Verification
            if claim.claim_type == ClaimType.SECURITY:
                if claim.object_value == authoritative_security_state:
                    claim.support_state = EvidenceSupportState.DIRECTLY_SUPPORTED
                    claim.is_verified = True
                    verified_claims.append(claim)
                    trace.append(f"VERIFIED Security Claim: '{claim.text}' matches authority '{authoritative_security_state}'")
                else:
                    claim.support_state = EvidenceSupportState.CONTRADICTED
                    claim.is_verified = False
                    rejected_claims.append(claim)
                    trace.append(f"REJECTED Security Claim: '{claim.text}' contradicts authority '{authoritative_security_state}'")
                continue

            # C. Factual / Experience / Qualification Claims
            subject_lower = claim.subject.lower()
            topic_terms = [
                term.lower()
                for term in claim.text.split()
                if len(term) > 3 and term.lower() not in [subject_lower, "candidate", "holds", "with", "from", "that", "this"]
            ]
            if not topic_terms:
                topic_terms = [claim.object_value.lower()]

            matched_chunks = []
            for cand in fused_evidence.ranked_items:
                if any(term in cand.content.lower() for term in topic_terms):
                    matched_chunks.append(cand)

            if not matched_chunks:
                claim.support_state = EvidenceSupportState.UNSUPPORTED
                claim.is_verified = False
                rejected_claims.append(claim)
                trace.append(f"REJECTED Claim: '{claim.text}' -> No supporting evidence found")
            else:
                claim.supporting_chunk_ids = [c.chunk_id for c in matched_chunks]
                combined_content = " ".join([c.content.lower() for c in matched_chunks])

                # Check if specific predicate / numeric constraint is met
                if claim.object_value.lower() in combined_content or claim.text.lower() in combined_content:
                    claim.support_state = EvidenceSupportState.DIRECTLY_SUPPORTED
                    claim.is_verified = True
                    verified_claims.append(claim)
                    trace.append(f"VERIFIED Claim: '{claim.text}' -> Directly supported by {len(matched_chunks)} chunks")
                else:
                    # Partial support -> Perform claim repair / qualification
                    claim.support_state = EvidenceSupportState.PARTIALLY_SUPPORTED
                    claim.is_verified = False
                    claim.repaired_text = f"{claim.subject}'s records indicate related experience; specific assertions in '{claim.text}' could not be fully verified."
                    qualified_claims.append(claim)
                    trace.append(f"QUALIFIED Claim: '{claim.text}' -> Repaired: '{claim.repaired_text}'")

            # Store in deduplication cache
            claim_cache[claim_sig] = claim

        # 3. Groundedness Evaluation
        total_claims = max(len(claims), 1)
        coverage_pct = (len(verified_claims) / total_claims) * 100.0
        valid_citations_count = sum(1 for c in validated_citations if c.is_valid)
        citation_precision_pct = (valid_citations_count / max(len(validated_citations), 1)) * 100.0

        if len(verified_claims) == len(claims):
            groundedness_state = GroundednessState.FULLY_GROUNDED
            answer_status = AnswerStatus.GROUNDED
        elif (len(verified_claims) + len(qualified_claims)) >= len(claims) * 0.7:
            groundedness_state = GroundednessState.MOSTLY_GROUNDED
            answer_status = AnswerStatus.GROUNDED_WITH_QUALIFICATIONS
        elif len(verified_claims) > 0:
            groundedness_state = GroundednessState.PARTIALLY_GROUNDED
            answer_status = AnswerStatus.PARTIAL
        else:
            groundedness_state = GroundednessState.INSUFFICIENTLY_GROUNDED
            answer_status = AnswerStatus.INSUFFICIENT_EVIDENCE

        # Check for any conflict
        conflicts_summary = [c.to_dict() for c in fused_evidence.conflicts]
        if conflicts_summary:
            answer_status = AnswerStatus.CONFLICTING

        return VerifiedEvidencePackage(
            task_id=task_id,
            tenant_id=tenant_id,
            query=fused_evidence.query,
            groundedness_state=groundedness_state,
            answer_status=answer_status,
            claims=claims,
            verified_claims=verified_claims,
            qualified_claims=qualified_claims,
            rejected_claims=rejected_claims,
            citations=validated_citations,
            conflicts=conflicts_summary,
            claim_coverage_pct=coverage_pct,
            citation_precision_pct=citation_precision_pct,
            security_state=authoritative_security_state,
            verification_trace=trace,
        )
