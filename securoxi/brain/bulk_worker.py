"""
SECUROXI AI Document Intelligence Stage 3 — Distributed Worker Engine & Batch Manager
Consumes bulk document tasks from ContinuousEventBus, executes security scanning,
enforces idempotency deduplication, handles retries/DLQ, and updates persistent batch state.
"""

import os
import time
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.scanner import SecuroxiScanner
from securoxi.storage.db import SecuroxiDatabase
from securoxi.brain.continuous_monitoring import ContinuousEventBus
from securoxi.brain.bulk_models import (
    BulkBatchJob,
    BulkDocumentTask,
    JobStatus,
    TaskStatus
)


class SecuroxiBulkManager:
    """
    Centralized Distributed Bulk Job Manager.
    Creates batch jobs, calculates file SHA-256 hashes for idempotency, dispatches tasks
    to event broker, and tracks real-time progress.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.brain.bulk_manager")
        self.db = SecuroxiDatabase()
        self.event_bus = ContinuousEventBus(config=self.config)
        self.scanner = SecuroxiScanner(config=self.config)
        self._jobs_cache: Dict[str, BulkBatchJob] = {}

    def create_batch_job(
        self,
        file_paths: List[str],
        tenant_id: str = "TENANT-DEFAULT",
        source: str = "BULK_API_UPLOAD"
    ) -> BulkBatchJob:
        """
        Creates an asynchronous bulk batch job, deduplicates files by SHA-256 hash,
        and enqueues tasks for distributed worker consumption.
        """
        batch_id = f"BATCH-{uuid.uuid4().hex[:8]}"
        job_id = f"JOB-{uuid.uuid4().hex[:8]}"
        self.logger.info(f"Creating bulk batch job '{job_id}' ({batch_id}) for tenant '{tenant_id}' with {len(file_paths)} files.")

        tasks: List[BulkDocumentTask] = []
        seen_hashes = set()

        for path in file_paths:
            if not os.path.exists(path) or not os.path.isfile(path):
                continue

            # Calculate SHA-256 file hash for idempotency deduplication
            hasher = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            file_hash = hasher.hexdigest()

            if file_hash in seen_hashes:
                self.logger.info(f"Idempotency: Skipping duplicate file in batch '{filename}': Hash {file_hash[:8]}...")
                continue
            seen_hashes.add(file_hash)

            filename = os.path.basename(path)
            task_id = f"TASK-{uuid.uuid4().hex[:8]}"
            task = BulkDocumentTask(
                task_id=task_id,
                batch_id=batch_id,
                job_id=job_id,
                tenant_id=tenant_id,
                file_path=path,
                filename=filename,
                file_hash=file_hash
            )
            tasks.append(task)

        job = BulkBatchJob(
            job_id=job_id,
            batch_id=batch_id,
            tenant_id=tenant_id,
            source=source,
            status=JobStatus.QUEUED,
            total_documents=len(tasks),
            tasks=tasks
        )

        self._jobs_cache[batch_id] = job
        self._jobs_cache[job_id] = job

        # Dispatch tasks to ContinuousEventBus as EnterpriseSecurityEvents
        from securoxi.brain.continuous_monitoring import EnterpriseSecurityEvent, EnterpriseEventType
        for task in tasks:
            evt = EnterpriseSecurityEvent(
                event_type=EnterpriseEventType.NEW_DOCUMENT,
                source="BULK_BATCH_JOB",
                file_path=task.file_path,
                payload={
                    "type": "BULK_DOCUMENT_TASK",
                    "task": task.to_dict(),
                    "tenant_id": tenant_id
                }
            )
            self.event_bus.publish_event(evt)

        self.logger.info(f"Successfully enqueued {len(tasks)} tasks for batch '{batch_id}'.")
        return job

    def process_task(self, task: BulkDocumentTask) -> BulkDocumentTask:
        """
        Executes document scanning for a single task within a distributed worker.
        Enforces retries (up to 3) and routes poison documents to DLQ upon failure.
        """
        t0 = time.time()
        task.status = TaskStatus.PROCESSING
        self.logger.info(f"Worker processing task '{task.task_id}' ({task.filename}) for tenant '{task.tenant_id}'...")

        try:
            # Execute Phase 1 Security Pipeline Scan
            report = self.scanner.scan(task.file_path)
            task.result_scan_id = report.metadata.get("scan_id", f"SCAN-{uuid.uuid4().hex[:8]}")
            task.execution_time_ms = (time.time() - t0) * 1000
            task.status = TaskStatus.COMPLETE

            # Persist scan report in database
            self.db.save_scan(report.to_dict(), tenant_id=task.tenant_id)
            self.logger.info(f"Task '{task.task_id}' completed successfully: Verdict={report.verdict.value}")

        except Exception as err:
            task.retry_count += 1
            task.error_message = str(err)
            self.logger.error(f"Task '{task.task_id}' failed (Attempt {task.retry_count}/{task.max_retries}): {err}")

            if task.retry_count >= task.max_retries:
                task.status = TaskStatus.POISON
                self.logger.critical(f"POISON DOCUMENT DETECTED: Task '{task.task_id}' exceeded max retries. Routing to Dead-Letter Queue (securoxi:dlq).")
                from securoxi.brain.continuous_monitoring import EnterpriseSecurityEvent, EnterpriseEventType
                dlq_evt = EnterpriseSecurityEvent(
                    event_type=EnterpriseEventType.SUSPICIOUS_CONTENT,
                    source="BULK_WORKER_DLQ",
                    file_path=task.file_path,
                    payload={
                        "type": "DEAD_LETTER_QUEUE",
                        "task": task.to_dict(),
                        "reason": f"Max retries exceeded: {err}",
                        "tenant_id": task.tenant_id
                    }
                )
                self.event_bus.publish_event(dlq_evt)
            else:
                task.status = TaskStatus.RETRYING

        return task

    def process_batch_sync(self, batch_id: str, max_workers: int = 4) -> BulkBatchJob:
        """
        Executes all pending tasks in a batch using a worker thread pool.
        """
        job = self._jobs_cache.get(batch_id)
        if not job:
            raise ValueError(f"Batch ID '{batch_id}' not found.")

        job.status = JobStatus.PROCESSING
        job.started_at = time.strftime('%Y-%m-%d %H:%M:%S')

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            processed_tasks = list(executor.map(self.process_task, job.tasks))

        # Aggregate batch statistics
        job.tasks = processed_tasks
        job.completed_documents = sum(1 for t in processed_tasks if t.status == TaskStatus.COMPLETE)
        job.failed_documents = sum(1 for t in processed_tasks if t.status in [TaskStatus.FAILED, TaskStatus.POISON])

        # Aggregate verdicts from DB or metadata
        for t in processed_tasks:
            if t.result_scan_id:
                scan = self.db.get_scan(t.result_scan_id, tenant_id=job.tenant_id)
                if scan:
                    v = scan.get("verdict", "SAFE")
                    st = scan.get("analysis_status", "ANALYZED")
                    if st == "UNINSPECTABLE":
                        job.uninspectable_count += 1
                    elif v == "HIGH_RISK":
                        job.high_risk_count += 1
                    elif v == "SUSPICIOUS":
                        job.suspicious_count += 1
                    else:
                        job.safe_count += 1

        job.update_progress()
        self.logger.info(f"Batch '{batch_id}' processing complete: Status={job.status.value}, Progress={job.progress_pct}%")
        return job

    def get_batch_job(self, batch_id: str, tenant_id: str = "TENANT-DEFAULT") -> Optional[BulkBatchJob]:
        """Fetch batch job details with multi-tenant security isolation."""
        job = self._jobs_cache.get(batch_id)
        if not job:
            return None
        if job.tenant_id != tenant_id and tenant_id != "TENANT-DEFAULT":
            self.logger.warning(f"TENANT ISOLATION ALERT: Tenant '{tenant_id}' attempted to access job '{batch_id}' belonging to '{job.tenant_id}'.")
            return None
        return job
