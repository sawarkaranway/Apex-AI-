"""
Canonical Idempotency & Claim Management for Chaitanya Karya.
"""

import json
import hashlib
import threading
from typing import Dict, Any, Optional, Tuple
from agent.domain.errors import IdempotencyConflictError
from agent.contracts.tool import ToolResult

def generate_canonical_idempotency_key(
    tool_name: str,
    arguments: Dict[str, Any],
    task_id: str,
    user_id: int
) -> str:
    """
    Generates a deterministic SHA-256 idempotency key from a canonical sorted representation of arguments.
    Independent of key insertion order.
    """
    # Canonical JSON string with sorted keys and trimmed whitespace
    canonical_payload = {
        "user_id": user_id,
        "task_id": task_id,
        "tool_name": tool_name,
        "arguments": arguments
    }
    canonical_json = json.dumps(canonical_payload, sort_keys=True, separators=(',', ':'), default=str)
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

class IdempotencyClaimManager:
    """
    Thread-safe / atomic idempotency claim manager.
    Atomically claims idempotency key before provider execution to prevent duplicate concurrent runs.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._in_flight: Dict[str, str] = {}  # idempotency_key -> step_id
        self._completed: Dict[str, ToolResult[Any]] = {}  # idempotency_key -> ToolResult

    def try_claim(self, idempotency_key: str, step_id: str) -> Tuple[bool, Optional[ToolResult[Any]]]:
        """
        Attempts to atomically claim an idempotency key.
        Returns:
            (True, None) -> Successfully claimed, proceed to execute.
            (False, cached_result) -> Already completed, return cached result.
            (False, None) -> Currently in-flight by another step; caller should handle conflict.
        """
        with self._lock:
            if idempotency_key in self._completed:
                return False, self._completed[idempotency_key]
            if idempotency_key in self._in_flight:
                return False, None
            
            self._in_flight[idempotency_key] = step_id
            return True, None

    def complete_claim(self, idempotency_key: str, result: ToolResult[Any]) -> None:
        """Mark idempotency claim as successfully completed with cached result."""
        with self._lock:
            self._in_flight.pop(idempotency_key, None)
            self._completed[idempotency_key] = result

    def release_claim(self, idempotency_key: str) -> None:
        """Release an in-flight claim on failure/abort."""
        with self._lock:
            self._in_flight.pop(idempotency_key, None)

idempotency_claim_manager = IdempotencyClaimManager()
