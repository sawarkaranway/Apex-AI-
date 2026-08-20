"""
Comprehensive Phase 0 Invariant & Contract Test Suite for Chaitanya Karya.
Verifies all domain rules, state machine transitions, locks, idempotency, policy gates, and cryptography.
"""

import pytest
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chaitanya_backend.settings')
django.setup()

from datetime import datetime, timezone, timedelta
from cryptography.exceptions import InvalidTag

from agent.domain.enums import StepStatus, RiskLevel, ToolExecutionStatus, FailureCategory
from agent.domain.errors import (
    StateTransitionError,
    ExecutionLockedError,
    SchemaValidationError,
    PolicyViolationError,
    ProviderError
)
from agent.contracts.tool import ToolResult
from agent.contracts.execution import StepExecutionState
from agent.contracts.observations import ObservationFormatter
from agent.policy.engine import policy_engine
from agent.runtime.transitions import validate_step_transition
from agent.runtime.locks import step_lock_manager
from agent.runtime.idempotency import (
    generate_canonical_idempotency_key,
    idempotency_claim_manager
)
from agent.runtime.state_machine import StepLifecycleManager
from agent.runtime.executor import step_executor
from agent.vault import CredentialVault
from agent.tools.calendar_tools import (
    CalendarCreateEventInput,
    calendar_create_event_handler
)
from agent.tools.storage_tools import (
    WriteFileInput,
    ReadFileInput,
    write_file_handler,
    read_file_handler
)

# ══════════════════════════════════════════════════════════════
# 1. State Machine & Lifecycle Invariant Tests
# ══════════════════════════════════════════════════════════════

def test_legal_step_state_transitions():
    """Verifies that strictly allowed step state transitions succeed."""
    # PLANNED -> POLICY_CHECK
    validate_step_transition(StepStatus.PLANNED, StepStatus.POLICY_CHECK)
    # POLICY_CHECK -> AWAITING_APPROVAL
    validate_step_transition(StepStatus.POLICY_CHECK, StepStatus.AWAITING_APPROVAL)
    # AWAITING_APPROVAL -> APPROVED
    validate_step_transition(StepStatus.AWAITING_APPROVAL, StepStatus.APPROVED)
    # APPROVED -> EXECUTING
    validate_step_transition(StepStatus.APPROVED, StepStatus.EXECUTING)
    # EXECUTING -> COMPLETED
    validate_step_transition(StepStatus.EXECUTING, StepStatus.COMPLETED)

def test_illegal_step_state_transitions_raise_error():
    """Verifies that invalid transitions raise StateTransitionError."""
    with pytest.raises(StateTransitionError) as exc_info:
        validate_step_transition(StepStatus.PLANNED, StepStatus.COMPLETED)
    assert exc_info.value.category == FailureCategory.SYSTEM_ERROR

    with pytest.raises(StateTransitionError):
        validate_step_transition(StepStatus.EXECUTING, StepStatus.PLANNED)

    with pytest.raises(StateTransitionError):
        validate_step_transition(StepStatus.COMPLETED, StepStatus.EXECUTING)

def test_argument_mutation_resets_state_to_policy_check():
    """Verifies that modifying arguments in AWAITING_APPROVAL resets state to POLICY_CHECK."""
    initial_args = {"title": "Initial Sync", "start_time": "2026-08-20T10:00:00Z"}
    step_state = StepExecutionState(
        step_id="step-101",
        task_id="task-1",
        sequence_num=1,
        tool_name="calendar_create_event",
        arguments=initial_args,
        status=StepStatus.AWAITING_APPROVAL,
        risk_level=RiskLevel.HIGH,
        idempotency_key="initial-key"
    )
    lifecycle = StepLifecycleManager(step_state, user_id=1)

    new_args = {"title": "Updated Strategy Sync", "start_time": "2026-08-20T11:00:00Z"}
    lifecycle.mutate_arguments(new_args)

    assert step_state.status == StepStatus.POLICY_CHECK
    assert step_state.arguments == new_args
    assert step_state.idempotency_key != "initial-key"

def test_argument_mutation_blocked_during_execution():
    """Verifies that modifying arguments while EXECUTING raises ExecutionLockedError."""
    step_state = StepExecutionState(
        step_id="step-102",
        task_id="task-1",
        sequence_num=1,
        tool_name="calendar_create_event",
        arguments={"title": "Test"},
        status=StepStatus.EXECUTING,
        risk_level=RiskLevel.LOW,
        idempotency_key="key-102"
    )
    lifecycle = StepLifecycleManager(step_state, user_id=1)

    with pytest.raises(ExecutionLockedError):
        lifecycle.mutate_arguments({"title": "Changed Mid-Flight"})

# ══════════════════════════════════════════════════════════════
# 2. Execution Lock Invariant Tests
# ══════════════════════════════════════════════════════════════

def test_step_lock_acquisition_and_release():
    step_id = "step-lock-test"
    assert step_lock_manager.acquire_lock(step_id) is True
    # Duplicate acquisition fails
    assert step_lock_manager.acquire_lock(step_id) is False
    assert step_lock_manager.is_locked(step_id) is True

    step_lock_manager.release_lock(step_id)
    assert step_lock_manager.is_locked(step_id) is False
    assert step_lock_manager.acquire_lock(step_id) is True
    step_lock_manager.release_lock(step_id)

# ══════════════════════════════════════════════════════════════
# 3. Canonical Idempotency Key Tests
# ══════════════════════════════════════════════════════════════

def test_canonical_idempotency_key_order_independence():
    """Verifies that dictionaries with different key orders generate the exact same hash."""
    args_1 = {"title": "Sync", "attendees": ["a@b.com", "c@d.com"], "priority": 1}
    args_2 = {"priority": 1, "title": "Sync", "attendees": ["a@b.com", "c@d.com"]}

    key_1 = generate_canonical_idempotency_key("calendar_create_event", args_1, "task-1", 1)
    key_2 = generate_canonical_idempotency_key("calendar_create_event", args_2, "task-1", 1)

    assert key_1 == key_2

# ══════════════════════════════════════════════════════════════
# 4. Policy Engine Authority Tests
# ══════════════════════════════════════════════════════════════

def test_policy_evaluates_high_risk_actions_for_approval():
    res = policy_engine.evaluate("gmail_send", {"to": ["board@corp.com"], "subject": "Financials"})
    assert res.risk_level == RiskLevel.HIGH
    assert res.requires_approval is True
    assert res.allowed is True

def test_policy_denies_root_system_deletion():
    res = policy_engine.evaluate("delete_file", {"file_path": "C:\\Windows"})
    assert res.allowed is False
    assert res.risk_level == RiskLevel.CRITICAL
    assert "strictly prohibited" in (res.denial_reason or "")

# ══════════════════════════════════════════════════════════════
# 5. Pipeline Execution & Typed Failure Categorization Tests
# ══════════════════════════════════════════════════════════════

def test_executor_validation_failure():
    """Passing invalid arguments categorizes failure as VALIDATION_FAILURE."""
    invalid_args = {"start_time": "not-a-datetime"}  # missing title, invalid datetime
    result = step_executor.execute_step(
        tool_name="calendar_create_event",
        raw_arguments=invalid_args,
        schema_cls=CalendarCreateEventInput,
        handler_func=calendar_create_event_handler,
        task_id="task-1",
        step_id="step-val-1",
        user_id=1
    )
    assert result.status == ToolExecutionStatus.FAILURE
    assert result.failure_category == FailureCategory.VALIDATION_FAILURE
    assert "SCHEMA_VALIDATION_ERROR" in result.error_code

def test_executor_business_failure():
    """Passing start_time >= end_time categorizes failure as BUSINESS_FAILURE."""
    now = datetime.now(timezone.utc)
    args = {
        "title": "Invalid Meeting",
        "start_time": now + timedelta(hours=2),
        "end_time": now + timedelta(hours=1),  # Invalid: end before start
    }
    result = step_executor.execute_step(
        tool_name="calendar_create_event",
        raw_arguments=args,
        schema_cls=CalendarCreateEventInput,
        handler_func=calendar_create_event_handler,
        task_id="task-1",
        step_id="step-biz-1",
        user_id=1
    )
    assert result.status == ToolExecutionStatus.FAILURE
    assert result.failure_category == FailureCategory.BUSINESS_FAILURE
    assert "End time must be after start time" in result.error_message

def test_executor_successful_run():
    """Valid arguments execute successfully and yield clean ToolResult."""
    now = datetime.now(timezone.utc)
    args = {
        "title": "Executive Review",
        "start_time": now + timedelta(hours=1),
        "end_time": now + timedelta(hours=2),
        "attendees": ["test@example.com"]
    }
    result = step_executor.execute_step(
        tool_name="calendar_create_event",
        raw_arguments=args,
        schema_cls=CalendarCreateEventInput,
        handler_func=calendar_create_event_handler,
        task_id="task-1",
        step_id="step-success-1",
        user_id=1,
        skip_policy_check=True
    )
    assert result.status == ToolExecutionStatus.SUCCESS
    assert result.data is not None
    assert result.data.title == "Executive Review"
    assert "Executive Review" in result.sanitized_summary

# ══════════════════════════════════════════════════════════════
# 6. Observation Formatter Token Leaking Safety
# ══════════════════════════════════════════════════════════════

def test_observation_formatter_sanitization():
    result = ToolResult.success(
        tool_name="test_tool",
        execution_id="exec-1",
        step_id="step-1",
        idempotency_key="idem-1",
        data={"token": "SECRET_BEARER_TOKEN_DO_NOT_LEAK"},
        sanitized_summary="Resource listed successfully: 3 items found.",
        debug_payload={"raw_headers": {"Authorization": "Bearer secret"}}
    )
    obs = ObservationFormatter.format_observation(result)
    assert "SECRET_BEARER_TOKEN_DO_NOT_LEAK" not in obs
    assert "Authorization" not in obs
    assert "3 items found" in obs

# ══════════════════════════════════════════════════════════════
# 7. AES-256-GCM Credential Vault Tests
# ══════════════════════════════════════════════════════════════

def test_credential_vault_encryption_decryption():
    master_key = os.urandom(32)
    vault = CredentialVault(master_key)

    secret = {"access_token": "ya29.a0AfH6SMB...", "refresh_token": "1//04..."}
    aad = CredentialVault.construct_aad(user_id=42, provider_id="google")

    encrypted_json = vault.encrypt_secret(secret, associated_data=aad)
    decrypted = vault.decrypt_secret(encrypted_json, expected_associated_data=aad)

    assert decrypted == secret

def test_credential_vault_tamper_detection():
    master_key = os.urandom(32)
    vault = CredentialVault(master_key)
    secret = {"token": "secret123"}
    aad = CredentialVault.construct_aad(user_id=1, provider_id="google")

    encrypted_json = vault.encrypt_secret(secret, associated_data=aad)

    # Tampered AAD (e.g. wrong user trying to decrypt)
    wrong_aad = CredentialVault.construct_aad(user_id=99, provider_id="google")
    with pytest.raises(InvalidTag):
        vault.decrypt_secret(encrypted_json, expected_associated_data=wrong_aad)

def test_credential_vault_from_passphrase():
    passphrase = "UltraSecureExecutivePassphrase!2026"
    salt = os.urandom(16)
    vault1 = CredentialVault.from_passphrase(passphrase, salt, iterations=10_000)
    vault2 = CredentialVault.from_passphrase(passphrase, salt, iterations=10_000)

    secret = {"api_key": "sk-proj-xyz"}
    aad = "user:1:provider:openai"
    encrypted = vault1.encrypt_secret(secret, aad)
    decrypted = vault2.decrypt_secret(encrypted, aad)
    assert decrypted == secret
