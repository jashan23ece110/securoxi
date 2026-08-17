"""
SECUROXI AI Local Folder Desktop Scanner & Enterprise Agent
Provides native read-only folder discovery, local content hashing & deduplication,
durable SQLite queue management, and resilient batched cloud synchronization.
"""

from securoxi.agent.folder_scanner import LocalFolderScanner, DiscoveredFile
from securoxi.agent.local_queue import LocalScanQueue, QueueItemState
from securoxi.agent.uploader import AgentUploader

__all__ = [
    "LocalFolderScanner",
    "DiscoveredFile",
    "LocalScanQueue",
    "QueueItemState",
    "AgentUploader",
]
