"""
Observation Transformers for Chaitanya Karya.
Converts strongly typed ToolResult objects into clean, safe prompt observations.
"""

from typing import Any
from agent.contracts.tool import ToolResult
from agent.domain.enums import ToolExecutionStatus

class ObservationFormatter:
    """
    Transforms ToolResult into safe observation strings for next LLM planning turn.
    Prevents leaking raw debug tokens, huge unformatted payloads, or internal stack traces.
    """

    @staticmethod
    def format_observation(result: ToolResult[Any], max_length: int = 2000) -> str:
        if result.status == ToolExecutionStatus.SUCCESS:
            summary = result.sanitized_summary
            if len(summary) > max_length:
                summary = summary[:max_length] + "... [Output truncated for safety]"
            return f"Observation: [{result.tool_name}] (Status: SUCCESS)\nResult: {summary}"
        else:
            cat_name = result.failure_category.value if result.failure_category else "unknown"
            err_msg = result.error_message or "An unexpected error occurred."
            return f"Observation: [{result.tool_name}] (Status: FAILED, Category: {cat_name})\nError: {err_msg}"
