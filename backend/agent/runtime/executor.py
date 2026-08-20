"""
Pipeline Executor for Chaitanya Karya.
Enforces: Schema Validation -> Policy Gate -> Atomic Idempotency Claim -> Execution Lock -> Provider Execution -> Typed Result.
"""

from typing import Dict, Any, Type, Optional
from pydantic import BaseModel, ValidationError

from agent.domain.enums import StepStatus, RiskLevel, ToolExecutionStatus, FailureCategory
from agent.domain.errors import (
    SchemaValidationError,
    PolicyViolationError,
    ExecutionLockedError,
    AgentDomainError,
    ProviderError
)
from agent.contracts.tool import ToolResult
from agent.policy.engine import policy_engine
from agent.runtime.transitions import validate_step_transition
from agent.runtime.locks import step_lock_manager
from agent.runtime.idempotency import generate_canonical_idempotency_key, idempotency_claim_manager

class StepExecutor:
    """
    Deterministic Step Execution Coordinator.
    """

    @staticmethod
    def execute_step(
        tool_name: str,
        raw_arguments: Dict[str, Any],
        schema_cls: Type[BaseModel],
        handler_func: Any,
        task_id: str,
        step_id: str,
        user_id: int,
        provider_name: str = "local",
        skip_policy_check: bool = False
    ) -> ToolResult[Any]:
        # 1. Schema Validation (Pydantic)
        try:
            validated_model = schema_cls(**raw_arguments)
            validated_args = validated_model.model_dump()
        except ValidationError as val_err:
            idempotency_key = generate_canonical_idempotency_key(tool_name, raw_arguments, task_id, user_id)
            return ToolResult.failure(
                tool_name=tool_name,
                execution_id=task_id,
                step_id=step_id,
                idempotency_key=idempotency_key,
                failure_category=FailureCategory.VALIDATION_FAILURE,
                error_message=str(val_err),
                error_code="SCHEMA_VALIDATION_ERROR",
                provider=provider_name,
                debug_payload={"validation_errors": val_err.errors()}
            )

        # 2. Canonical Idempotency Key Generation
        idempotency_key = generate_canonical_idempotency_key(tool_name, validated_args, task_id, user_id)

        # 3. Policy Gate Evaluation
        if not skip_policy_check:
            policy_result = policy_engine.evaluate(tool_name, validated_args)
            if not policy_result.allowed:
                return ToolResult.failure(
                    tool_name=tool_name,
                    execution_id=task_id,
                    step_id=step_id,
                    idempotency_key=idempotency_key,
                    failure_category=FailureCategory.POLICY_DENIAL,
                    error_message=policy_result.denial_reason or "Action prohibited by security policy.",
                    error_code="POLICY_DENIAL",
                    provider=provider_name
                )

        # 4. Atomic Idempotency Claim
        claimed, cached_result = idempotency_claim_manager.try_claim(idempotency_key, step_id)
        if not claimed and cached_result is not None:
            return cached_result
        elif not claimed:
            # In-flight conflict
            return ToolResult.failure(
                tool_name=tool_name,
                execution_id=task_id,
                step_id=step_id,
                idempotency_key=idempotency_key,
                failure_category=FailureCategory.BUSINESS_FAILURE,
                error_message=f"Duplicate in-flight execution detected for step {step_id}.",
                error_code="IDEMPOTENCY_IN_FLIGHT_CONFLICT",
                provider=provider_name
            )

        # 5. Acquire Step Execution Lock
        if not step_lock_manager.acquire_lock(step_id):
            idempotency_claim_manager.release_claim(idempotency_key)
            return ToolResult.failure(
                tool_name=tool_name,
                execution_id=task_id,
                step_id=step_id,
                idempotency_key=idempotency_key,
                failure_category=FailureCategory.SYSTEM_ERROR,
                error_message="Could not acquire execution lock for step.",
                error_code="LOCK_ACQUISITION_FAILED",
                provider=provider_name
            )

        # 6. Provider Dispatch
        try:
            import inspect
            sig = inspect.signature(handler_func)
            if "user_id" in sig.parameters:
                execution_output = handler_func(validated_model, user_id=user_id)
            else:
                execution_output = handler_func(validated_model)
            
            # Format clean sanitized summary
            if isinstance(execution_output, str):
                summary = execution_output
            elif hasattr(execution_output, "model_dump_json"):
                summary = execution_output.model_dump_json()
            else:
                summary = str(execution_output)

            result = ToolResult.success(
                tool_name=tool_name,
                execution_id=task_id,
                step_id=step_id,
                idempotency_key=idempotency_key,
                data=execution_output,
                sanitized_summary=summary,
                provider=provider_name
            )
            idempotency_claim_manager.complete_claim(idempotency_key, result)
            return result

        except ProviderError as p_err:
            idempotency_claim_manager.release_claim(idempotency_key)
            return ToolResult.failure(
                tool_name=tool_name,
                execution_id=task_id,
                step_id=step_id,
                idempotency_key=idempotency_key,
                failure_category=p_err.category,
                error_message=p_err.message,
                error_code=p_err.code,
                provider=provider_name,
                debug_payload=p_err.details
            )
        except Exception as ex:
            idempotency_claim_manager.release_claim(idempotency_key)
            return ToolResult.failure(
                tool_name=tool_name,
                execution_id=task_id,
                step_id=step_id,
                idempotency_key=idempotency_key,
                failure_category=FailureCategory.SYSTEM_ERROR,
                error_message=f"Unhandled internal error during execution: {str(ex)}",
                error_code="UNHANDLED_EXCEPTION",
                provider=provider_name
            )
        finally:
            step_lock_manager.release_lock(step_id)

step_executor = StepExecutor()
