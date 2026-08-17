"""
SECUROXI AI Local Scan Queue
Durable SQLite-backed queue tracking batch and file synchronization state.
Guarantees crash recovery, resumable processing, and zero state loss.
"""

import sqlite3
import os
import time
import uuid
from typing import List, Dict, Any, Optional
from enum import Enum


class QueueItemState(str, Enum):
    QUEUED = "QUEUED"
    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"


class LocalScanQueue:
    """Manages local scanner queue state in a durable SQLite database."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.expanduser("~/.securoxi/agent_queue.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scan_batches (
                    batch_id TEXT PRIMARY KEY,
                    folder_path TEXT NOT NULL,
                    folder_name TEXT NOT NULL,
                    total_files INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queue_items (
                    item_id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    remote_scan_id TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (batch_id) REFERENCES scan_batches(batch_id)
                )
            """)
            conn.commit()

    def create_batch(self, folder_path: str, files: List[Dict[str, Any]]) -> str:
        batch_id = f"BATCH-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        folder_name = os.path.basename(os.path.abspath(folder_path))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scan_batches (batch_id, folder_path, folder_name, total_files, status)
                VALUES (?, ?, ?, ?, 'QUEUED')
            """, (batch_id, folder_path, folder_name, len(files)))

            for f in files:
                item_id = f"ITEM-{uuid.uuid4().hex[:8]}"
                state = QueueItemState.SKIPPED_DUPLICATE.value if f.get("is_duplicate") else QueueItemState.QUEUED.value
                cursor.execute("""
                    INSERT INTO queue_items
                    (item_id, batch_id, file_path, relative_path, file_name, sha256_hash, size_bytes, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_id,
                    batch_id,
                    f["file_path"],
                    f.get("relative_path", f["file_name"]),
                    f["file_name"],
                    f.get("sha256_hash", ""),
                    f.get("size_bytes", 0),
                    state
                ))
            conn.commit()

        return batch_id

    def get_pending_items(self, batch_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT item_id, batch_id, file_path, relative_path, file_name, sha256_hash, size_bytes, state
                FROM queue_items
                WHERE batch_id = ? AND state = 'QUEUED'
                ORDER BY created_at ASC
                LIMIT ?
            """, (batch_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def update_item_state(self, item_id: str, state: QueueItemState, remote_scan_id: Optional[str] = None, error: Optional[str] = None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE queue_items
                SET state = ?, remote_scan_id = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE item_id = ?
            """, (state.value, remote_scan_id, error, item_id))
            conn.commit()

    def update_batch_status(self, batch_id: str, status: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE scan_batches
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE batch_id = ?
            """, (status, batch_id))
            conn.commit()

    def get_batch_progress(self, batch_id: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scan_batches WHERE batch_id = ?", (batch_id,))
            batch = cursor.fetchone()
            if not batch:
                return {}

            cursor.execute("""
                SELECT state, COUNT(*) as count
                FROM queue_items
                WHERE batch_id = ?
                GROUP BY state
            """, (batch_id,))
            counts = {row["state"]: row["count"] for row in cursor.fetchall()}

            return {
                "batch_id": batch_id,
                "folder_name": batch["folder_name"],
                "total_files": batch["total_files"],
                "status": batch["status"],
                "completed": counts.get(QueueItemState.COMPLETED.value, 0),
                "queued": counts.get(QueueItemState.QUEUED.value, 0),
                "uploading": counts.get(QueueItemState.UPLOADING.value, 0),
                "failed": counts.get(QueueItemState.FAILED.value, 0),
                "duplicates_skipped": counts.get(QueueItemState.SKIPPED_DUPLICATE.value, 0),
            }
