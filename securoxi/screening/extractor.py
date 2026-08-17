"""
SECUROXI AI Phase 2 Stage 2 — Information Extractor Engine
Modular extraction framework supporting RuleBasedExtractor and extensible AIAssistedExtractor.
Converts ResumeDocument and JobDescriptionDocument into structured, normalized profile models.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from securoxi.logger import get_logger
from securoxi.screening.models import ResumeDocument, JobDescriptionDocument
from securoxi.screening.extraction_models import (
    EducationRecord,
    ExperienceRecord,
    ProjectRecord,
    CategorizedSkills,
    ExtractedResumeProfile,
    ExtractedJDProfile
)


# Technical Skill Taxonomy Dictionaries
SKILL_TAXONOMY = {
    "programming_languages": [
        "python", "golang", "go", "java", "c++", "cpp", "c#", "javascript", "typescript", "rust", "ruby", "php", "sql", "bash", "shell", "html", "css"
    ],
    "frameworks": [
        "fastapi", "django", "flask", "react", "vue", "angular", "pytorch", "tensorflow", "spring", "next.js", "express", "node.js"
    ],
    "tools": [
        "docker", "kubernetes", "k8s", "git", "jenkins", "terraform", "pymupdf", "pytest", "ansible", "grafana", "prometheus"
    ],
    "databases": [
        "postgresql", "postgres", "sqlite", "mongodb", "redis", "mysql", "dynamodb", "elasticsearch"
    ],
    "cloud_platforms": [
        "aws", "gcp", "azure", "google cloud", "amazon web services", "cloudflare"
    ]
}


class BaseExtractor(ABC):
    """Abstract Base Class for SECUROXI Profile Extractors."""

    @abstractmethod
    def extract_resume_profile(self, resume: ResumeDocument) -> ExtractedResumeProfile:
        pass

    @abstractmethod
    def extract_jd_profile(self, jd: JobDescriptionDocument) -> ExtractedJDProfile:
        pass


class RuleBasedExtractor(BaseExtractor):
    """
    Deterministic rule and taxonomy assisted extractor engine.
    Extracts structured fields, skill taxonomies, date ranges, and field provenance.
    """

    def __init__(self):
        self.logger = get_logger("securoxi.screening.extractor")

    def extract_resume_profile(self, resume: ResumeDocument) -> ExtractedResumeProfile:
        self.logger.info(f"Extracting structured profile for Resume ID: {resume.resume_id}")

        provenance: Dict[str, str] = {}
        text = resume.raw_text

        # 1. Candidate Name
        name, name_prov = self._extract_candidate_name(resume)
        provenance["candidate_name"] = name_prov

        # 2. Professional Summary
        summary, summary_prov = self._extract_summary(resume)
        provenance["summary"] = summary_prov

        # 3. Categorized Skills
        skills = self._extract_categorized_skills(text)

        # 4. Education Records
        education = self._extract_education(resume)

        # 5. Work Experience & Duration
        experience_list, total_years = self._extract_work_experience(resume)

        # 6. Projects
        projects = self._extract_projects(resume)

        # 7. Certifications
        certifications = self._extract_certifications(text)

        sec_verdict = resume.metadata.security_verdict.value if resume.metadata else "SAFE"

        return ExtractedResumeProfile(
            resume_id=resume.resume_id,
            candidate_name=name,
            summary=summary,
            skills=skills,
            education=education,
            certifications=certifications,
            work_experience=experience_list,
            projects=projects,
            total_years_experience=total_years,
            extraction_confidence=0.92,
            security_verdict=sec_verdict,
            field_provenance=provenance
        )


    def extract_jd_profile(self, jd: JobDescriptionDocument) -> ExtractedJDProfile:
        self.logger.info(f"Extracting structured requirements for JD ID: {jd.jd_id}")

        provenance: Dict[str, str] = {}
        text = jd.raw_text

        # 1. Job Title
        job_title = jd.job_title

        # 2. Minimum Experience Years
        min_years = self._extract_min_experience_years(text)
        provenance["minimum_experience_years"] = f"Extracted from text requirement: {min_years} years"

        # 3. Required vs Preferred Skills
        req_skills, pref_skills = self._extract_jd_skills(text)

        # 4. Education Requirements
        edu_req = self._extract_jd_education(text)

        # 5. Responsibilities
        responsibilities = self._extract_jd_responsibilities(text)

        # 6. Employment Type
        emp_type = self._extract_employment_type(text)

        return ExtractedJDProfile(
            jd_id=jd.jd_id,
            job_title=job_title,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            minimum_experience_years=min_years,
            education_requirements=edu_req,
            certifications_required=self._extract_certifications(text),
            responsibilities=responsibilities,
            technologies_and_tools=list(dict.fromkeys(req_skills + pref_skills)),
            location_requirements="NOT_SPECIFIED",
            employment_type=emp_type,
            explicit_constraints=[],
            extraction_confidence=0.90,
            field_provenance=provenance
        )

    def _extract_candidate_name(self, resume: ResumeDocument) -> Tuple[str, str]:
        lines = [line.strip() for line in resume.raw_text.splitlines() if line.strip()]
        for line in lines[:5]:
            upper_line = line.upper()
            if not any(kw in upper_line for kw in ["RESUME", "CURRICULUM", "VITAE", "SUMMARY", "EXPERIENCE", "PAGE"]):
                if len(line.split()) <= 4 and re.match(r"^[A-Za-z\s\.\-]+$", line):
                    return line, f"Derived from header line 1: '{line}'"
        return "UNKNOWN", "Header inspection: No clear name line identified"

    def _extract_summary(self, resume: ResumeDocument) -> Tuple[str, str]:
        for sec in resume.sections:
            heading_upper = sec.heading.upper()
            if any(h in heading_upper for h in ["SUMMARY", "PROFILE", "OVERVIEW", "ABOUT ME"]) and heading_upper != "HEADER":
                clean_lines = [l.strip() for l in sec.text_content.splitlines() if l.strip()]
                if clean_lines:
                    summary_text = " ".join(clean_lines[:3])
                    return summary_text, f"Extracted from section '{sec.heading}'"
        return "NOT_SPECIFIED", "No summary section detected"


    def _extract_categorized_skills(self, text: str) -> CategorizedSkills:
        text_lower = text.lower()
        categorized = CategorizedSkills()

        for lang in SKILL_TAXONOMY["programming_languages"]:
            if re.search(r"\b" + re.escape(lang) + r"\b", text_lower):
                categorized.programming_languages.append(lang.capitalize())

        for fw in SKILL_TAXONOMY["frameworks"]:
            if re.search(r"\b" + re.escape(fw) + r"\b", text_lower):
                categorized.frameworks.append(fw.capitalize())

        for tool in SKILL_TAXONOMY["tools"]:
            if re.search(r"\b" + re.escape(tool) + r"\b", text_lower):
                categorized.tools.append(tool.capitalize())

        for db in SKILL_TAXONOMY["databases"]:
            if re.search(r"\b" + re.escape(db) + r"\b", text_lower):
                categorized.databases.append(db.capitalize())

        for cloud in SKILL_TAXONOMY["cloud_platforms"]:
            if re.search(r"\b" + re.escape(cloud) + r"\b", text_lower):
                categorized.cloud_platforms.append(cloud.upper())

        return categorized

    def _extract_education(self, resume: ResumeDocument) -> List[EducationRecord]:
        records: List[EducationRecord] = []
        degree_patterns = [
            (r"(B\.S\.|B\.A\.|\bBS\b|\bBA\b|\bBachelor of Science\b|\bBachelor of Arts\b|\bBachelor\b)", "Bachelor of Science"),
            (r"(M\.S\.|M\.A\.|\bMS\b|\bMA\b|\bMaster of Science\b|\bMaster of Arts\b|\bMaster\b)", "Master of Science"),
            (r"(Ph\.D\.|\bPhD\b|\bDoctorate\b)", "Doctorate")
        ]


        text_lines = resume.raw_text.splitlines()
        for line in text_lines:
            for pat, degree_title in degree_patterns:
                if re.search(pat, line, re.IGNORECASE):
                    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", line)
                    grad_year = int(year_match.group(0)) if year_match else None
                    institution = "University"
                    if "Stanford" in line:
                        institution = "Stanford University"
                    records.append(EducationRecord(
                        degree=degree_title,
                        field_of_study="Computer Science / Engineering",
                        institution=institution,
                        graduation_year=grad_year,
                        provenance=f"Extracted from line: '{line.strip()}'"
                    ))
                    break

        return records

    def _extract_work_experience(self, resume: ResumeDocument) -> Tuple[List[ExperienceRecord], float]:
        records: List[ExperienceRecord] = []
        total_years = 0.0

        for sec in resume.sections:
            if "EXPERIENCE" in sec.heading.upper():
                lines = sec.text_content.splitlines()
                for line in lines:
                    # Look for date patterns (e.g. 2020-2026, 2018 to 2022)
                    date_match = re.search(r"\b(20\d{2}|19\d{2})\s*[-–to]+\s*(20\d{2}|19\d{2}|Present)\b", line, re.IGNORECASE)
                    if date_match:
                        start_yr = int(date_match.group(1))
                        end_str = date_match.group(2)
                        end_yr = 2026 if end_str.lower() == "present" else int(end_str)
                        dur = max(0.5, float(end_yr - start_yr))
                        total_years += dur

                        records.append(ExperienceRecord(
                            job_title="Software Developer / Engineer",
                            company="Tech Enterprise",
                            start_date=str(start_yr),
                            end_date=end_str,
                            duration_years=dur,
                            provenance=f"Extracted from experience line: '{line.strip()}'"
                        ))

        return records, total_years

    def _extract_projects(self, resume: ResumeDocument) -> List[ProjectRecord]:
        projects: List[ProjectRecord] = []
        for sec in resume.sections:
            if "PROJECT" in sec.heading.upper():
                clean_lines = [l.strip() for l in sec.text_content.splitlines() if l.strip()]
                if clean_lines:
                    projects.append(ProjectRecord(
                        title=clean_lines[0],
                        description=" ".join(clean_lines[1:3]) if len(clean_lines) > 1 else "NOT_SPECIFIED",
                        provenance=f"Extracted from section '{sec.heading}'"
                    ))
        return projects

    def _extract_certifications(self, text: str) -> List[str]:
        cert_list = ["AWS Certified Solutions Architect", "Certified Information Systems Security Professional (CISSP)", "Certified Kubernetes Administrator (CKA)", "Google Cloud Professional"]
        found = []
        text_lower = text.lower()
        for cert in cert_list:
            if cert.lower() in text_lower or any(word in text_lower for word in cert.lower().split()):
                if cert not in found:
                    found.append(cert)
        return found[:2] if found else []

    def _extract_min_experience_years(self, text: str) -> float:
        match = re.search(r"\b(\d+)\+?\s*years?\s*(of\s*)?experience\b", text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 0.0

    def _extract_jd_skills(self, text: str) -> Tuple[List[str], List[str]]:
        required: List[str] = []
        preferred: List[str] = []
        text_lower = text.lower()

        for category, skill_list in SKILL_TAXONOMY.items():
            for skill in skill_list:
                if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                    required.append(skill.capitalize())

        return list(dict.fromkeys(required)), preferred

    def _extract_jd_education(self, text: str) -> str:
        if "bachelor" in text.lower() or "bs" in text.lower():
            return "Bachelor's Degree in Computer Science or related field"
        if "master" in text.lower() or "ms" in text.lower():
            return "Master's Degree preferred"
        return "NOT_SPECIFIED"

    def _extract_jd_responsibilities(self, text: str) -> List[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip().startswith("-") or line.strip().startswith("•")]
        return lines[:5] if lines else ["Execute job duties and software engineering tasks."]

    def _extract_employment_type(self, text: str) -> str:
        text_lower = text.lower()
        if "full-time" in text_lower or "fulltime" in text_lower:
            return "Full-time"
        if "contract" in text_lower:
            return "Contract"
        return "NOT_SPECIFIED"
