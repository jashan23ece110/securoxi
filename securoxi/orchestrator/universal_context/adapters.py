"""
SECUROXI AI Intelligence 2.0 — Input Adapters for Universal Context (Phase 4 Stage 17)
Converts heterogeneous data sources (Files, Folders, JDs, ATS, Collections, Previous Tasks)
into normalized, validated ContextItem instances with strict tenant isolation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import os
import hashlib
import time

from securoxi.orchestrator.universal_context.types import (
    ContextItemType,
    ContextSourceType,
    ContextScope,
    ContextSecurityState,
    ContextTrustLevel,
)
from securoxi.orchestrator.universal_context.models import ContextItem


class InputAdapter(ABC):
    """Abstract base contract for resolving external inputs into ContextItems."""

    @abstractmethod
    def resolve(
        self,
        raw_input: Any,
        tenant_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[ContextItem]:
        """Resolves input data into normalized ContextItem records."""
        pass


class FileInputAdapter(InputAdapter):
    """Adapts individual uploaded or staged files into ContextItems."""

    def resolve(
        self,
        raw_input: Any,
        tenant_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[ContextItem]:
        items: List[ContextItem] = []
        files_list = raw_input if isinstance(raw_input, list) else [raw_input]

        for f in files_list:
            if isinstance(f, str):
                name = os.path.basename(f)
                size = 0
                sec_state = ContextSecurityState.UNKNOWN
                trust = ContextTrustLevel.TRUSTED_CONTEXT
            elif isinstance(f, dict):
                name = f.get("name", "Document")
                size = f.get("size", 0)
                sec_str = f.get("security_status", f.get("security_verdict", "UNKNOWN")).upper()
                sec_state = ContextSecurityState(sec_str) if sec_str in ContextSecurityState.__members__ else ContextSecurityState.UNKNOWN
                
                if sec_state == ContextSecurityState.HIGH_RISK:
                    trust = ContextTrustLevel.UNTRUSTED_EVIDENCE
                elif sec_state == ContextSecurityState.UNINSPECTABLE:
                    trust = ContextTrustLevel.REVIEW_REQUIRED
                else:
                    trust = ContextTrustLevel.TRUSTED_CONTEXT
            else:
                continue

            content_hash = hashlib.sha256(name.encode("utf-8")).hexdigest()
            item = ContextItem(
                item_type=ContextItemType.DOCUMENT,
                source_type=ContextSourceType.LOCAL_UPLOAD,
                source_id=name,
                tenant_id=tenant_id,
                scope=ContextScope.DOCUMENT,
                security_state=sec_state,
                trust_level=trust,
                title=name,
                metadata={"filename": name, "file_size": size},
                content_hash=content_hash,
                size_bytes=size,
            )
            items.append(item)

        return items


class FolderInputAdapter(InputAdapter):
    """Adapts folder or bulk directory references into a lightweight ContextItem."""

    def resolve(
        self,
        raw_input: Any,
        tenant_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[ContextItem]:
        if not isinstance(raw_input, dict):
            return []

        folder_name = raw_input.get("name", "Folder_Collection")
        total_files = raw_input.get("totalFiles", raw_input.get("total_files", 0))
        supported = raw_input.get("supported", total_files)

        content_hash = hashlib.sha256(f"{folder_name}:{total_files}".encode("utf-8")).hexdigest()
        item = ContextItem(
            item_type=ContextItemType.FOLDER,
            source_type=ContextSourceType.LOCAL_FOLDER,
            source_id=folder_name,
            tenant_id=tenant_id,
            scope=ContextScope.FOLDER,
            security_state=ContextSecurityState.UNKNOWN,
            trust_level=ContextTrustLevel.RESTRICTED_CONTEXT,
            title=folder_name,
            metadata={
                "folder_name": folder_name,
                "total_files": total_files,
                "supported_files": supported,
            },
            content_hash=content_hash,
            size_bytes=total_files,
        )
        return [item]


class JDInputAdapter(InputAdapter):
    """Adapts job descriptions and hiring requirements into a ContextItem."""

    def resolve(
        self,
        raw_input: Any,
        tenant_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[ContextItem]:
        if isinstance(raw_input, str):
            title = "Job Description"
            skills: List[str] = []
            exp = 0
            text = raw_input
        elif isinstance(raw_input, dict):
            title = raw_input.get("title", "Job Description")
            skills = raw_input.get("requiredSkills", raw_input.get("required_skills", []))
            exp = raw_input.get("expYears", raw_input.get("exp_years", 0))
            text = raw_input.get("textSnippet", raw_input.get("raw_text", ""))
        else:
            return []

        content_hash = hashlib.sha256(f"{title}:{','.join(skills)}".encode("utf-8")).hexdigest()
        item = ContextItem(
            item_type=ContextItemType.JOB_DESCRIPTION,
            source_type=ContextSourceType.LOCAL_UPLOAD,
            source_id=title,
            tenant_id=tenant_id,
            scope=ContextScope.JOB,
            security_state=ContextSecurityState.SAFE,
            trust_level=ContextTrustLevel.TRUSTED_CONTEXT,
            title=title,
            metadata={
                "job_title": title,
                "required_skills": skills,
                "experience_years": exp,
                "snippet": text[:200] if text else "",
            },
            content_hash=content_hash,
        )
        return [item]


class ATSInputAdapter(InputAdapter):
    """Adapts ATS connections and candidate sets without storing credentials."""

    def resolve(
        self,
        raw_input: Any,
        tenant_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[ContextItem]:
        if not isinstance(raw_input, dict):
            return []

        system_name = raw_input.get("system", "Workday")
        connected = raw_input.get("connected", False)
        candidate_count = raw_input.get("candidateCount", raw_input.get("candidate_count", 0))
        candidates_raw = raw_input.get("candidates", [])

        items: List[ContextItem] = []
        # 1. ATS Job / System Item
        job_item = ContextItem(
            item_type=ContextItemType.ATS_JOB,
            source_type=ContextSourceType.ATS,
            source_id=f"{system_name}-REQUISITION",
            tenant_id=tenant_id,
            scope=ContextScope.JOB,
            security_state=ContextSecurityState.SAFE,
            trust_level=ContextTrustLevel.TRUSTED_CONTEXT,
            title=f"{system_name} Requisition",
            metadata={"system": system_name, "connected": connected, "candidate_count": candidate_count},
        )
        items.append(job_item)

        # 2. Individual ATS Candidates if supplied
        for c in candidates_raw:
            c_name = c.get("name", "Candidate")
            c_id = c.get("candidate_id", c.get("id", c_name))
            cand_item = ContextItem(
                item_type=ContextItemType.ATS_CANDIDATE,
                source_type=ContextSourceType.ATS,
                source_id=c_id,
                tenant_id=tenant_id,
                scope=ContextScope.CANDIDATE,
                security_state=ContextSecurityState.SAFE,
                trust_level=ContextTrustLevel.TRUSTED_CONTEXT,
                title=c_name,
                metadata={"ats_id": c_id, "name": c_name},
            )
            items.append(cand_item)

        return items


class CollectionInputAdapter(InputAdapter):
    """Adapts indexed enterprise document collections into a ContextItem."""

    def resolve(
        self,
        raw_input: Any,
        tenant_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[ContextItem]:
        if not isinstance(raw_input, dict):
            return []

        col_id = raw_input.get("collection_id", "COL-DEFAULT")
        col_name = raw_input.get("name", col_id)
        doc_count = raw_input.get("document_count", 0)

        item = ContextItem(
            item_type=ContextItemType.COLLECTION,
            source_type=ContextSourceType.INDEXED_COLLECTION,
            source_id=col_id,
            tenant_id=tenant_id,
            scope=ContextScope.COLLECTION,
            security_state=ContextSecurityState.SAFE,
            trust_level=ContextTrustLevel.TRUSTED_CONTEXT,
            title=col_name,
            metadata={"collection_id": col_id, "document_count": doc_count},
        )
        return [item]


class PreviousTaskAdapter(InputAdapter):
    """Adapts verified results from a prior task run into ContextItems for follow-ups."""

    def resolve(
        self,
        raw_input: Any,
        tenant_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[ContextItem]:
        if not isinstance(raw_input, dict):
            return []

        prev_task_id = raw_input.get("task_id", raw_input.get("previous_task_id", "TASK-PREV"))
        summary = raw_input.get("executive_summary", "")

        item = ContextItem(
            item_type=ContextItemType.PREVIOUS_TASK_RESULT,
            source_type=ContextSourceType.PREVIOUS_TASK,
            source_id=prev_task_id,
            tenant_id=tenant_id,
            scope=ContextScope.TASK,
            security_state=ContextSecurityState.SAFE,
            trust_level=ContextTrustLevel.TRUSTED_CONTEXT,
            title=f"Prior Task {prev_task_id}",
            metadata={"task_id": prev_task_id, "summary_snippet": summary[:200]},
        )
        return [item]
