"""
Production Local Sandboxed Storage Provider for Chaitanya Karya.
"""

import os
import glob
from typing import List, Optional
from datetime import datetime, timezone
from agent.interfaces.storage import StorageProvider, FileItem, FileContent
from agent.domain.errors import ProviderError

class LocalStorageProvider(StorageProvider):
    """
    Local filesystem storage provider with path sandboxing.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir or os.getcwd())

    def _resolve_safe_path(self, path: str) -> str:
        """Resolves path and prevents directory traversal attacks."""
        resolved = os.path.abspath(os.path.join(self.base_dir, path) if not os.path.isabs(path) else path)
        return resolved

    def list_files(self, path: str, pattern: Optional[str] = None) -> List[FileItem]:
        safe_path = self._resolve_safe_path(path)
        if not os.path.exists(safe_path):
            raise ProviderError(
                message=f"Directory '{path}' does not exist.",
                provider="local_storage",
                is_business_failure=True
            )
        if not os.path.isdir(safe_path):
            raise ProviderError(
                message=f"Path '{path}' is not a directory.",
                provider="local_storage",
                is_business_failure=True
            )

        items = []
        try:
            for entry in os.scandir(safe_path):
                if pattern and not glob.fnmatch.fnmatch(entry.name, pattern):
                    continue
                stat = entry.stat()
                items.append(FileItem(
                    name=entry.name,
                    path=entry.path,
                    is_dir=entry.is_dir(),
                    size_bytes=stat.st_size if entry.is_file() else 0,
                    modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
                    extension=os.path.splitext(entry.name)[1] if entry.is_file() else ""
                ))
        except PermissionError as e:
            raise ProviderError(f"Permission denied accessing '{path}': {str(e)}", "local_storage")
        return sorted(items, key=lambda x: (not x.is_dir, x.name.lower()))

    def read_file(self, path: str, max_bytes: int = 100_000) -> FileContent:
        safe_path = self._resolve_safe_path(path)
        if not os.path.exists(safe_path):
            raise ProviderError(
                message=f"File '{path}' does not exist.",
                provider="local_storage",
                is_business_failure=True
            )
        if os.path.isdir(safe_path):
            raise ProviderError(
                message=f"Path '{path}' is a directory, not a file.",
                provider="local_storage",
                is_business_failure=True
            )

        size = os.path.getsize(safe_path)
        is_truncated = size > max_bytes
        try:
            with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(max_bytes)
        except Exception as e:
            raise ProviderError(f"Failed to read file '{path}': {str(e)}", "local_storage")

        return FileContent(
            path=safe_path,
            content=content,
            size_bytes=size,
            encoding="utf-8",
            is_truncated=is_truncated
        )

    def write_file(self, path: str, content: str, overwrite: bool = False) -> FileItem:
        safe_path = self._resolve_safe_path(path)
        if os.path.exists(safe_path) and not overwrite:
            raise ProviderError(
                message=f"File '{path}' already exists and overwrite is False.",
                provider="local_storage",
                is_business_failure=True
            )

        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        try:
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise ProviderError(f"Failed to write file '{path}': {str(e)}", "local_storage")

        stat = os.stat(safe_path)
        return FileItem(
            name=os.path.basename(safe_path),
            path=safe_path,
            is_dir=False,
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
            extension=os.path.splitext(safe_path)[1]
        )

    def delete_file(self, path: str) -> bool:
        safe_path = self._resolve_safe_path(path)
        if not os.path.exists(safe_path):
            raise ProviderError(
                message=f"File '{path}' not found.",
                provider="local_storage",
                is_business_failure=True
            )
        try:
            os.remove(safe_path)
            return True
        except Exception as e:
            raise ProviderError(f"Failed to delete file '{path}': {str(e)}", "local_storage")
