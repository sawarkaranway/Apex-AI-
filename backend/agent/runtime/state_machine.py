"""
Structured State Machine Runtime for Chaitanya Karya.
Coordinates step transitions, policy checks, approval pauses, execution, and observations.
"""

from typing import Dict, Any, List, Optional
from agent.domain.enums import StepStatus, TaskStatus, RiskLevel
from agent.domain.errors import StateTransitionError, ExecutionLockedError
from agent.contracts.tool import ToolResult
from agent.contracts.execution import StepExecutionState
from agent.contracts.observations import ObservationFormatter
from agent.policy.engine import policy_engine
from agent.runtime.transitions import validate_step_transition
from agent.runtime.locks import step_lock_manager
from agent.runtime.idempotency import generate_canonical_idempotency_key

class StepLifecycleManager:
    """
    Manages state progression and invariant checks for a single execution step.
    """

    def __init__(self, step_state: StepExecutionState, user_id: int):
        self.state = step_state
        self.user_id = user_id

    def transition_to(self, target_status: StepStatus) -> None:
        """Enforces deterministic state transition rule."""
        validate_step_transition(self.state.status, target_status)
        self.state.status = target_status

    def mutate_arguments(self, new_arguments: Dict[str, Any]) -> None:
        """
        Allows editing arguments ONLY when in PLANNED or AWAITING_APPROVAL state.
        Automatically resets state to POLICY_CHECK and recomputes canonical idempotency key.
        """
        step_lock_manager.assert_can_modify_arguments(self.state.step_id, self.state.status)
        
        # Invariant: mutation resets state to POLICY_CHECK
        self.transition_to(StepStatus.POLICY_CHECK)
        self.state.arguments = new_arguments
        self.state.idempotency_key = generate_canonical_idempotency_key(
            self.state.tool_name,
            new_arguments,
            self.state.task_id,
            self.user_id
        )
