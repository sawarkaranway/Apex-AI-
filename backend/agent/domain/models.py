"""
Runtime Domain Context Models for Chaitanya Karya Agent Runtime.
Django's AUTH_USER_MODEL remains the sole authority for user identity;
these models represent lightweight, immutable in-flight runtime execution contexts.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass(frozen=True)
class TaskContext:
    """In-flight runtime context of a task execution."""
    task_id: str
    user_id: int
    conversation_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass(frozen=True)
class StepContext:
    """In-flight runtime context of an execution step."""
    step_id: str
    task_id: str
    sequence_num: int
    tool_name: str
    idempotency_key: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass(frozen=True)
class SanitizedOutput:
    """Safe, sanitized representation of tool output for LLM prompts and UI logs."""
    summary: str
    is_truncated: bool = False
    character_count: int = 0
