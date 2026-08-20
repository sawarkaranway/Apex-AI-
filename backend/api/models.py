import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

def generate_conv_id():
    return f"conv-{uuid.uuid4().hex[:10]}"

def generate_msg_id():
    return f"msg-{uuid.uuid4().hex[:10]}"

def generate_tc_id():
    return f"tc-{uuid.uuid4().hex[:10]}"

def generate_task_exec_id():
    return f"task-{uuid.uuid4().hex[:10]}"

def generate_step_id():
    return f"step-{uuid.uuid4().hex[:10]}"

def generate_approval_id():
    return f"approval-{uuid.uuid4().hex[:10]}"

class Conversation(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_conv_id)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="conversations")
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    message_count = models.IntegerField(default=0)
    last_message_preview = models.TextField(blank=True, default="")

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.id} — {self.title}"


class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    STATUS_CHOICES = [
        ('streaming', 'Streaming'),
        ('complete', 'Complete'),
        ('error', 'Error'),
    ]

    id = models.CharField(max_length=64, primary_key=True, default=generate_msg_id)
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='complete')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.id}: {self.content[:40]}"


class ToolCall(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executing', 'Executing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('awaiting_approval', 'Awaiting Approval'),
    ]

    id = models.CharField(max_length=64, primary_key=True, default=generate_tc_id)
    message = models.ForeignKey(Message, related_name='tool_calls', on_delete=models.CASCADE, null=True, blank=True)
    tool_name = models.CharField(max_length=100)
    tool_display_name = models.CharField(max_length=200, blank=True, default="")
    arguments = models.JSONField(default=dict)
    result = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.tool_name} ({self.status})"


class TaskExecution(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('executing', 'Executing'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.CharField(max_length=64, primary_key=True, default=generate_task_exec_id)
    conversation = models.ForeignKey(Conversation, related_name='task_executions', on_delete=models.CASCADE)
    graph_thread_id = models.CharField(max_length=100, blank=True, default="")
    graph_checkpoint_id = models.CharField(max_length=100, blank=True, default="")
    user_prompt = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='planning')
    plan = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Task [{self.id}] — {self.status}"


class ExecutionStep(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executing', 'Executing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
        ('awaiting_approval', 'Awaiting Approval'),
    ]

    id = models.CharField(max_length=64, primary_key=True, default=generate_step_id)
    task_execution = models.ForeignKey(TaskExecution, related_name='steps', on_delete=models.CASCADE)
    sequence_num = models.IntegerField(default=1)
    tool_name = models.CharField(max_length=100)
    tool_display_name = models.CharField(max_length=200, blank=True, default="")
    validated_arguments = models.JSONField(default=dict)
    risk_level = models.CharField(max_length=20, default='LOW')
    idempotency_key = models.CharField(max_length=128, blank=True, default="")
    external_resource_id = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    result = models.TextField(blank=True, default="")
    error = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['sequence_num']

    def __str__(self):
        return f"Step {self.sequence_num} ({self.tool_name}) — {self.status}"


class ApprovalRequest(models.Model):
    RISK_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    id = models.CharField(max_length=64, primary_key=True, default=generate_approval_id)
    message = models.OneToOneField(Message, related_name='approval_request', on_delete=models.CASCADE, null=True, blank=True)
    task_execution = models.ForeignKey(TaskExecution, related_name='approval_requests', on_delete=models.CASCADE, null=True, blank=True)
    execution_step = models.ForeignKey(ExecutionStep, related_name='approval_requests', on_delete=models.CASCADE, null=True, blank=True)
    tool_call_id = models.CharField(max_length=64, blank=True, default="")
    tool_name = models.CharField(max_length=100)
    tool_display_name = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField()
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default='HIGH')
    arguments = models.JSONField(default=dict)
    impact_summary = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{self.risk_level}] {self.tool_name} — {self.status}"


class TaskEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_execution = models.ForeignKey(TaskExecution, related_name='events', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=100) # e.g. task.created, task.planning, task.step_started, etc.
    payload = models.JSONField(default=dict)
    sequence_num = models.IntegerField(default=1)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sequence_num']


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_type = models.CharField(max_length=100)
    risk_level = models.CharField(max_length=20)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']


class UserPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="preferences")
    key = models.CharField(max_length=100)
    value = models.TextField()
    category = models.CharField(max_length=50, default="general")
    confidence = models.FloatField(default=1.0)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=100, default="user_statement")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-updated_at']


class KnowledgeDocument(models.Model):
    """
    Dedicated application-level Knowledge Base Document entity.
    Supports logical category separation:
    - user_knowledge (Personal facts, preferences, instructions)
    - subject_knowledge (Data Science, ML, academic/domain notes)
    - project_knowledge (Architecture, codebases, workflows)
    - uploaded_documents (PDF, DOCX, CSV, XLSX, PPTX)
    - system_knowledge (Application capabilities, built-in reference, read-only for normal users)
    """
    CATEGORY_CHOICES = [
        ('user_knowledge', 'User Knowledge'),
        ('subject_knowledge', 'Subject / Domain Knowledge'),
        ('project_knowledge', 'Project Knowledge'),
        ('uploaded_documents', 'Uploaded Documents'),
        ('system_knowledge', 'System / Application Knowledge'),
    ]
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('indexing', 'Indexing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="knowledge_documents")
    project_id = models.CharField(max_length=100, blank=True, default="")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='uploaded_documents', db_index=True)
    title = models.CharField(max_length=255)
    filename = models.CharField(max_length=255, blank=True, default="")
    file_type = models.CharField(max_length=50, default="text")
    document_type = models.CharField(max_length=50, default="text")
    source = models.CharField(max_length=255, blank=True, default="")
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='ready', db_index=True)
    content = models.TextField(blank=True, default="")
    file_path = models.CharField(max_length=500, blank=True, default="")
    file_size = models.BigIntegerField(default=0)
    file_checksum = models.CharField(max_length=64, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    summary = models.TextField(blank=True, default="")
    chunk_count = models.IntegerField(default=0)
    is_system = models.BooleanField(default=False, db_index=True)
    doc_metadata = models.JSONField(default=dict, blank=True)
    ingested_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"[{self.category}] {self.title} ({self.status})"


class KnowledgeChunk(models.Model):
    """
    Fine-grained semantic fragment from a parsed KnowledgeDocument.
    Preserves exact page numbers and section headers for accurate RAG citations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(KnowledgeDocument, related_name='chunks', on_delete=models.CASCADE)
    chunk_index = models.IntegerField(default=1)
    text = models.TextField()
    cleaned_text = models.TextField(blank=True, default="")
    token_count = models.IntegerField(default=0)
    page_number = models.IntegerField(default=1)
    section_title = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['document', 'chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title} (Page {self.page_number})"


class CalculationHistory(models.Model):
    """
    Persistent, user-isolated audit history for mathematical computations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="calculations")
    query = models.TextField()
    operation = models.CharField(max_length=100, blank=True, default="")
    exact_answer = models.TextField(blank=True, default="")
    approximate_answer = models.TextField(blank=True, default="")
    formula_used = models.TextField(blank=True, default="")
    steps = models.JSONField(default=list, blank=True)
    result_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.operation}] {self.query[:40]} => {self.exact_answer[:30]}"


# ══════════════════════════════════════════════════════════════
# Phase 1: Real OAuth2 Integration Hub & Encrypted Credentials
# ══════════════════════════════════════════════════════════════

class Integration(models.Model):
    STATUS_CHOICES = [
        ('CONNECTED', 'Connected'),
        ('REAUTH_REQUIRED', 'Reauthorization Required'),
        ('DISCONNECTED', 'Disconnected'),
        ('ERROR', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="integrations")
    provider = models.CharField(max_length=50)  # e.g., 'google', 'microsoft', 'slack', 'github'
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DISCONNECTED')
    account_email = models.EmailField(blank=True, default="")
    account_name = models.CharField(max_length=255, blank=True, default="")
    last_successful_auth = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'provider')
        ordering = ['provider']

    def __str__(self):
        return f"{self.user.username} — {self.provider} ({self.status})"


class OAuthGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.OneToOneField(Integration, on_delete=models.CASCADE, related_name='grant')
    scopes = models.JSONField(default=list)
    token_type = models.CharField(max_length=50, default="Bearer")
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"Grant for {self.integration} (expires: {self.expires_at})"


class EncryptedCredential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grant = models.OneToOneField(OAuthGrant, on_delete=models.CASCADE, related_name='encrypted_credential')
    encrypted_envelope = models.TextField(help_text="JSON serialized AES-256-GCM envelope with nonce, ciphertext, and AAD")
    key_version = models.IntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"EncryptedCredential v{self.key_version} for {self.grant.integration}"


class OAuthStateNonce(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="oauth_states")
    provider = models.CharField(max_length=50)
    state_token = models.CharField(max_length=128, unique=True, db_index=True)
    redirect_uri = models.CharField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    def is_valid(self) -> bool:
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"OAuthState [{self.provider}] for {self.user.username}"


# ══════════════════════════════════════════════════════════════
# Phase 2: Persistent Task Scheduler & Clipboard Monitor
# ══════════════════════════════════════════════════════════════

def generate_sched_id():
    return f"sched-{uuid.uuid4().hex[:10]}"

class ScheduledTask(models.Model):
    REPEAT_CHOICES = [
        ('once', 'Once'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.CharField(max_length=64, primary_key=True, default=generate_sched_id)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="scheduled_tasks")
    prompt = models.TextField(help_text="The AI instruction to execute at scheduled time")
    next_run = models.DateTimeField(help_text="Next scheduled execution time")
    repeat_type = models.CharField(max_length=20, choices=REPEAT_CHOICES, default='once')
    cron_expression = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_run = models.DateTimeField(null=True, blank=True)
    last_result = models.TextField(blank=True, default="")
    run_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_run']

    def __str__(self):
        return f"[{self.id}] {self.prompt[:40]}... ({self.status})"


class ClipboardEntry(models.Model):
    """Stores clipboard history entries captured by the clipboard monitor."""
    CATEGORY_CHOICES = [
        ('text', 'Text'),
        ('url', 'URL'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('code', 'Code'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="clipboard_entries")
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='text')
    source_app = models.CharField(max_length=200, blank=True, default="")
    is_pinned = models.BooleanField(default=False)
    captured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-captured_at']

    def __str__(self):
        return f"[{self.category}] {self.content[:40]}... ({self.captured_at})"


# ══════════════════════════════════════════════════════════════
# Phase 3: Autonomous Background Workflow Automation Loops
# ══════════════════════════════════════════════════════════════

def generate_wf_id():
    return f"wf-{uuid.uuid4().hex[:10]}"

class WorkflowAutomation(models.Model):
    """Stores background autonomous workflows and agentic loops."""
    TRIGGER_CHOICES = [
        ('interval', 'Interval (Minutes)'),
        ('daily', 'Daily at specific time'),
        ('on_event', 'Triggered on Event'),
    ]
    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('error', 'Error'),
    ]
    WORKFLOW_TYPES = [
        ('downloads_cleaner', 'Smart Downloads Folder Cleaner'),
        ('priority_email_alert', 'Priority Email Inbox Watcher'),
        ('system_health_guard', 'System Health & Resource Alert Guard'),
        ('morning_briefing', 'Automated Morning Briefing'),
        ('custom_ai_loop', 'Custom Background AI Instruction'),
    ]

    id = models.CharField(max_length=64, primary_key=True, default=generate_wf_id)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="workflows")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default="")
    workflow_type = models.CharField(max_length=50, choices=WORKFLOW_TYPES, default='custom_ai_loop')
    trigger_type = models.CharField(max_length=30, choices=TRIGGER_CHOICES, default='interval')
    interval_minutes = models.IntegerField(default=60)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    config = models.JSONField(default=dict, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=50, blank=True, default="")
    last_output = models.TextField(blank=True, default="")
    run_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        status_icon = "🟢" if self.is_active else "⚪"
        return f"{status_icon} [{self.workflow_type}] {self.name}"


class WorkflowExecutionLog(models.Model):
    """Audit log for each autonomous background workflow execution."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(WorkflowAutomation, on_delete=models.CASCADE, related_name="execution_logs")
    status = models.CharField(max_length=30)  # success, failed, warning
    summary = models.TextField()
    execution_time_seconds = models.FloatField(default=0.0)
    executed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-executed_at']




