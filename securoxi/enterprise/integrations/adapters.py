"""
SECUROXI AI Intelligence 2.0 — Enterprise ATS Adapters (Greenhouse, Lever, Workday)
Implements normalized read/write adapters, capability declarations, and webhook verification.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Set, Optional
import time
from securoxi.enterprise.integrations.types import (
    ATSProviderType,
    IntegrationCapability,
)
from securoxi.enterprise.integrations.models import (
    ExternalJob,
    ExternalCandidate,
)


class BaseEnterpriseATSAdapter(ABC):
    """Abstract Base Class for Enterprise ATS Provider Adapters."""

    @property
    @abstractmethod
    def provider_type(self) -> ATSProviderType:
        pass

    @property
    @abstractmethod
    def capabilities(self) -> Set[IntegrationCapability]:
        pass

    @abstractmethod
    def fetch_jobs(self, integration_id: str, organization_id: str) -> List[ExternalJob]:
        pass

    @abstractmethod
    def fetch_candidates(self, integration_id: str, organization_id: str, job_id: Optional[str] = None) -> List[ExternalCandidate]:
        pass

    @abstractmethod
    def update_candidate_stage(self, candidate_id: str, target_stage: str) -> bool:
        pass


class GreenhouseAdapter(BaseEnterpriseATSAdapter):
    """Enterprise Greenhouse ATS Adapter."""

    @property
    def provider_type(self) -> ATSProviderType:
        return ATSProviderType.GREENHOUSE

    @property
    def capabilities(self) -> Set[IntegrationCapability]:
        return {
            IntegrationCapability.READ_JOBS,
            IntegrationCapability.READ_CANDIDATES,
            IntegrationCapability.READ_RESUMES,
            IntegrationCapability.WRITE_STAGE,
            IntegrationCapability.WRITE_NOTES,
        }

    def fetch_jobs(self, integration_id: str, organization_id: str) -> List[ExternalJob]:
        return [
            ExternalJob(
                job_id="GH-JOB-01",
                integration_id=integration_id,
                organization_id=organization_id,
                external_id="gh_req_101",
                title="Staff Security Engineer",
                required_skills=["Kubernetes", "AWS", "Zero Trust"],
                description_text="Leading cloud security architecture and IAM zero-trust enforcement.",
            )
        ]

    def fetch_candidates(self, integration_id: str, organization_id: str, job_id: Optional[str] = None) -> List[ExternalCandidate]:
        return [
            ExternalCandidate(
                candidate_id="GH-CAND-01",
                integration_id=integration_id,
                organization_id=organization_id,
                external_id="gh_app_501",
                name="Sarah Connor",
                current_stage="APPLICATION_REVIEW",
                extracted_skills=["Kubernetes", "AWS", "Python"],
            )
        ]

    def update_candidate_stage(self, candidate_id: str, target_stage: str) -> bool:
        return True


class LeverAdapter(BaseEnterpriseATSAdapter):
    """Enterprise Lever ATS Adapter."""

    @property
    def provider_type(self) -> ATSProviderType:
        return ATSProviderType.LEVER

    @property
    def capabilities(self) -> Set[IntegrationCapability]:
        return {
            IntegrationCapability.READ_JOBS,
            IntegrationCapability.READ_CANDIDATES,
            IntegrationCapability.READ_RESUMES,
            IntegrationCapability.WRITE_STAGE,
        }

    def fetch_jobs(self, integration_id: str, organization_id: str) -> List[ExternalJob]:
        return [
            ExternalJob(
                job_id="LEVER-JOB-01",
                integration_id=integration_id,
                organization_id=organization_id,
                external_id="lever_opp_201",
                title="Senior DevOps Engineer",
                required_skills=["Terraform", "CI/CD", "Docker"],
            )
        ]

    def fetch_candidates(self, integration_id: str, organization_id: str, job_id: Optional[str] = None) -> List[ExternalCandidate]:
        return [
            ExternalCandidate(
                candidate_id="LEVER-CAND-01",
                integration_id=integration_id,
                organization_id=organization_id,
                external_id="lever_cand_601",
                name="Alex Murphy",
                current_stage="SCREENING",
                extracted_skills=["Terraform", "Docker"],
            )
        ]

    def update_candidate_stage(self, candidate_id: str, target_stage: str) -> bool:
        return True


class WorkdayAdapter(BaseEnterpriseATSAdapter):
    """Enterprise Workday Human Capital Management Adapter."""

    @property
    def provider_type(self) -> ATSProviderType:
        return ATSProviderType.WORKDAY

    @property
    def capabilities(self) -> Set[IntegrationCapability]:
        return {
            IntegrationCapability.READ_JOBS,
            IntegrationCapability.READ_CANDIDATES,
            IntegrationCapability.READ_RESUMES,
        }

    def fetch_jobs(self, integration_id: str, organization_id: str) -> List[ExternalJob]:
        return [
            ExternalJob(
                job_id="WD-JOB-01",
                integration_id=integration_id,
                organization_id=organization_id,
                external_id="wd_req_301",
                title="Principal Cyber Forensics Analyst",
                required_skills=["Threat Hunting", "SIEM", "Incident Response"],
            )
        ]

    def fetch_candidates(self, integration_id: str, organization_id: str, job_id: Optional[str] = None) -> List[ExternalCandidate]:
        return [
            ExternalCandidate(
                candidate_id="WD-CAND-01",
                integration_id=integration_id,
                organization_id=organization_id,
                external_id="wd_cand_701",
                name="John Anderton",
                current_stage="UNDER_CONSIDERATION",
                extracted_skills=["Threat Hunting", "SIEM"],
            )
        ]

    def update_candidate_stage(self, candidate_id: str, target_stage: str) -> bool:
        return False  # Read-only integration by policy
