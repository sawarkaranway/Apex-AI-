"""
Step Execution Locks for Chaitanya Karya.
Enforces write-locking on execution steps to prevent race conditions or argument mutations.
"""

import threading
from typing import Set, Dict
from agent.domain.errors import ExecutionLockedError
from agent.domain.enums import StepStatus

class StepLockManager:
    """
    In-memory / thread-safe execution lock manager.
    Guarantees that once a step is executing, its arguments cannot be mutated.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._active_locks: Set[str] = set()

    def acquire_lock(self, step_id: str) -> bool:
        """Acquire execution lock for a step. Returns True if acquired, False if already locked."""
        with self._lock:
            if step_id in self._active_locks:
                return False
            self._active_locks.add(step_id)
            return True

    def release_lock(self, step_id: str) -> None:
        """Release execution lock for a step."""
        with self._lock:
            self._active_locks.discard(step_id)

    def is_locked(self, step_id: str) -> bool:
        with self._lock:
            return step_id in self._active_locks

    def assert_can_modify_arguments(self, step_id: str, current_status: StepStatus) -> None:
        """
        Ensures that step arguments can only be modified in mutable states (PLANNED, AWAITING_APPROVAL).
        Raises ExecutionLockedError if step is locked or in EXECUTING/terminal status.
        """
        if self.is_locked(step_id) or current_status in [
            StepStatus.EXECUTING,
            StepStatus.APPROVED,
            StepStatus.COMPLETED,
            StepStatus.SKIPPED
        ]:
            raise ExecutionLockedError(
                step_id=step_id,
                details={
                    "current_status": current_status.value,
                    "is_locked": self.is_locked(step_id)
                }
            )

step_lock_manager = StepLockManager()
