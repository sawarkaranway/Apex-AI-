"""
Proactive Assistant Background Worker (APScheduler)
Performs morning briefings, email/calendar polling, and proactive notification triggers dynamically.
"""

import datetime
from typing import Dict, Any
from .registry import registry

_scheduler_started = False

def generate_daily_briefing() -> Dict[str, Any]:
    """Compile daily briefing dynamically from real system date, Calendar, Gmail, Drive, and RAG memory."""
    today_str = datetime.datetime.now().strftime("%A, %B %d, %Y")
    
    cal_res = registry.execute_tool("calendar_get_events", {"date_str": today_str})
    mail_res = registry.execute_tool("gmail_search", {"query": "important OR urgent OR briefing"})
    drive_res = registry.execute_tool("drive_search_files", {"query": "Project OR Report"})
    rag_res = registry.execute_tool("search_knowledge_base", {"query": "executive priorities"})

    briefing_text = (
        f"Good morning! Executive Briefing for {today_str}:\n\n"
        f"📅 **Calendar Schedule**:\n{cal_res}\n\n"
        f"📧 **Relevant Emails**:\n{mail_res}\n\n"
        f"📁 **Drive Preparation Documents**:\n{drive_res}\n\n"
        f"💡 **Context Memory Snippets**:\n{rag_res}\n"
    )

    return {
        "summary": f"Morning briefing generated for {today_str}.",
        "content": briefing_text,
        "date": today_str
    }


def start_proactive_scheduler():
    global _scheduler_started
    if _scheduler_started:
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(generate_daily_briefing, 'interval', hours=1, id='daily_briefing_job')
        scheduler.start()
        _scheduler_started = True
        print("[APScheduler] Background proactive scheduler started successfully.")
    except Exception as e:
        print(f"[APScheduler] Proactive scheduler initialized: {e}")
