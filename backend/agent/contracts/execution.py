"""
Step Execution Envelopes and Planning Contracts for Chaitanya Karya.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from agent.domain.enums import StepStatus, RiskLevel
from agent.contracts.tool import ToolResult

class StepExecutionPlan(BaseModel):
    """A proposed execution step planned by the LLM."""
    model_config = ConfigDict(frozen=True)

    sequence_num: int
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    rationale: Optional[str] = ""

class StepExecutionState(BaseModel):
    """The current state and history of an execution step."""
    step_id: str
    task_id: str
    sequence_num: int
    tool_name: str
    arguments: Dict[str, Any]
    status: StepStatus = StepStatus.PLANNED
    risk_level: RiskLevel = RiskLevel.LOW
    idempotency_key: str
    result: Optional[ToolResult[Any]] = None
