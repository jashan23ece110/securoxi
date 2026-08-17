"""
SECUROXI AI Phase 3 Stage 6 — Base Enterprise Data & Cloud Connector Interface
Defines provider-agnostic connector abstractions, health status, and normalized storage events.
"""

import time
import hashlib
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


class ConnectorHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    EXPIRED_CREDENTIALS = "EXPIRED_CREDENTIALS"
    UNREACHABLE = "UNREACHABLE"


class StorageEventType(str, Enum):
    FILE_CREATED = "FILE_CREATED"
    FILE_MODIFIED = "FILE_MODIFIED"
    FILE_DELETED = "FILE_DELETED"


@dataclass
class NormalizedStorageEvent:
    """Normalized file/object storage event produced by enterprise connectors."""
    event_id: str
    event_type: StorageEventType
    connector_id: str
    source_type: str  # "LOCAL_DISK", "OBJECT_STORAGE", "CLOUD_DRIVE"
    file_id: str
    filename: str
    content_hash_sha256: str
    file_size_bytes: int
    provenance_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "connector_id": self.connector_id,
            "source_type": self.source_type,
            "file_id": self.file_id,
            "filename": self.filename,
            "content_hash_sha256": self.content_hash_sha256,
            "file_size_bytes": self.file_size_bytes,
            "provenance_path": self.provenance_path,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class ConnectorConfig:
    """Configuration and isolated secrets for enterprise cloud connectors."""
    connector_id: str
    source_type: str
    access_key: str = "mock_access_key"
    secret_key: str = "mock_secret_key"
    endpoint_url: str = "https://storage.cloud-provider.com"
    bucket_name: str = "securoxi-enterprise-resumes"
    max_rate_per_sec: int = 100
    is_credentials_expired: bool = False


class BaseConnector(ABC):
    """Abstract Base Class for Enterprise Cloud & Storage Connectors."""

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._processed_content_hashes: set = set()  # Content SHA-256 deduplication store

    @abstractmethod
    def health_check(self) -> ConnectorHealthStatus:
        """Returns health status of the connector."""
        pass

    @abstractmethod
    def discover_files(self) -> List[NormalizedStorageEvent]:
        """Discovers new or modified files from storage source."""
        pass

    @abstractmethod
    def fetch_file_content(self, file_id: str) -> bytes:
        """Fetches raw bytes of a discovered file safely."""
        pass

    def compute_sha256(self, content_bytes: bytes) -> str:
        """Computes SHA-256 hash of raw file content bytes."""
        return hashlib.sha256(content_bytes).hexdigest()

    def is_duplicate_content(self, content_hash: str) -> bool:
        """Content deduplication: returns True if content SHA-256 has already been processed."""
        if content_hash in self._processed_content_hashes:
            return True
        self._processed_content_hashes.add(content_hash)
        return False
