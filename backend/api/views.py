import time
import json
import uuid
import threading
from django.db import transaction
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Conversation, Message, ToolCall, ApprovalRequest,
    AuditLog, UserPreference, KnowledgeDocument,
    TaskExecution, ExecutionStep, TaskEvent,
    Integration, OAuthGrant, EncryptedCredential, OAuthStateNonce,
    ScheduledTask, ClipboardEntry, WorkflowAutomation, WorkflowExecutionLog
)
from .serializers import (
    ConversationSerializer, MessageSerializer, ToolCallSerializer,
    ApprovalRequestSerializer, AuditLogSerializer
)
from agent.graph import agent_runtime
from agent.policy import evaluate_tool_risk
from agent.registry import registry
from agent.memory import memory_system
from agent.proactive import generate_daily_briefing
from agent.meeting_intel import generate_mom_from_transcript
from agent.voice import process_speech_to_text, generate_text_to_speech

@api_view(['POST'])
@permission_classes([AllowAny])
def guest_login_endpoint(request):
    """
    Creates an anonymous Guest user session and issues a valid JWT access token.
    """
    guest_id = uuid.uuid4().hex[:8]
    username = f"guest_{guest_id}"
    email = f"guest_{guest_id}@chaitanyakarya.local"
    user = User.objects.create_user(
        username=username,
        email=email,
        password=uuid.uuid4().hex,
        first_name="Guest",
        last_name="User"
    )
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'pk': user.pk,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_guest': True
        }
    }, status=status.HTTP_200_OK)

class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        qs = Message.objects.filter(conversation__user=self.request.user)
        conv_id = self.request.query_params.get('conversation_id')
        if conv_id:
            return qs.filter(conversation_id=conv_id)
        return qs

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    Main Chat API Endpoint. Runs LangGraph agent execution and saves state.
    """
    content = request.data.get('content', '')
    conversation_id = request.data.get('conversation_id')

    if not content:
        return Response({'error': 'Message content is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not conversation_id:
        conv = Conversation.objects.create(
            user=request.user,
            title=content[:50],
            last_message_preview=content[:60]
        )
        conversation_id = conv.id
    else:
        conv = Conversation.objects.filter(id=conversation_id, user=request.user).first()
        if not conv:
            conv = Conversation.objects.create(id=conversation_id, user=request.user, title=content[:50])

    user_msg = Message.objects.create(
        conversation=conv,
        role='user',
        content=content,
        status='complete'
    )

    result_turn = None
    for step in agent_runtime.process_turn(content, conversation_id):
        result_turn = step

    assistant_content = result_turn.get('content', '')
    tool_calls_data = result_turn.get('tool_calls', [])
    approval_data = result_turn.get('approval_request')

    asst_msg = Message.objects.create(
        conversation=conv,
        role='assistant',
        content=assistant_content,
        status='complete'
    )

    saved_tool_calls = []
    for tc in tool_calls_data:
        tc_id = tc.get('id')
        if ToolCall.objects.filter(id=tc_id).exists():
            tc_id = f"tc-{uuid.uuid4().hex[:10]}"
        tc_obj = ToolCall.objects.create(
            id=tc_id,
            message=asst_msg,
            tool_name=tc.get('tool_name'),
            tool_display_name=tc.get('tool_display_name', ''),
            arguments=tc.get('arguments', {}),
            result=tc.get('result', ''),
            status=tc.get('status', 'success')
        )
        saved_tool_calls.append(tc_obj)

    if approval_data:
        appr_id = approval_data.get('id')
        appr_obj = ApprovalRequest.objects.filter(id=appr_id).first()
        if appr_obj:
            appr_obj.message = asst_msg
            appr_obj.save()
        else:
            ApprovalRequest.objects.create(
                id=appr_id,
                message=asst_msg,
                tool_call_id=approval_data.get('tool_call_id', ''),
                tool_name=approval_data.get('tool_name'),
                tool_display_name=approval_data.get('tool_display_name', ''),
                description=approval_data.get('description', ''),
                risk_level=approval_data.get('risk_level', 'HIGH'),
                arguments=approval_data.get('arguments', {}),
                impact_summary=approval_data.get('impact_summary', ''),
                status='pending'
            )


    conv.message_count += 2
    conv.last_message_preview = assistant_content[:60]
    conv.updated_at = timezone.now()
    conv.save()

    return Response({
        'user_message': MessageSerializer(user_msg).data,
        'assistant_message': MessageSerializer(asst_msg).data,
        'conversation_id': conversation_id,
        'task_id': result_turn.get('task_id')
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_task_endpoint(request):
    """
    Asynchronous Task Creation Endpoint.
    Spawns background execution and returns task_id immediately.
    """
    prompt = request.data.get('prompt', '')
    conv_id = request.data.get('conversation_id', f"conv-{uuid.uuid4().hex[:10]}")

    if not prompt:
        return Response({'error': 'Prompt is required'}, status=status.HTTP_400_BAD_REQUEST)

    conv, _ = Conversation.objects.get_or_create(id=conv_id, user=request.user, defaults={'title': prompt[:50]})

    task_exec = TaskExecution.objects.create(
        conversation=conv,
        user_prompt=prompt,
        status='planning'
    )

    def run_worker():
        for _ in agent_runtime.process_turn(prompt, conv_id, task_exec.id):
            pass

    t = threading.Thread(target=run_worker)
    t.daemon = True
    t.start()

    return Response({
        'task_id': task_exec.id,
        'conversation_id': conv_id,
        'status': 'planning'
    }, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stream_task_events_endpoint(request, task_id):
    """
    Server-Sent Events (SSE) Endpoint.
    Streams persisted TaskEvent records starting from last sequence.
    """
    task_exec = TaskExecution.objects.filter(id=task_id).first()
    if not task_exec:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    def event_stream():
        last_seq = int(request.query_params.get('last_seq', 0))
        retry_count = 0
        while retry_count < 30: # max polling iterations
            events = TaskEvent.objects.filter(task_execution=task_exec, sequence_num__gt=last_seq)
            for ev in events:
                data = {
                    'event_type': ev.event_type,
                    'sequence_num': ev.sequence_num,
                    'payload': ev.payload,
                    'timestamp': ev.timestamp.isoformat()
                }
                yield f"event: {ev.event_type}\ndata: {json.dumps(data)}\n\n"
                last_seq = ev.sequence_num

            if task_exec.status in ['completed', 'failed', 'awaiting_approval']:
                break
            time.sleep(0.5)
            retry_count += 1
            task_exec.refresh_from_db()

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_approval(request, approval_id):
    """
    Resolves human approval decision atomically using database transactions & row locks.
    Prevents double execution race conditions.
    """
    approved = request.data.get('approved', False)
    reason = request.data.get('reason', '')

    with transaction.atomic():
        approval = ApprovalRequest.objects.select_for_update().filter(id=approval_id).first()
        if not approval:
            return Response({'error': 'Approval request not found'}, status=status.HTTP_404_NOT_FOUND)

        if approval.status != 'pending':
            return Response({'error': f'Approval request already resolved as {approval.status}.'}, status=status.HTTP_409_CONFLICT)

        approval.status = 'approved' if approved else 'rejected'
        approval.resolved_at = timezone.now()
        approval.rejection_reason = reason
        approval.save()

        AuditLog.objects.create(
            action_type=f"APPROVAL_{approval.status.upper()}",
            risk_level=approval.risk_level,
            details={
                'approval_id': approval_id,
                'tool_name': approval.tool_name,
                'arguments': approval.arguments,
                'reason': reason
            }
        )

        execution_result = ""
        if approved:
            # Re-evaluate policy on stored args
            risk, req, summary = evaluate_tool_risk(approval.tool_name, approval.arguments)
            execution_result = registry.execute_tool(approval.tool_name, approval.arguments)
            followup_content = f"✅ Action **approved**. Executed {approval.tool_display_name}: {execution_result}"

            if approval.execution_step:
                approval.execution_step.status = 'success'
                approval.execution_step.result = execution_result
                approval.execution_step.save()
        else:
            followup_content = f"❌ Action **rejected**{f': {reason}' if reason else ''}. The action was cancelled."
            if approval.execution_step:
                approval.execution_step.status = 'skipped'
                approval.execution_step.save()

        if approval.task_execution:
            approval.task_execution.status = 'completed' if approved else 'cancelled'
            approval.task_execution.save()

        followup_msg = None
        if approval.message:
            conv = approval.message.conversation
            followup_msg = Message.objects.create(
                conversation=conv,
                role='assistant',
                content=followup_content,
                status='complete'
            )

    return Response({
        'approval': ApprovalRequestSerializer(approval).data,
        'execution_result': execution_result,
        'followup_content': followup_content
    })

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def preferences_endpoint(request):
    """CRUD API for structured user preferences."""
    if request.method == 'GET':
        category = request.query_params.get('category')
        prefs = UserPreference.objects.filter(is_active=True)
        if category:
            prefs = prefs.filter(category=category)
        data = [{'id': str(p.id), 'key': p.key, 'value': p.value, 'category': p.category, 'confidence': p.confidence, 'source': p.source} for p in prefs]
        return Response({'preferences': data})

    elif request.method == 'POST':
        key = request.data.get('key')
        value = request.data.get('value')
        category = request.data.get('category', 'general')
        if not key or not value:
            return Response({'error': 'key and value are required'}, status=status.HTTP_400_BAD_REQUEST)
        msg = memory_system.save_preference(key, value, category)
        return Response({'message': msg})

    elif request.method == 'DELETE':
        key = request.data.get('key')
        if key:
            UserPreference.objects.filter(key=key).update(is_active=False)
            return Response({'message': f"Preference '{key}' deactivated."})
        return Response({'error': 'key is required'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def briefing_endpoint(request):
    data = generate_daily_briefing()
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def meeting_intel_endpoint(request):
    transcript = request.data.get('transcript', '')
    title = request.data.get('title', 'Team Sync')
    result = generate_mom_from_transcript(transcript, title)
    return Response(result)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def voice_stt_endpoint(request):
    text = process_speech_to_text(request.body)
    return Response({'transcription': text})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def voice_tts_endpoint(request):
    text = request.data.get('text', '')
    res = generate_text_to_speech(text)
    return Response(res)


# ══════════════════════════════════════════════════════════════
# Phase 1: OAuth2 Integration Hub API Endpoints
# ══════════════════════════════════════════════════════════════

from agent.integrations.hub import integration_hub, InvalidOAuthStateError, IntegrationError

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_integrations_endpoint(request):
    """
    Lists all supported providers and their connection status for the authenticated user.
    """
    user_integrations = {
        integ.provider: integ
        for integ in Integration.objects.filter(user=request.user)
    }

    supported_providers = ["google", "microsoft", "slack", "github"]
    results = []

    for prov in supported_providers:
        integ = user_integrations.get(prov)
        if integ:
            grant = getattr(integ, "grant", None)
            results.append({
                "provider": prov,
                "status": integ.status,
                "account_email": integ.account_email,
                "account_name": integ.account_name,
                "last_successful_auth": integ.last_successful_auth,
                "scopes": grant.scopes if grant else [],
                "is_expired": grant.is_expired() if grant else False,
            })
        else:
            results.append({
                "provider": prov,
                "status": "DISCONNECTED",
                "account_email": "",
                "account_name": "",
                "last_successful_auth": None,
                "scopes": [],
                "is_expired": False,
            })

    return Response({"integrations": results})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def connect_integration_endpoint(request, provider):
    """
    Initiates OAuth authorization flow for the requested provider.
    """
    redirect_uri = request.query_params.get('redirect_uri', 'http://127.0.0.1:8000/api/auth/google/login/callback/')
    scopes = request.query_params.getlist('scopes') or None

    try:
        auth_url, state = integration_hub.start_oauth_flow(
            user_id=request.user.id,
            provider_id=provider,
            redirect_uri=redirect_uri,
            scopes=scopes
        )
        return Response({
            "provider": provider,
            "authorization_url": auth_url,
            "state": state,
        })
    except NotImplementedError as nie:
        return Response({"error": str(nie)}, status=status.HTTP_501_NOT_IMPLEMENTED)
    except Exception as ex:
        return Response({"error": f"Failed to initiate OAuth flow: {str(ex)}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def callback_integration_endpoint(request, provider):
    """
    Handles OAuth callback code exchange, validates CSRF state, and stores encrypted credentials.
    """
    code = request.data.get('code')
    state = request.data.get('state')
    redirect_uri = request.data.get('redirect_uri', 'http://localhost:5173/oauth/callback')

    if not code or not state:
        return Response({"error": "Both 'code' and 'state' are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        integration = integration_hub.complete_oauth_flow(
            user_id=request.user.id,
            provider_id=provider,
            code=code,
            state=state,
            redirect_uri=redirect_uri
        )
        return Response({
            "message": f"Successfully connected {provider}.",
            "provider": integration.provider,
            "status": integration.status,
            "account_email": integration.account_email,
            "account_name": integration.account_name,
        })
    except InvalidOAuthStateError as ose:
        return Response({"error": str(ose)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as ex:
        return Response({"error": f"OAuth callback completion failed: {str(ex)}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_integration_endpoint(request, provider):
    """
    Revokes provider tokens, deletes encrypted credentials, and disconnects integration.
    """
    try:
        success = integration_hub.disconnect_integration(
            user_id=request.user.id,
            provider_id=provider
        )
        if success:
            return Response({"message": f"Successfully disconnected {provider}."})
        return Response({"error": f"No active integration found for {provider}."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as ex:
        return Response({"error": f"Failed to disconnect {provider}: {str(ex)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_integration_endpoint(request, provider):
    """
    Triggers live Cloud Sync test for target provider (e.g. Google Calendar).
    """
    if provider.lower() == 'google':
        from agent.tools.google_tools import get_google_credentials, calendar_get_events
        creds = get_google_credentials()
        if creds:
            events_msg = calendar_get_events("today")
            return Response({
                "status": "CONNECTED",
                "synced": True,
                "message": "Google Workspace & Calendar are connected and actively syncing in real-time.",
                "details": events_msg
            })
        else:
            return Response({
                "status": "DISCONNECTED",
                "synced": False,
                "message": "Google Workspace is not yet connected with Calendar write scope."
            })
    return Response({"error": f"Provider '{provider}' sync not supported."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_token_endpoint(request, provider):
    """
    Directly links / seeds OAuth tokens for a provider into the IntegrationHub vault.
    """
    access_token = request.data.get('access_token', '').strip()
    refresh_token = request.data.get('refresh_token', '').strip()
    account_email = request.data.get('account_email', '').strip() or request.user.email

    if not access_token:
        return Response({"error": "access_token is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from api.models import Integration, OAuthGrant, EncryptedCredential
        from agent.vault import CredentialVault
        from agent.integrations.hub import get_credential_vault
        from django.utils import timezone as dj_timezone
        from datetime import timedelta

        vault = get_credential_vault()
        aad = CredentialVault.construct_aad(request.user.id, provider.lower())
        secret_payload = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }
        encrypted_envelope = vault.encrypt_secret(secret_payload, associated_data=aad)

        integ, _ = Integration.objects.update_or_create(
            user=request.user,
            provider=provider.lower(),
            defaults={
                "status": "CONNECTED",
                "account_email": account_email,
                "account_name": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                "last_successful_auth": dj_timezone.now(),
            }
        )
        grant, _ = OAuthGrant.objects.update_or_create(
            integration=integ,
            defaults={
                "scopes": ["profile", "email", "https://www.googleapis.com/auth/calendar.events"],
                "token_type": "Bearer",
                "expires_at": dj_timezone.now() + timedelta(days=30),
                "revoked_at": None,
            }
        )
        EncryptedCredential.objects.update_or_create(
            grant=grant,
            defaults={
                "encrypted_envelope": encrypted_envelope,
                "key_version": 1,
            }
        )

        return Response({
            "message": f"Successfully linked {provider} credentials to vault.",
            "provider": provider,
            "status": "CONNECTED"
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ══════════════════════════════════════════════════════════════
# Phase 2: Scheduler & Clipboard Monitor Endpoints
# ══════════════════════════════════════════════════════════════

from .models import ScheduledTask, ClipboardEntry
from agent.tools.scheduler_tools import schedule_task, list_scheduled_tasks, cancel_scheduled_task
from agent.clipboard_monitor import start_clipboard_monitor, stop_clipboard_monitor, get_clipboard_history

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def scheduled_tasks_endpoint(request, task_id=None):
    """Manage Scheduled Tasks."""
    if request.method == 'GET':
        tasks = ScheduledTask.objects.filter(user=request.user)
        data = [{
            'id': t.id,
            'prompt': t.prompt,
            'next_run': t.next_run.isoformat() if t.next_run else None,
            'repeat_type': t.repeat_type,
            'status': t.status,
            'last_run': t.last_run.isoformat() if t.last_run else None,
            'last_result': t.last_result,
            'run_count': t.run_count
        } for t in tasks]
        return Response({'scheduled_tasks': data})

    elif request.method == 'POST':
        prompt = request.data.get('prompt', '')
        run_at = request.data.get('run_at', '')
        repeat = request.data.get('repeat', 'once')
        if not prompt:
            return Response({'error': 'prompt is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = schedule_task(prompt=prompt, run_at=run_at, repeat=repeat)
        return Response({'message': result})

    elif request.method == 'DELETE':
        target_id = task_id or request.data.get('task_id')
        if not target_id:
            return Response({'error': 'task_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = cancel_scheduled_task(target_id)
        return Response({'message': result})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def clipboard_endpoint(request):
    """Access clipboard history and toggle background clipboard monitor."""
    from agent.clipboard_monitor import start_clipboard_monitor, stop_clipboard_monitor
    if request.method == 'GET':
        entries = ClipboardEntry.objects.all()[:50]
        data = [{
            'id': str(e.id),
            'content': e.content,
            'category': e.category,
            'is_pinned': e.is_pinned,
            'captured_at': e.captured_at.isoformat() if e.captured_at else None
        } for e in entries]
        return Response({'clipboard_entries': data})

    elif request.method == 'POST':
        action = request.data.get('action', 'start')
        if action == 'start':
            msg = start_clipboard_monitor()
        else:
            msg = stop_clipboard_monitor()
        return Response({'message': msg})


# ══════════════════════════════════════════════════════════════
# Phase 4: Autonomous Workflows, Screen Vision & Wake Word APIs
# ══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([AllowAny])
def workflows_endpoint(request, workflow_id=None):
    """List, create, update, or toggle background autonomous workflows."""
    from agent.workflows import seed_default_workflows
    seed_default_workflows()

    if request.method == 'GET':
        workflows = WorkflowAutomation.objects.all()
        data = [{
            'id': w.id,
            'name': w.name,
            'description': w.description,
            'workflow_type': w.workflow_type,
            'trigger_type': w.trigger_type,
            'interval_minutes': w.interval_minutes,
            'is_active': w.is_active,
            'status': w.status,
            'config': w.config,
            'last_run': w.last_run.isoformat() if w.last_run else None,
            'last_status': w.last_status,
            'last_output': w.last_output,
            'run_count': w.run_count
        } for w in workflows]
        return Response({'workflows': data})

    elif request.method == 'POST':
        wf_id = workflow_id or request.data.get('id')
        if wf_id:
            try:
                wf = WorkflowAutomation.objects.get(id=wf_id)
                if 'is_active' in request.data:
                    wf.is_active = bool(request.data['is_active'])
                if 'interval_minutes' in request.data:
                    wf.interval_minutes = int(request.data['interval_minutes'])
                if 'config' in request.data:
                    wf.config = request.data['config']
                wf.save()
                return Response({'status': 'updated', 'workflow_id': wf.id, 'is_active': wf.is_active})
            except WorkflowAutomation.DoesNotExist:
                return Response({'error': 'Workflow not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create new custom workflow
        name = request.data.get('name', 'Custom AI Workflow')
        desc = request.data.get('description', '')
        wf_type = request.data.get('workflow_type', 'custom_ai_loop')
        interval = int(request.data.get('interval_minutes', 60))
        wf = WorkflowAutomation.objects.create(
            name=name,
            description=desc,
            workflow_type=wf_type,
            interval_minutes=interval,
            is_active=True,
            config=request.data.get('config', {})
        )
        return Response({'status': 'created', 'workflow_id': wf.id})

    elif request.method == 'DELETE':
        target_id = workflow_id or request.data.get('id')
        if not target_id:
            return Response({'error': 'id required'}, status=status.HTTP_400_BAD_REQUEST)
        WorkflowAutomation.objects.filter(id=target_id).delete()
        return Response({'status': 'deleted', 'id': target_id})


@api_view(['POST'])
@permission_classes([AllowAny])
def trigger_workflow_endpoint(request, workflow_id):
    """Trigger immediate execution of an autonomous background workflow."""
    from agent.workflows import execute_workflow
    success, result_message = execute_workflow(workflow_id)
    return Response({
        'workflow_id': workflow_id,
        'success': success,
        'result': result_message
    })


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def screen_analyze_endpoint(request):
    """Analyze current active screen, window, and visual OCR text."""
    from agent.tools.local_tools import analyze_screen_context
    focus_prompt = request.data.get('prompt', '') if request.method == 'POST' else ''
    result = analyze_screen_context(focus_prompt=focus_prompt)
    return Response({
        'status': 'success',
        'analysis': result
    })


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def wakeword_status_endpoint(request):
    """Get or toggle Wake Word ('Hey Chaitanya') listening engine."""
    from agent.wakeword import get_wake_word_status, set_wake_word_enabled
    if request.method == 'POST':
        enabled = request.data.get('enabled', True)
        new_state = set_wake_word_enabled(bool(enabled))
        return Response({'status': 'updated', 'enabled': new_state})
    return Response(get_wake_word_status())




