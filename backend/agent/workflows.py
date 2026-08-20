"""
Autonomous Background Workflow Automation Loops Engine.
Executes periodic background agentic workflows:
- Downloads Cleaner
- Priority Email Watcher
- System Health Guard
- Proactive Morning Briefing
- Custom AI Instructions
"""

import time
import logging
from typing import Dict, Any, Tuple
from django.utils import timezone

logger = logging.getLogger("agent.workflows")


def execute_workflow(workflow_id: str) -> Tuple[bool, str]:
    """Execute a single workflow automation task by its ID."""
    from api.models import WorkflowAutomation, WorkflowExecutionLog
    
    start_time = time.time()
    try:
        wf = WorkflowAutomation.objects.get(id=workflow_id)
    except WorkflowAutomation.DoesNotExist:
        return False, f"Workflow '{workflow_id}' not found."

    wf.status = "running"
    wf.save(update_fields=['status'])

    success = True
    output_message = ""

    try:
        wf_type = wf.workflow_type

        if wf_type == "downloads_cleaner":
            from .tools.local_tools import clean_downloads_folder
            days = wf.config.get("days_old", 7)
            output_message = clean_downloads_folder(days_old=int(days))

        elif wf_type == "system_health_guard":
            from .tools.local_tools import get_system_metrics
            metrics_str = get_system_metrics()
            output_message = f"🛡️ **System Health Guard Check**:\n{metrics_str}"

        elif wf_type == "priority_email_alert":
            from .tools.google_tools import gmail_search
            search_res = gmail_search(query="is:unread label:important")
            output_message = f"📧 **Priority Email Watcher**:\n{search_res}"

        elif wf_type == "morning_briefing":
            from .proactive import generate_morning_briefing
            output_message = generate_morning_briefing()

        elif wf_type == "custom_ai_loop":
            prompt = wf.config.get("prompt") or wf.description
            if prompt:
                from .runtime import run_agent_turn
                output_message = run_agent_turn(f"[Background Workflow: {wf.name}] {prompt}")
            else:
                output_message = f"Custom workflow '{wf.name}' executed with no prompt."

        else:
            output_message = f"Executed generic workflow loop '{wf.name}'."

        wf.status = "idle"
        wf.last_status = "success"
        wf.last_run = timezone.now()
        wf.last_output = output_message[:2000]
        wf.run_count += 1
        wf.save()

        # Log execution
        duration = round(time.time() - start_time, 2)
        WorkflowExecutionLog.objects.create(
            workflow=wf,
            status="success",
            summary=output_message[:1000],
            execution_time_seconds=duration
        )

        return True, output_message

    except Exception as e:
        err_msg = f"Workflow '{wf.name}' execution failed: {str(e)}"
        logger.error(err_msg, exc_info=True)
        wf.status = "error"
        wf.last_status = "failed"
        wf.last_run = timezone.now()
        wf.last_output = err_msg
        wf.save()

        duration = round(time.time() - start_time, 2)
        WorkflowExecutionLog.objects.create(
            workflow=wf,
            status="failed",
            summary=err_msg,
            execution_time_seconds=duration
        )
        return False, err_msg


def seed_default_workflows():
    """Ensure default out-of-the-box workflows exist in database."""
    try:
        from api.models import WorkflowAutomation
        defaults = [
            {
                "name": "🧹 Smart Downloads Cleaner",
                "description": "Automatically moves files older than 7 days from Downloads to Cleaned_Archive to free up disk space.",
                "workflow_type": "downloads_cleaner",
                "trigger_type": "interval",
                "interval_minutes": 720,  # 12 hours
                "is_active": True,
                "config": {"days_old": 7}
            },
            {
                "name": "🛡️ System Health & Resource Guard",
                "description": "Monitors CPU load %, RAM usage, and battery status periodically to prevent PC overheating or slowdowns.",
                "workflow_type": "system_health_guard",
                "trigger_type": "interval",
                "interval_minutes": 60,  # hourly
                "is_active": True,
                "config": {"cpu_threshold": 90, "ram_threshold": 90}
            },
            {
                "name": "📧 Priority Inbox Watcher",
                "description": "Scans connected Gmail inbox for unread high-priority emails from key contacts.",
                "workflow_type": "priority_email_alert",
                "trigger_type": "interval",
                "interval_minutes": 30,
                "is_active": False,
                "config": {"keywords": "urgent, action required, invoice"}
            },
            {
                "name": "☀️ Proactive Morning Briefing",
                "description": "Compiles calendar schedule, weather, and pending items into a morning brief.",
                "workflow_type": "morning_briefing",
                "trigger_type": "daily",
                "interval_minutes": 1440,
                "is_active": True,
                "config": {"time": "08:30"}
            }
        ]

        for item in defaults:
            if not WorkflowAutomation.objects.filter(name=item["name"]).exists():
                WorkflowAutomation.objects.create(**item)
    except Exception:
        pass
