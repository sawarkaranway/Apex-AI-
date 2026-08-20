"""
Core Domain Enums for Chaitanya Karya Agent Runtime.
"""

from enum import Enum

class StepStatus(str, Enum):
    PLANNED = "planned"
    POLICY_CHECK = "policy_check"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ToolExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class FailureCategory(str, Enum):
    """
    Operationally distinct failure classes to ensure clear observability and error handling.
    """
    BUSINESS_FAILURE = "business_failure"       # Target not found, logic conflict, invalid business input
    POLICY_DENIAL = "policy_denial"             # Security policy blocked action, or user rejected
    AUTH_FAILURE = "auth_failure"               # Missing or invalid integration credentials/token
    VALIDATION_FAILURE = "validation_failure"   # Pydantic parameter schema validation failure
    PROVIDER_FAILURE = "provider_failure"       # 5xx, upstream timeout, rate-limited
    SYSTEM_ERROR = "system_error"               # Internal unhandled exceptions
