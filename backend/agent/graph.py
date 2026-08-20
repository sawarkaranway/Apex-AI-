"""
Structured Agent Runtime Engine.
Node-based State Machine: Request -> Intent/Goal -> Plan -> Policy -> Execute -> Observe -> Re-plan -> Complete.
Persists state into TaskExecution, ExecutionStep, ApprovalRequest, and TaskEvent records.
"""

import os
import re
import json
import hashlib
import uuid
import datetime
from typing import Dict, List, Any, Generator, Tuple, Optional

from .policy import evaluate_tool_risk
from .registry import registry
from .llm import get_llm_client, LLMResponse, ToolCall
from .memory import memory_system

def compute_idempotency_key(tool_name: str, task_id: str, args: Dict[str, Any]) -> str:
    """Generates sha256 idempotency key: sha256(tool_name + task_id + sorted_args)."""
    raw_str = f"{tool_name}:{task_id}:{json.dumps(args, sort_keys=True)}"
    return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

class LangGraphAgentRuntime:
    MAX_ITERATIONS = 10
    MAX_TOOL_CALLS = 15
    
    def process_turn(
        self,
        user_prompt: str,
        conversation_id: str,
        task_id: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Executes turn through structured state machine, persisting steps, emitting SSE events.
        """
        from api.models import Conversation, Message, TaskExecution, ExecutionStep, ApprovalRequest, TaskEvent

        # 1. Get or create Conversation & TaskExecution
        conv = Conversation.objects.filter(id=conversation_id).first()
        if not conv:
            conv = Conversation.objects.create(id=conversation_id, title=user_prompt[:50])

        if not task_id:
            task_exec = TaskExecution.objects.create(
                conversation=conv,
                graph_thread_id=conversation_id,
                user_prompt=user_prompt,
                status='planning'
            )
            task_id = task_exec.id
        else:
            task_exec = TaskExecution.objects.filter(id=task_id).first()
            if not task_exec:
                task_exec = TaskExecution.objects.create(
                    id=task_id,
                    conversation=conv,
                    graph_thread_id=conversation_id,
                    user_prompt=user_prompt,
                    status='planning'
                )

        seq_num = TaskEvent.objects.filter(task_execution=task_exec).count() + 1
        
        def emit_event(event_type: str, payload: Dict[str, Any]):
            nonlocal seq_num
            TaskEvent.objects.create(
                task_execution=task_exec,
                event_type=event_type,
                payload=payload,
                sequence_num=seq_num
            )
            seq_num += 1

        if task_exec.status == 'completed' or task_exec.status == 'failed' or task_exec.status == 'cancelled':
            yield {"type": "complete", "content": "Task is already finished.", "task_id": task_id, "status": task_exec.status}
            return

        yield {
            "type": "thinking",
            "content": f"Task [{task_id}]: Analyzing intent & planning...",
            "task_id": task_id
        }
        
        if task_exec.status == 'planning':
            emit_event("task.planning", {"prompt": user_prompt})
            task_exec.status = 'executing'
            task_exec.save()

        # State Recovery / Resume
        completed_steps = ExecutionStep.objects.filter(task_execution=task_exec, status__in=['success', 'failed']).order_by('sequence_num')
        total_tool_calls_made = completed_steps.count()
        iteration_count = 0
        
        # Prepare LLM Tools
        available_tools = list(registry.list_tools().values())
        llm_client = get_llm_client()
        
        pending_approval_request = None
        executed_tool_calls = []
        
        # Format conversation history
        sys_instruction = "You are Chaitanya Karya AI Executive Assistant. Use available tools to fulfill the user's request. When you have completed the request or cannot proceed, provide a final response summary and DO NOT call any more tools."
        
        while iteration_count < self.MAX_ITERATIONS and total_tool_calls_made < self.MAX_TOOL_CALLS:
            iteration_count += 1
            
            # Re-fetch completed steps to pass to LLM
            current_steps = ExecutionStep.objects.filter(task_execution=task_exec).order_by('sequence_num')
            
            # Construct Prompt with Observation History
            history_prompt = f"User Request: {task_exec.user_prompt}\n\nExecution History:\n"
            for step in current_steps:
                history_prompt += f"- Tool: {step.tool_name}, Args: {json.dumps(step.validated_arguments)}\n  Result: {step.result if step.status == 'success' else step.error}\n"
                
            history_prompt += "\nBased on the execution history, if the task is complete, provide the final response text. Otherwise, call the next tool."

            # Plan Phase: LLM Proposes Action
            llm_response = llm_client.generate_completion(
                prompt=history_prompt,
                system_instruction=sys_instruction,
                tools=available_tools
            )
            
            if not llm_response.tool_calls:
                # Agent decided it is complete
                task_exec.status = 'completed'
                task_exec.save()
                emit_event("task.completed", {"content": llm_response.content, "status": "completed"})
                
                yield {
                    "type": "complete",
                    "content": llm_response.content,
                    "tool_calls": executed_tool_calls,
                    "task_id": task_id,
                    "status": "completed"
                }
                return

            # Execute Phase: Process Tool Calls
            for tc in llm_response.tool_calls:
                if total_tool_calls_made >= self.MAX_TOOL_CALLS:
                    break
                
                tool_name = tc.name
                args = tc.arguments
                
                # Fetch tool display name
                tool_info = registry.get_tool(tool_name)
                display_name = tool_info["display_name"] if tool_info else tool_name

                # Policy Gateway
                risk_level, requires_approval, impact_summary = evaluate_tool_risk(tool_name, args)
                idempotency_key = compute_idempotency_key(tool_name, task_id, args)
                
                # Idempotency Protection Check
                existing_step = ExecutionStep.objects.filter(
                    task_execution=task_exec, 
                    idempotency_key=idempotency_key, 
                    status='success'
                ).first()
                
                if existing_step:
                    # Skip duplicate execution
                    continue

                total_tool_calls_made += 1
                seq_idx = current_steps.count() + 1
                
                step_obj = ExecutionStep.objects.create(
                    task_execution=task_exec,
                    sequence_num=seq_idx,
                    tool_name=tool_name,
                    tool_display_name=display_name,
                    validated_arguments=args,
                    risk_level=risk_level,
                    idempotency_key=idempotency_key,
                    status='pending'
                )

                emit_event("task.step_started", {
                    "step_id": step_obj.id,
                    "sequence_num": seq_idx,
                    "tool_name": tool_name,
                    "display_name": display_name,
                    "risk_level": risk_level
                })
                
                tool_call_id = f"tc-{step_obj.id}"

                if requires_approval:
                    step_obj.status = 'awaiting_approval'
                    step_obj.save()

                    task_exec.status = 'awaiting_approval'
                    task_exec.save()

                    appr_id = f"approval-{step_obj.id}"
                    appr_obj = ApprovalRequest.objects.create(
                        id=appr_id,
                        task_execution=task_exec,
                        execution_step=step_obj,
                        tool_call_id=tool_call_id,
                        tool_name=tool_name,
                        tool_display_name=display_name,
                        description=f"Action '{display_name}' requires human approval (Risk: {risk_level}).",
                        risk_level=risk_level,
                        arguments=args,
                        impact_summary=impact_summary,
                        status='pending'
                    )

                    pending_approval_request = {
                        "id": appr_id,
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_name,
                        "tool_display_name": display_name,
                        "description": appr_obj.description,
                        "risk_level": risk_level,
                        "arguments": args,
                        "impact_summary": impact_summary,
                        "status": "pending"
                    }

                    tool_call_entry = {
                        "id": tool_call_id,
                        "tool_name": tool_name,
                        "tool_display_name": display_name,
                        "arguments": args,
                        "result": "Awaiting human approval...",
                        "status": "awaiting_approval"
                    }
                    executed_tool_calls.append(tool_call_entry)

                    emit_event("task.approval_required", pending_approval_request)

                    yield {
                        "type": "tool_call",
                        "tool_call": tool_call_entry,
                        "task_id": task_id
                    }
                    yield {
                        "type": "approval_required",
                        "approval_request": pending_approval_request,
                        "task_id": task_id
                    }
                    return

                # Execute Tool
                step_obj.status = 'executing'
                step_obj.started_at = datetime.datetime.now(datetime.timezone.utc)
                step_obj.save()

                try:
                    result_str = registry.execute_tool(tool_name, args)
                    step_obj.status = 'success'
                    step_obj.result = result_str

                    res_match = re.search(r'\[ResourceID:\s*([^\]]+)\]', result_str)
                    if res_match:
                        step_obj.external_resource_id = res_match.group(1).strip()

                except Exception as ex:
                    result_str = f"Execution error in step {seq_idx} ({tool_name}): {str(ex)}"
                    step_obj.status = 'failed'
                    step_obj.error = result_str

                step_obj.completed_at = datetime.datetime.now(datetime.timezone.utc)
                step_obj.save()

                tool_call_entry = {
                    "id": tool_call_id,
                    "tool_name": tool_name,
                    "tool_display_name": display_name,
                    "arguments": args,
                    "result": result_str,
                    "status": step_obj.status
                }
                executed_tool_calls.append(tool_call_entry)

                emit_event("task.step_completed", {
                    "step_id": step_obj.id,
                    "tool_name": tool_name,
                    "status": step_obj.status,
                    "result": result_str
                })

                yield {
                    "type": "tool_call",
                    "tool_call": tool_call_entry,
                    "task_id": task_id
                }

        # Loop exhausted
        task_exec.status = 'failed'
        task_exec.save()
        err_msg = "Task failed: Exceeded maximum iterations or tool calls limit."
        emit_event("task.failed", {"content": err_msg, "status": "failed"})
        
        yield {
            "type": "complete",
            "content": err_msg,
            "tool_calls": executed_tool_calls,
            "task_id": task_id,
            "status": "failed"
        }

agent_runtime = LangGraphAgentRuntime()


