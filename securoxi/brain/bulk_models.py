"""
SECUROXI AI Document Intelligence Stage 3 — Distributed Bulk Processing Models
Provides persistent Job and Task data models for asynchronous multi-worker document processing.
"""

import time
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PARTIAL = "PARTIAL"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    POISON = "POISON"


@dataclass
class BulkDocumentTask:
    """Individual document processing unit within a bulk batch job."""
    task_id: str
    batch_id: str
    job_id: str
    tenant_id: str
    file_path: str
    filename: str
    file_hash: str
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result_scan_id: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task into JSON-serializable dictionary."""
        return {
            "task_id": self.task_id,
            "batch_id": self.batch_id,
            "job_id": self.job_id,
            "tenant_id": self.tenant_id,
            "filename": self.filename,
            "file_hash": self.file_hash,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "result_scan_id": self.result_scan_id,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "metadata": self.metadata
        }


@dataclass
class BulkBatchJob:
    """Asynchronous batch processing job container."""
    job_id: str
    batch_id: str
    tenant_id: str
    source: str
    status: JobStatus = JobStatus.QUEUED
    total_documents: int = 0
    completed_documents: int = 0
    failed_documents: int = 0
    safe_count: int = 0
    suspicious_count: int = 0
    high_risk_count: int = 0
    uninspectable_count: int = 0
    created_at: str = field(default_factory=lambda: time.strftime('%Y-%m-%d %H:%M:%S'))
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress_pct: float = 0.0
    tasks: List[BulkDocumentTask] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_progress(self):
        """Re-evaluates progress percentage and aggregate verdict statistics."""
        if self.total_documents == 0:
            self.progress_pct = 100.0
            return

        processed = self.completed_documents + self.failed_documents
        self.progress_pct = round((processed / self.total_documents) * 100.0, 1)

        if processed >= self.total_documents:
            if self.failed_documents == self.total_documents:
                self.status = JobStatus.FAILED
            elif self.failed_documents > 0:
                self.status = JobStatus.PARTIAL
            else:
                self.status = JobStatus.COMPLETE
            self.completed_at = time.strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> Dict[str, Any]:
        """Convert job into JSON-serializable dictionary."""
        return {
            "job_id": self.job_id,
            "batch_id": self.batch_id,
            "tenant_id": self.tenant_id,
            "source": self.source,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "total_documents": self.total_documents,
            "completed_documents": self.completed_documents,
            "failed_documents": self.failed_documents,
            "progress_pct": self.progress_pct,
            "verdict_summary": {
                "safe": self.safe_count,
                "suspicious": self.suspicious_count,
                "high_risk": self.high_risk_count,
                "uninspectable": self.uninspectable_count
            },
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }
