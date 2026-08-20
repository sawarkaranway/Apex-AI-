"""
Provider-Agnostic Storage & Filesystem Interface for Chaitanya Karya.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class FileItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    path: str
    is_dir: bool
    size_bytes: int = 0
    modified_at: Optional[datetime] = None
    extension: Optional[str] = ""

class FileContent(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    content: str
    size_bytes: int
    encoding: str = "utf-8"
    is_truncated: bool = False

class StorageProvider(ABC):
    """
    Abstract Base Class for Storage Providers (Local Sandboxed FS, Google Drive, OneDrive).
    """

    @abstractmethod
    def list_files(self, path: str, pattern: Optional[str] = None) -> List[FileItem]:
        """List files and folders in directory."""
        pass

    @abstractmethod
    def read_file(self, path: str, max_bytes: int = 100_000) -> FileContent:
        """Read content from file path."""
        pass

    @abstractmethod
    def write_file(self, path: str, content: str, overwrite: bool = False) -> FileItem:
        """Write content to file path."""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Delete file at path. Returns True if deleted."""
        pass
