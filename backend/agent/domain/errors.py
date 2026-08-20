"""
Typed Domain Exceptions for Chaitanya Karya Agent Runtime.
"""

from typing import Optional, Any, Dict
from .enums import FailureCategory

class AgentDomainError(Exception):
    """Base exception for all agent domain errors."""
    def __init__(
        self,
        message: str,
        category: FailureCategory = FailureCategory.SYSTEM_ERROR,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.code = code or self.__class__.__name__
        self.details = details or {}

class PolicyViolationError(AgentDomainError):
    """Raised when policy engine denies execution of a step."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, FailureCategory.POLICY_DENIAL, "POLICY_VIOLATION", details)

class AuthenticationRequiredError(AgentDomainError):
    """Raised when provider integration credentials/token are missing or invalid."""
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        d = details or {}
        d["provider"] = provider
        super().__init__(message, FailureCategory.AUTH_FAILURE, "AUTH_REQUIRED", d)

class SchemaValidationError(AgentDomainError):
    """Raised when tool arguments fail Pydantic schema validation."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, FailureCategory.VALIDATION_FAILURE, "SCHEMA_VALIDATION_ERROR", details)

class ProviderError(AgentDomainError):
    """Raised when an external or local provider encounters an operational error."""
    def __init__(self, message: str, provider: str, is_business_failure: bool = False, details: Optional[Dict[str, Any]] = None):
        cat = FailureCategory.BUSINESS_FAILURE if is_business_failure else FailureCategory.PROVIDER_FAILURE
        d = details or {}
        d["provider"] = provider
        super().__init__(message, cat, "PROVIDER_ERROR", d)

class StateTransitionError(AgentDomainError):
    """Raised on invalid step/task state transitions."""
    def __init__(self, from_state: str, to_state: str, details: Optional[Dict[str, Any]] = None):
        msg = f"Illegal state transition from '{from_state}' to '{to_state}'."
        d = details or {}
        d.update({"from_state": from_state, "to_state": to_state})
        super().__init__(msg, FailureCategory.SYSTEM_ERROR, "ILLEGAL_STATE_TRANSITION", d)

class ExecutionLockedError(AgentDomainError):
    """Raised when attempting to modify arguments of an already executing or locked step."""
    def __init__(self, step_id: str, details: Optional[Dict[str, Any]] = None):
        msg = f"Step '{step_id}' is locked in execution and arguments cannot be modified."
        d = details or {}
        d["step_id"] = step_id
        super().__init__(msg, FailureCategory.SYSTEM_ERROR, "EXECUTION_LOCKED", d)

class IdempotencyConflictError(AgentDomainError):
    """Raised when an idempotency conflict or duplicate in-flight execution is detected."""
    def __init__(self, idempotency_key: str, details: Optional[Dict[str, Any]] = None):
        msg = f"Idempotency key conflict for key '{idempotency_key}'."
        d = details or {}
        d["idempotency_key"] = idempotency_key
        super().__init__(msg, FailureCategory.BUSINESS_FAILURE, "IDEMPOTENCY_CONFLICT", d)
