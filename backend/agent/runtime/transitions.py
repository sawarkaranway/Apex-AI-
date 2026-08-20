"""
Deterministic State Transitions for Chaitanya Karya.
Enforces legal step lifecycle transitions and invariant validations.
"""

from typing import Set, Dict
from agent.domain.enums import StepStatus
from agent.domain.errors import StateTransitionError

# Matrix of strictly allowed state transitions
ALLOWED_STEP_TRANSITIONS: Dict[StepStatus, Set[StepStatus]] = {
    StepStatus.PLANNED: {
        StepStatus.POLICY_CHECK,
        StepStatus.SKIPPED
    },
    StepStatus.POLICY_CHECK: {
        StepStatus.AWAITING_APPROVAL,
        StepStatus.EXECUTING,
        StepStatus.SKIPPED
    },
    StepStatus.AWAITING_APPROVAL: {
        StepStatus.APPROVED,
        StepStatus.REJECTED,
        StepStatus.POLICY_CHECK   # Re-evaluation trigger when user edits arguments
    },
    StepStatus.APPROVED: {
        StepStatus.EXECUTING,
        StepStatus.SKIPPED
    },
    StepStatus.REJECTED: {
        StepStatus.SKIPPED
    },
    StepStatus.EXECUTING: {
        StepStatus.COMPLETED,
        StepStatus.FAILED
    },
    StepStatus.COMPLETED: set(),  # Terminal state
    StepStatus.FAILED: {
        StepStatus.POLICY_CHECK   # Retry trigger
    },
    StepStatus.SKIPPED: set(),    # Terminal state
}

def validate_step_transition(current_status: StepStatus, next_status: StepStatus) -> None:
    """
    Validates if transitioning from current_status to next_status is legal.
    Raises StateTransitionError if the transition violates invariants.
    """
    allowed_targets = ALLOWED_STEP_TRANSITIONS.get(current_status, set())
    if next_status not in allowed_targets:
        raise StateTransitionError(
            from_state=current_status.value,
            to_state=next_status.value,
            details={
                "allowed_transitions": [s.value for s in allowed_targets]
            }
        )
