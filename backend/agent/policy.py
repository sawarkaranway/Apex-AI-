"""
Deterministic Policy Engine for Risk Classification & Safety Approval Gates.
Key Principle: Approval is deterministic policy in code, not an LLM decision.
"""

from typing import Dict, Any, Tuple

TOOL_RISK_MAP = {
    # Safe / Read-Only tools -> LOW risk (No approval)
    "list_directory": ("LOW", False),
    "read_file": ("LOW", False),
    "system_search": ("LOW", False),
    "list_processes": ("LOW", False),
    "search_knowledge_base": ("LOW", False),
    "calendar_get_events": ("LOW", False),
    "gmail_search": ("LOW", False),
    "drive_search_files": ("LOW", False),
    "open_browser_url": ("LOW", False),
    "get_current_datetime": ("LOW", False),
    "get_system_info": ("LOW", False),
    "play_media_or_smart_app_launch": ("LOW", False),
    "clipboard_read": ("LOW", False),
    "get_weather": ("LOW", False),
    "list_scheduled_tasks": ("LOW", False),
    "get_system_metrics": ("LOW", False),
    "check_network_status": ("LOW", False),
    "search_web_duckduckgo": ("LOW", False),
    "analyze_screen_context": ("LOW", False),
    "scientific_calculator": ("LOW", False),

    # Controlled Local / Reversible Writes -> MEDIUM risk (No approval required if within scope)
    "write_file": ("MEDIUM", False),
    "open_application": ("MEDIUM", False),
    "docs_create_doc": ("MEDIUM", False),
    "gmail_draft": ("MEDIUM", False),
    "ingest_document": ("MEDIUM", False),
    "clipboard_write": ("MEDIUM", False),
    "set_reminder": ("MEDIUM", False),
    "take_screenshot": ("MEDIUM", False),
    "set_system_volume": ("MEDIUM", False),
    "create_folder": ("MEDIUM", False),
    "schedule_task": ("MEDIUM", False),
    "cancel_scheduled_task": ("MEDIUM", False),
    "control_media_playback": ("MEDIUM", False),
    "lock_workstation": ("MEDIUM", False),
    "clean_downloads_folder": ("MEDIUM", False),

    # External / Consequential Actions -> HIGH risk (Explicit Human Approval Required)
    "delete_file": ("HIGH", True),
    "gmail_send": ("HIGH", True),
    "calendar_create_event": ("HIGH", True),
    "kill_process": ("HIGH", True),
    "run_shell_command": ("HIGH", True),
}

def evaluate_tool_risk(tool_name: str, args: Dict[str, Any]) -> Tuple[str, bool, str]:
    """
    Evaluates risk level for a given tool call and arguments.
    Returns: (risk_level, requires_approval, impact_summary)
    """
    if tool_name not in TOOL_RISK_MAP:
        return ("HIGH", True, f"Tool '{tool_name}' is not in policy map. Awaiting human approval by default.")

    risk_level, default_approval = TOOL_RISK_MAP[tool_name]

    # Dynamic checks based on arguments
    if tool_name == "delete_file":
        target = args.get("file_path", "specified file")
        summary = f"This action will permanently delete the file '{target}' from your local disk."
        return ("HIGH", True, summary)

    elif tool_name == "gmail_send":
        recipients = args.get("to", [])
        rec_str = ", ".join(recipients) if isinstance(recipients, list) else str(recipients)
        subject = args.get("subject", "No subject")
        summary = f"This action will send an email to {rec_str} with subject '{subject}'."
        return ("HIGH", True, summary)

    elif tool_name == "calendar_create_event":
        title = args.get("title", "New Event")
        summary = f"This action will schedule an event '{title}' on your Google Calendar."
        return ("HIGH", True, summary)

    summary = f"Execution of tool '{tool_name}' with risk level {risk_level}."
    return (risk_level, default_approval, summary)

def verify_all_tools_have_policy(registry) -> bool:
    """Verifies every tool registered in ToolRegistry has an explicit entry in TOOL_RISK_MAP."""
    registered_names = set(registry.list_tools().keys()) if hasattr(registry, 'list_tools') else set(registry._tools.keys())
    missing = registered_names - set(TOOL_RISK_MAP.keys())
    if missing:
        raise ValueError(f"Security Policy Coverage Error: Tools {missing} lack policy classifications!")
    return True

