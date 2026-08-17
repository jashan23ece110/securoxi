"""
SECUROXI AI Phase 3 Stage 6 — Enterprise Cloud & Storage Connectors
Implements LocalFileConnector, ObjectStorageConnector (Mock S3/Blob), and CloudDriveConnector.
"""

import os
import uuid
import time
from typing import List, Dict, Any, Optional
from securoxi.connectors.base_connector import (
    BaseConnector, ConnectorConfig, ConnectorHealthStatus,
    NormalizedStorageEvent, StorageEventType
)
from securoxi.logger import get_logger


class LocalFileConnector(BaseConnector):
    """Local File & Directory Source Connector."""

    def __init__(self, watch_directory: str, config: Optional[ConnectorConfig] = None):
        cfg = config or ConnectorConfig(connector_id="CONN-LOCAL-DISK", source_type="LOCAL_DISK")
        super().__init__(cfg)
        self.watch_directory = watch_directory
        self.logger = get_logger("securoxi.connectors.local")

    def health_check(self) -> ConnectorHealthStatus:
        if os.path.exists(self.watch_directory):
            return ConnectorHealthStatus.HEALTHY
        return ConnectorHealthStatus.UNREACHABLE

    def discover_files(self) -> List[NormalizedStorageEvent]:
        events = []
        if not os.path.exists(self.watch_directory):
            return events

        for root, _, files in os.walk(self.watch_directory):
            for file in files:
                if file.endswith((".pdf", ".txt", ".docx", ".zip")):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "rb") as f:
                            content = f.read()
                        sha256 = self.compute_sha256(content)

                        events.append(NormalizedStorageEvent(
                            event_id=f"EVT-LOCAL-{uuid.uuid4().hex[:8]}",
                            event_type=StorageEventType.FILE_CREATED,
                            connector_id=self.config.connector_id,
                            source_type="LOCAL_DISK",
                            file_id=full_path,
                            filename=file,
                            content_hash_sha256=sha256,
                            file_size_bytes=len(content),
                            provenance_path=full_path
                        ))
                    except Exception as err:
                        self.logger.warning(f"Error reading file '{full_path}': {err}")

        return events

    def fetch_file_content(self, file_id: str) -> bytes:
        if not os.path.exists(file_id):
            raise FileNotFoundError(f"Inaccessible file path: '{file_id}'")
        with open(file_id, "rb") as f:
            return f.read()


class ObjectStorageConnector(BaseConnector):
    """Mock Enterprise S3 / Azure Blob Storage Connector."""

    def __init__(self, config: Optional[ConnectorConfig] = None):
        cfg = config or ConnectorConfig(connector_id="CONN-MOCK-S3", source_type="OBJECT_STORAGE")
        super().__init__(cfg)
        self.logger = get_logger("securoxi.connectors.s3")
        self.mock_bucket: Dict[str, bytes] = {}

    def health_check(self) -> ConnectorHealthStatus:
        if self.config.is_credentials_expired:
            return ConnectorHealthStatus.EXPIRED_CREDENTIALS
        return ConnectorHealthStatus.HEALTHY

    def add_mock_object(self, key: str, content: bytes):
        self.mock_bucket[key] = content

    def discover_files(self) -> List[NormalizedStorageEvent]:
        if self.health_check() == ConnectorHealthStatus.EXPIRED_CREDENTIALS:
            raise PermissionError("Connector credentials expired! Authentication failed.")

        events = []
        for key, content in self.mock_bucket.items():
            sha256 = self.compute_sha256(content)
            events.append(NormalizedStorageEvent(
                event_id=f"EVT-S3-{uuid.uuid4().hex[:8]}",
                event_type=StorageEventType.FILE_CREATED,
                connector_id=self.config.connector_id,
                source_type="OBJECT_STORAGE",
                file_id=key,
                filename=key,
                content_hash_sha256=sha256,
                file_size_bytes=len(content),
                provenance_path=f"s3://{self.config.bucket_name}/{key}"
            ))
        return events

    def fetch_file_content(self, file_id: str) -> bytes:
        if self.health_check() == ConnectorHealthStatus.EXPIRED_CREDENTIALS:
            raise PermissionError("Connector credentials expired!")
        if file_id not in self.mock_bucket:
            raise KeyError(f"Object '{file_id}' not found in S3 bucket.")
        return self.mock_bucket[file_id]


class CloudDriveConnector(BaseConnector):
    """Mock Google Drive / OneDrive Connector with Change Tracking."""

    def __init__(self, config: Optional[ConnectorConfig] = None):
        cfg = config or ConnectorConfig(connector_id="CONN-CLOUD-DRIVE", source_type="CLOUD_DRIVE")
        super().__init__(cfg)
        self.logger = get_logger("securoxi.connectors.drive")
        self.mock_files: Dict[str, Dict[str, Any]] = {}

    def health_check(self) -> ConnectorHealthStatus:
        return ConnectorHealthStatus.HEALTHY

    def upsert_drive_file(self, file_id: str, filename: str, content: bytes):
        self.mock_files[file_id] = {"filename": filename, "content": content, "status": "ACTIVE"}

    def delete_drive_file(self, file_id: str):
        if file_id in self.mock_files:
            self.mock_files[file_id]["status"] = "DELETED"

    def discover_files(self) -> List[NormalizedStorageEvent]:
        events = []
        for fid, fmeta in self.mock_files.items():
            ev_type = StorageEventType.FILE_DELETED if fmeta["status"] == "DELETED" else StorageEventType.FILE_CREATED
            content = fmeta["content"]
            sha256 = self.compute_sha256(content)

            events.append(NormalizedStorageEvent(
                event_id=f"EVT-DRIVE-{uuid.uuid4().hex[:8]}",
                event_type=ev_type,
                connector_id=self.config.connector_id,
                source_type="CLOUD_DRIVE",
                file_id=fid,
                filename=fmeta["filename"],
                content_hash_sha256=sha256,
                file_size_bytes=len(content),
                provenance_path=f"gdrive://{fid}"
            ))
        return events

    def fetch_file_content(self, file_id: str) -> bytes:
        if file_id not in self.mock_files or self.mock_files[file_id]["status"] == "DELETED":
            raise FileNotFoundError(f"Drive file '{file_id}' deleted or inaccessible.")
        return self.mock_files[file_id]["content"]
