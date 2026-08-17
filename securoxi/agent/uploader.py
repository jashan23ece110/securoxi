"""
SECUROXI AI Agent Uploader
Performs batched, authenticated, resilient uploads to the SECUROXI API.
Enforces retry backoff, tenant scoping, and batch tracking.
"""

import os
import time
import requests
from typing import Dict, Any, Optional, List
from securoxi.logger import get_logger
from securoxi.agent.local_queue import LocalScanQueue, QueueItemState


class AgentUploader:
    """Manages secure HTTP/TLS file uploads from local queue to SECUROXI server."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = "securoxi-enterprise-key",
        tenant_id: str = "TENANT-DEFAULT",
        queue: Optional[LocalScanQueue] = None,
        batch_size: int = 50,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.queue = queue or LocalScanQueue()
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.logger = get_logger("securoxi.agent.uploader")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "X-Tenant-ID": self.tenant_id,
            "User-Agent": "SECUROXI-Desktop-Agent/1.0"
        }

    def upload_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Uploads a single document file to the SECUROXI scan API."""
        file_path = item["file_path"]
        if not os.path.exists(file_path):
            self.queue.update_item_state(item["item_id"], QueueItemState.FAILED, error="File not found locally")
            return {"status": "error", "error": "File not found"}

        self.queue.update_item_state(item["item_id"], QueueItemState.UPLOADING)

        endpoint = f"{self.base_url}/api/v1/scans/upload"
        headers = self._get_headers()

        for attempt in range(1, self.max_retries + 1):
            try:
                with open(file_path, "rb") as f:
                    files = {"file": (item["file_name"], f)}
                    data = {"batch_id": item["batch_id"]}
                    res = requests.post(endpoint, headers=headers, files=files, data=data, timeout=30)

                if res.status_code == 200:
                    resp_data = res.json()
                    scan_id = resp_data.get("scan_id", "")
                    self.queue.update_item_state(item["item_id"], QueueItemState.COMPLETED, remote_scan_id=scan_id)
                    return {"status": "success", "scan_id": scan_id}
                else:
                    self.logger.warning(f"Upload attempt {attempt} failed with HTTP {res.status_code}: {res.text}")

            except Exception as e:
                self.logger.warning(f"Upload attempt {attempt} encountered error: {e}")

            time.sleep(0.5 * (2 ** (attempt - 1)))  # Exponential backoff

        self.queue.update_item_state(item["item_id"], QueueItemState.FAILED, error="Max retries exceeded")
        return {"status": "failed", "error": "Max retries exceeded"}

    def process_batch(self, batch_id: str, max_items: Optional[int] = None) -> Dict[str, Any]:
        """Processes pending items for a batch in chunks."""
        self.queue.update_batch_status(batch_id, "PROCESSING")
        processed_count = 0

        while True:
            pending = self.queue.get_pending_items(batch_id, limit=self.batch_size)
            if not pending:
                break

            for item in pending:
                self.upload_item(item)
                processed_count += 1
                if max_items and processed_count >= max_items:
                    break

            if max_items and processed_count >= max_items:
                break

        progress = self.queue.get_batch_progress(batch_id)
        if progress.get("queued", 0) == 0 and progress.get("uploading", 0) == 0:
            self.queue.update_batch_status(batch_id, "COMPLETED")

        return progress
