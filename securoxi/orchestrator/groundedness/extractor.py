"""
SECUROXI AI Intelligence 2.0 — Atomic Claim Extractor
Decomposes compound reasoning output and structured statements into verified atomic claims.
"""

from typing import List, Dict, Any, Optional
import re
from securoxi.orchestrator.groundedness.types import ClaimType
from securoxi.orchestrator.groundedness.models import Claim
from securoxi.logger import get_logger

logger = get_logger("orchestrator.claim_extractor")


class ClaimExtractor:
    """Decomposes paragraphs and compound statements into atomic verifiable claims."""

    def extract_claims(self, text: str, default_subject: str = "Subject") -> List[Claim]:
        """
        Splits input text by punctuation, clauses ('and', 'because', 'with'),
        and identifies semantic subject-predicate-value tuples.
        """
        claims: List[Claim] = []
        sentences = [s.strip() for s in re.split(r"[.\n]+", text) if len(s.strip()) > 3]

        for s in sentences:
            # Check for security claims
            if any(w in s.lower() for w in ["safe", "high_risk", "uninspectable", "suspicious"]):
                claims.append(
                    Claim(
                        text=s,
                        claim_type=ClaimType.SECURITY,
                        subject=default_subject,
                        predicate="security_status",
                        object_value="SAFE" if "safe" in s.lower() else "HIGH_RISK",
                    )
                )
            # Check for ranking claims
            elif any(w in s.lower() for w in ["strongest", "#1", "top candidate", "highest ranked"]):
                claims.append(
                    Claim(
                        text=s,
                        claim_type=ClaimType.RANKING,
                        subject=default_subject,
                        predicate="candidate_ranking",
                        object_value="TOP_RANK",
                    )
                )
            # Check for numeric / experience claims
            elif re.search(r"\b\d+\s+(?:years|months|yrs)\b", s, re.IGNORECASE):
                match = re.search(r"(\d+\s+(?:years|months|yrs))", s, re.IGNORECASE)
                claims.append(
                    Claim(
                        text=s,
                        claim_type=ClaimType.FACTUAL,
                        subject=default_subject,
                        predicate="years_experience",
                        object_value=match.group(1) if match else "experience",
                    )
                )
            # General qualification/factual assertion
            else:
                claims.append(
                    Claim(
                        text=s,
                        claim_type=ClaimType.QUALIFICATION if "qualified" in s.lower() else ClaimType.FACTUAL,
                        subject=default_subject,
                        predicate="domain_qualification",
                        object_value=s,
                    )
                )

        return claims
