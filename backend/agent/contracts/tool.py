"""
Typed Tool Contracts & Envelopes for Chaitanya Karya.
"""

from typing import Generic, TypeVar, Optional, Any, Dict, List, Callable, Type
from pydantic import BaseModel, Field, ConfigDict
from agent.domain.enums import ToolExecutionStatus, FailureCategory, RiskLevel

T = TypeVar("T")

class ToolResult(BaseModel, Generic[T]):
    """
    Standardized typed tool result envelope.
    Enforces isolation between clean sanitized prompt-safe summaries and raw debug payloads.
    """
    model_config = ConfigDict(frozen=True)

    tool_name: str
    execution_id: str
    step_id: str
    provider: Optional[str] = "local"
    status: ToolExecutionStatus
    failure_category: Optional[FailureCategory] = None
    data: Optional[T] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    idempotency_key: str
    side_effects: Dict[str, Any] = Field(default_factory=dict)
    sanitized_summary: str = Field(..., description="Safe, structured text representation for LLM and UI logs")
    debug_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Isolated debug payload for tracing; never injected indiscriminately into LLM context"
    )

    def is_successful(self) -> bool:
        return self.status == ToolExecutionStatus.SUCCESS

    @classmethod
    def success(
        cls,
        tool_name: str,
        execution_id: str,
        step_id: str,
        idempotency_key: str,
        data: T,
        sanitized_summary: str,
        provider: Optional[str] = "local",
        side_effects: Optional[Dict[str, Any]] = None,
        debug_payload: Optional[Dict[str, Any]] = None
    ) -> "ToolResult[T]":
        return cls(
            tool_name=tool_name,
            execution_id=execution_id,
            step_id=step_id,
            provider=provider,
            status=ToolExecutionStatus.SUCCESS,
            failure_category=None,
            data=data,
            idempotency_key=idempotency_key,
            side_effects=side_effects or {},
            sanitized_summary=sanitized_summary,
            debug_payload=debug_payload
        )

    @classmethod
    def failure(
        cls,
        tool_name: str,
        execution_id: str,
        step_id: str,
        idempotency_key: str,
        failure_category: FailureCategory,
        error_message: str,
        error_code: Optional[str] = None,
        sanitized_summary: Optional[str] = None,
        provider: Optional[str] = "local",
        debug_payload: Optional[Dict[str, Any]] = None
    ) -> "ToolResult[Any]":
        summary = sanitized_summary or f"Error in {tool_name} [{failure_category.value}]: {error_message}"
        return cls(
            tool_name=tool_name,
            execution_id=execution_id,
            step_id=step_id,
            provider=provider,
            status=ToolExecutionStatus.FAILURE,
            failure_category=failure_category,
            data=None,
            error_message=error_message,
            error_code=error_code or failure_category.name,
            idempotency_key=idempotency_key,
            side_effects={},
            sanitized_summary=summary,
            debug_payload=debug_payload
        )

class ToolDefinition(BaseModel):
    """Metadata schema defining a registered tool."""
    name: str
    display_name: str
    description: str
    risk_level: RiskLevel = RiskLevel.LOW
    input_schema: Type[BaseModel]
    handler: Any  # Callable returning ToolResult or typed object
