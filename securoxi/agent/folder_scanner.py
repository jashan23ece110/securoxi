"""
SECUROXI AI Local Folder Scanner
Discovers files, validates extensions, checks symlink boundaries, and computes SHA-256 hashes.
Strictly read-only; never mutates or executes local files.
"""

import os
import hashlib
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from securoxi.logger import get_logger

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".rtf",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp"
}


@dataclass
class DiscoveredFile:
    """Represents a discovered local document."""
    file_path: str
    relative_path: str
    file_name: str
    extension: str
    size_bytes: int
    sha256_hash: str
    is_supported: bool
    is_duplicate: bool = False


class LocalFolderScanner:
    """
    Scans a local directory recursively, extracting file metadata and content hashes.
    Guarantees read-only access and safeguards against symlink loops.
    """

    def __init__(self, max_depth: int = 20, max_files: int = 50000):
        self.max_depth = max_depth
        self.max_files = max_files
        self.logger = get_logger("securoxi.agent.scanner")

    def _compute_sha256(self, file_path: str) -> str:
        """Streamingly computes SHA-256 hash of a file without loading entire file into memory."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to hash '{file_path}': {e}")
            return ""

    def discover_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Recursively discovers all documents in the target folder.
        Returns metadata summary and list of DiscoveredFile objects.
        """
        resolved_folder = os.path.realpath(os.path.abspath(folder_path))
        if not os.path.isdir(resolved_folder):
            raise ValueError(f"Invalid directory path: '{folder_path}'")

        discovered: List[DiscoveredFile] = []
        known_hashes: Set[str] = set()
        visited_real_paths: Set[str] = set()

        supported_count = 0
        unsupported_count = 0
        duplicate_count = 0
        total_bytes = 0

        for root, dirs, files in os.walk(resolved_folder, followlinks=False):
            # Calculate depth relative to root
            rel_root = os.path.relpath(root, resolved_folder)
            depth = 0 if rel_root == "." else len(rel_root.split(os.sep))
            if depth > self.max_depth:
                dirs.clear()
                continue

            for fname in files:
                if len(discovered) >= self.max_files:
                    self.logger.warning(f"Reached maximum file limit ({self.max_files}) during folder discovery.")
                    break

                full_path = os.path.join(root, fname)
                try:
                    real_path = os.path.realpath(full_path)
                except Exception:
                    real_path = full_path

                # Symlink breakout prevention: ensure real path resides within resolved_folder
                if not real_path.startswith(resolved_folder):
                    self.logger.warning(f"Symlink breakout detected and skipped: '{full_path}' -> '{real_path}'")
                    continue

                if real_path in visited_real_paths:
                    continue
                visited_real_paths.add(real_path)

                try:
                    stat = os.stat(full_path)
                    size = stat.st_size
                except Exception as e:
                    self.logger.warning(f"Could not stat file '{full_path}': {e}")
                    continue

                _, ext = os.path.splitext(fname)
                ext = ext.lower()
                is_supported = ext in SUPPORTED_EXTENSIONS
                rel_path = os.path.relpath(full_path, resolved_folder)

                sha256 = self._compute_sha256(full_path) if is_supported else ""
                is_dup = False
                if is_supported and sha256:
                    if sha256 in known_hashes:
                        is_dup = True
                        duplicate_count += 1
                    else:
                        known_hashes.add(sha256)

                if is_supported:
                    supported_count += 1
                else:
                    unsupported_count += 1

                total_bytes += size
                discovered.append(DiscoveredFile(
                    file_path=full_path,
                    relative_path=rel_path,
                    file_name=fname,
                    extension=ext,
                    size_bytes=size,
                    sha256_hash=sha256,
                    is_supported=is_supported,
                    is_duplicate=is_dup
                ))

        return {
            "folder_path": resolved_folder,
            "folder_name": os.path.basename(resolved_folder),
            "total_files": len(discovered),
            "supported_count": supported_count,
            "unsupported_count": unsupported_count,
            "duplicate_count": duplicate_count,
            "total_bytes": total_bytes,
            "files": discovered
        }
