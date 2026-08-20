"""
Typed Storage & Local Filesystem Tools for Chaitanya Karya.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from agent.interfaces.storage import FileItem, FileContent
from agent.providers import default_storage_provider

class ListDirectoryInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    dir_path: str = Field(default=".", description="Path of directory to list")
    pattern: Optional[str] = Field(default=None, description="Optional filename wildcard pattern (e.g. '*.py')")

class ReadFileInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    file_path: str = Field(..., description="Path of file to read")
    max_bytes: int = Field(default=50_000, description="Max bytes to read")

class WriteFileInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    file_path: str = Field(..., description="Destination file path")
    content: str = Field(..., description="Content to write")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing file")

class DeleteFileInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    file_path: str = Field(..., description="File path to delete")

def list_directory_handler(args: ListDirectoryInput) -> List[FileItem]:
    return default_storage_provider.list_files(args.dir_path, args.pattern)

def read_file_handler(args: ReadFileInput) -> FileContent:
    return default_storage_provider.read_file(args.file_path, args.max_bytes)

def write_file_handler(args: WriteFileInput) -> FileItem:
    return default_storage_provider.write_file(args.file_path, args.content, args.overwrite)

def delete_file_handler(args: DeleteFileInput) -> bool:
    return default_storage_provider.delete_file(args.file_path)
