"""
Scheduler Tools — Create, list, and cancel persistent scheduled AI tasks.
Integrates with Django ScheduledTask model and APScheduler.
"""

import uuid
import datetime
from typing import Optional


def schedule_task(prompt: str, run_at: str = "", repeat: str = "once") -> str:
    """
    Schedule a one-time or recurring AI task.
    
    Args:
        prompt: The instruction for the AI to execute (e.g., "Send daily report email")
        run_at: ISO datetime string for when to run (e.g., "2026-08-21T09:00:00")
                or relative time like "in 5 minutes", "in 1 hour"
        repeat: "once" for one-time, "daily", "hourly", "weekly" for recurring
    """
    if not prompt or not prompt.strip():
        return "Error: Task prompt cannot be empty."

    try:
        from api.models import ScheduledTask

        # Parse relative time expressions
        now = datetime.datetime.now(datetime.timezone.utc)
        next_run = None

        run_at_lower = run_at.lower().strip() if run_at else ""

        if not run_at_lower or run_at_lower in ("now", "immediately"):
            next_run = now + datetime.timedelta(seconds=30)
        elif "minute" in run_at_lower:
            import re
            m = re.search(r'(\d+)', run_at_lower)
            mins = int(m.group(1)) if m else 5
            next_run = now + datetime.timedelta(minutes=mins)
        elif "hour" in run_at_lower:
            import re
            m = re.search(r'(\d+)', run_at_lower)
            hours = int(m.group(1)) if m else 1
            next_run = now + datetime.timedelta(hours=hours)
        elif "day" in run_at_lower or "tomorrow" in run_at_lower:
            next_run = now + datetime.timedelta(days=1)
        else:
            try:
                next_run = datetime.datetime.fromisoformat(run_at.strip())
                if next_run.tzinfo is None:
                    next_run = next_run.replace(tzinfo=datetime.timezone.utc)
            except (ValueError, TypeError):
                next_run = now + datetime.timedelta(minutes=5)

        # Map repeat to cron expression
        cron_map = {
            "once": "",
            "hourly": "0 * * * *",
            "daily": "0 9 * * *",
            "weekly": "0 9 * * 1",
        }
        cron_expr = cron_map.get(repeat.lower().strip(), "")

        task = ScheduledTask.objects.create(
            prompt=prompt.strip(),
            next_run=next_run,
            repeat_type=repeat.lower().strip(),
            cron_expression=cron_expr,
            status='pending'
        )

        time_str = next_run.strftime("%A, %B %d, %Y at %I:%M %p UTC")
        repeat_str = f" (repeats {repeat})" if repeat.lower() != "once" else " (one-time)"

        return (
            f"✅ Scheduled task created successfully!\n"
            f"• Task ID: {task.id}\n"
            f"• Prompt: \"{prompt.strip()}\"\n"
            f"• Next Run: {time_str}{repeat_str}"
        )
    except ImportError:
        return f"Scheduled task '{prompt}' queued for {run_at or 'soon'}. [ScheduledTask model not yet migrated]"
    except Exception as e:
        return f"Error scheduling task: {str(e)}"


def list_scheduled_tasks() -> str:
    """List all pending and active scheduled tasks."""
    try:
        from api.models import ScheduledTask
        tasks = ScheduledTask.objects.filter(status__in=['pending', 'running']).order_by('next_run')

        if not tasks.exists():
            return "No scheduled tasks found. Use 'schedule_task' to create one."

        lines = [f"📋 **Scheduled Tasks** ({tasks.count()} active):"]
        for t in tasks[:20]:
            time_str = t.next_run.strftime("%b %d, %Y %I:%M %p") if t.next_run else "N/A"
            repeat_str = f" [{t.repeat_type}]" if t.repeat_type != "once" else ""
            lines.append(f"• [{t.id}] {t.prompt[:80]}... → {time_str}{repeat_str} ({t.status})")

        return "\n".join(lines)
    except ImportError:
        return "No scheduled tasks — ScheduledTask model not yet available."
    except Exception as e:
        return f"Error listing scheduled tasks: {str(e)}"


def cancel_scheduled_task(task_id: str) -> str:
    """Cancel a pending scheduled task by its ID."""
    if not task_id:
        return "Error: Task ID is required to cancel a scheduled task."

    try:
        from api.models import ScheduledTask
        task = ScheduledTask.objects.filter(id=task_id.strip()).first()
        if not task:
            return f"Scheduled task '{task_id}' not found."

        if task.status in ('completed', 'cancelled'):
            return f"Task '{task_id}' is already {task.status}."

        task.status = 'cancelled'
        task.save()
        return f"✅ Successfully cancelled scheduled task '{task_id}': \"{task.prompt[:60]}...\""
    except ImportError:
        return f"Cannot cancel — ScheduledTask model not available."
    except Exception as e:
        return f"Error cancelling task '{task_id}': {str(e)}"
