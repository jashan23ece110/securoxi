"""
SECUROXI AI Phase 2 Stage 3 — Skill & Requirement Normalization Engine
Maps skill aliases, abbreviations, experience numerical bounds, and education requirements
to canonical representations while preserving original source text.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from securoxi.logger import get_logger
from securoxi.screening.normalization_models import (
    NormalizedSkill,
    NormalizedExperienceRequirement,
    NormalizedEducationRequirement,
    NormalizedCertification,
    NormalizedProfile
)


# Canonical Skill Taxonomy Mapping
CANONICAL_SKILL_MAP: Dict[str, Dict[str, Any]] = {
    "JavaScript": {
        "aliases": ["js", "javascript", "ecmascript", "vanilla js"],
        "category": "Language"
    },
    "TypeScript": {
        "aliases": ["ts", "typescript"],
        "category": "Language"
    },
    "Node.js": {
        "aliases": ["node", "nodejs", "node.js"],
        "category": "Framework"
    },
    "PostgreSQL": {
        "aliases": ["postgres", "postgresql", "postgres db", "pg"],
        "category": "Database"
    },
    "MySQL": {
        "aliases": ["mysql", "my sql"],
        "category": "Database"
    },

    "Python": {
        "aliases": ["python", "python3", "py", "python developer", "python programming"],
        "category": "Language"
    },
    "Go": {
        "aliases": ["golang", "go lang"],
        "category": "Language"
    },
    "C++": {
        "aliases": ["cpp", "c++", "c plus plus"],
        "category": "Language"
    },
    "C#": {
        "aliases": ["c#", "c-sharp", "c sharp"],
        "category": "Language"
    },
    "C": {
        "aliases": ["c language", "c programming"],
        "category": "Language"
    },
    "Java": {
        "aliases": ["java", "java 8", "java 11", "java 17"],
        "category": "Language"
    },
    "React": {
        "aliases": ["react", "react.js", "reactjs", "react native"],
        "category": "Framework"
    },
    "Kubernetes": {
        "aliases": ["kubernetes", "k8s"],
        "category": "Tool"
    },
    "Docker": {
        "aliases": ["docker", "docker container", "docker containerization"],
        "category": "Tool"
    },
    "AWS": {
        "aliases": ["aws", "amazon web services"],
        "category": "Cloud"
    },
    "AWS Lambda": {
        "aliases": ["aws lambda", "lambda"],
        "category": "Cloud"
    },
    "PyTorch": {
        "aliases": ["pytorch", "torch"],
        "category": "Framework"
    },
    "TensorFlow": {
        "aliases": ["tensorflow", "tf"],
        "category": "Framework"
    },
    "FastAPI": {
        "aliases": ["fastapi", "fast api"],
        "category": "Framework"
    },
    "Django": {
        "aliases": ["django"],
        "category": "Framework"
    },
    "Flask": {
        "aliases": ["flask"],
        "category": "Framework"
    },
    "Git": {
        "aliases": ["git", "github", "gitlab"],
        "category": "Tool"
    },
    "SQL": {
        "aliases": ["sql", "ansi sql"],
        "category": "Language"
    }
}


class SecuroxiNormalizer:
    """
    Normalization Engine for Skills, Experience, Education, and Certifications.
    Enforces strict distinction rules (e.g. C != C++, Java != JavaScript).
    """

    def __init__(self):
        self.logger = get_logger("securoxi.screening.normalizer")

    def normalize_skill(self, raw_skill_text: str) -> NormalizedSkill:
        """
        Normalize a raw skill text string to its canonical representation.
        Preserves original raw_text.
        """
        clean_text = raw_skill_text.strip()
        lower_text = clean_text.lower()

        # Strict Exact Specific Matches First (e.g. C++ before C, JavaScript before Java)
        if lower_text in ["c++", "cpp", "c plus plus"]:
            return NormalizedSkill(raw_text=clean_text, canonical_name="C++", category="Language", confidence=1.0)
        if lower_text in ["c#", "c-sharp", "c sharp"]:
            return NormalizedSkill(raw_text=clean_text, canonical_name="C#", category="Language", confidence=1.0)
        if lower_text in ["javascript", "js", "ecmascript", "vanilla js"]:
            return NormalizedSkill(raw_text=clean_text, canonical_name="JavaScript", category="Language", confidence=1.0)
        if lower_text in ["java", "java 8", "java 11", "java 17"]:
            return NormalizedSkill(raw_text=clean_text, canonical_name="Java", category="Language", confidence=1.0)
        if lower_text in ["c", "c language", "c programming"]:
            return NormalizedSkill(raw_text=clean_text, canonical_name="C", category="Language", confidence=1.0)

        # General Taxonomy Search (Sorted by longest alias first to prevent shorter prefixes from matching early)
        all_aliases = []
        for canonical, info in CANONICAL_SKILL_MAP.items():
            for alias in info["aliases"]:
                all_aliases.append((alias, canonical, info["category"]))
        
        # Sort by alias length descending
        all_aliases.sort(key=lambda x: len(x[0]), reverse=True)

        for alias, canonical, category in all_aliases:
            if alias == lower_text or re.search(r"\b" + re.escape(alias) + r"\b", lower_text):
                # Prevent Java matching JavaScript
                if canonical == "Java" and "javascript" in lower_text:
                    continue
                # Prevent C matching C++ or C#
                if canonical == "C" and ("c++" in lower_text or "c#" in lower_text):
                    continue
                return NormalizedSkill(
                    raw_text=clean_text,
                    canonical_name=canonical,
                    category=category,
                    confidence=1.0
                )


        # Fallback: Title Case capitalization for unknown skills
        return NormalizedSkill(
            raw_text=clean_text,
            canonical_name=clean_text.title(),
            category="General",
            confidence=0.75
        )

    def normalize_skills_list(self, skills_list: List[str]) -> List[NormalizedSkill]:
        """Normalize a list of skill strings, removing canonical duplicates."""
        normalized: List[NormalizedSkill] = []
        seen_canonicals = set()

        for raw_skill in skills_list:
            norm_skill = self.normalize_skill(raw_skill)
            if norm_skill.canonical_name not in seen_canonicals:
                seen_canonicals.add(norm_skill.canonical_name)
                normalized.append(norm_skill)

        return normalized

    def normalize_experience(self, raw_exp_text: str) -> NormalizedExperienceRequirement:
        """
        Normalize experience expressions to min_years and max_years bounds.
        """
        clean_text = raw_exp_text.strip()
        
        # Match "3-5 years" or "3 to 5 yrs"
        range_match = re.search(r"\b(\d+)\s*[-–to]+\s*(\d+)\s*(years?|yrs?)\b", clean_text, re.IGNORECASE)
        if range_match:
            min_y = float(range_match.group(1))
            max_y = float(range_match.group(2))
            return NormalizedExperienceRequirement(raw_text=clean_text, min_years=min_y, max_years=max_y)

        # Match "5+ years" or "minimum 5 years"
        min_match = re.search(r"\b(\d+)\+?\s*(years?|yrs?)\b", clean_text, re.IGNORECASE)
        if min_match:
            min_y = float(min_match.group(1))
            return NormalizedExperienceRequirement(raw_text=clean_text, min_years=min_y)

        return NormalizedExperienceRequirement(raw_text=clean_text, min_years=0.0)

    def normalize_education(self, raw_edu_text: str) -> NormalizedEducationRequirement:
        """
        Normalize degree level and field of study.
        """
        clean_text = raw_edu_text.strip()
        lower_text = clean_text.lower()

        degree_level = "NOT_SPECIFIED"
        if any(term in lower_text for term in ["ph.d.", "phd", "doctorate"]):
            degree_level = "Doctorate"
        elif any(term in lower_text for term in ["master", "m.s.", "ms", "m.a.", "ma"]):
            degree_level = "Master's Degree"
        elif any(term in lower_text for term in ["bachelor", "b.s.", "bs", "b.a.", "ba"]):
            degree_level = "Bachelor's Degree"
        elif "associate" in lower_text:
            degree_level = "Associate Degree"

        field = "Computer Science / Engineering" if any(f in lower_text for f in ["computer science", "cs", "engineering", "software"]) else "NOT_SPECIFIED"

        return NormalizedEducationRequirement(
            raw_text=clean_text,
            degree_level=degree_level,
            field_of_study=field
        )

    def normalize_certification(self, raw_cert_text: str) -> NormalizedCertification:
        """
        Normalize certification title.
        """
        clean_text = raw_cert_text.strip()
        lower_text = clean_text.lower()

        if "aws" in lower_text and ("architect" in lower_text or "solutions" in lower_text):
            canonical = "AWS Certified Solutions Architect"
        elif "cissp" in lower_text:
            canonical = "CISSP"
        elif "kubernetes" in lower_text or "cka" in lower_text:
            canonical = "Certified Kubernetes Administrator (CKA)"
        else:
            canonical = clean_text.title()

        return NormalizedCertification(raw_text=clean_text, canonical_name=canonical)
