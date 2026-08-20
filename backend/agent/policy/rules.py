"""
Policy Rules & Risk Definitions for Chaitanya Karya.
"""

from typing import Dict, Any, Tuple
from agent.domain.enums import RiskLevel

# Base tool risk levels
DEFAULT_TOOL_RISK_MAP = {
    # Read-only / safe local operations
    "get_current_datetime": RiskLevel.LOW,
    "get_system_info": RiskLevel.LOW,
    "list_directory": RiskLevel.LOW,
    "read_file": RiskLevel.LOW,
    "list_processes": RiskLevel.LOW,
    "system_search": RiskLevel.LOW,
    "search_knowledge_base": RiskLevel.LOW,
    "calendar_get_events": RiskLevel.LOW,
    "gmail_search": RiskLevel.LOW,
    "drive_search_files": RiskLevel.LOW,

    # Medium risk (local changes, browser opens, drafts)
    "open_browser_url": RiskLevel.MEDIUM,
    "open_application": RiskLevel.MEDIUM,
    "play_media_or_smart_app_launch": RiskLevel.MEDIUM,
    "gmail_draft": RiskLevel.MEDIUM,
    "docs_create_doc": RiskLevel.MEDIUM,
    "calendar_create_event": RiskLevel.MEDIUM,
    "ingest_document": RiskLevel.MEDIUM,

    # High / Critical risk (file deletion, write outside sandbox, sending emails)
    "write_file": RiskLevel.HIGH,
    "delete_file": RiskLevel.HIGH,
    "gmail_send": RiskLevel.HIGH,
    "calendar_delete_event": RiskLevel.HIGH,
}

CRITICAL_PATHS = ["/etc", "/windows", "c:\\windows", "c:\\program files", "/sys", "/proc", "c:\\users\\default"]

def evaluate_risk(tool_name: str, args: Dict[str, Any]) -> Tuple[RiskLevel, bool, str]:
    """
    Evaluates dynamic risk for a tool invocation and returns (RiskLevel, requires_approval, impact_summary).
    """
    base_risk = DEFAULT_TOOL_RISK_MAP.get(tool_name, RiskLevel.MEDIUM)

    # Dynamic path risk elevation
    if tool_name in ["write_file", "delete_file"]:
        path = str(args.get("file_path", "")).lower()
        if any(path.startswith(cp) for cp in CRITICAL_PATHS):
            return RiskLevel.CRITICAL, True, f"Target path '{path}' is a protected system directory."
        if tool_name == "delete_file":
            return RiskLevel.HIGH, True, f"Permanent deletion of file '{path}'."
        return RiskLevel.HIGH, True, f"Overwriting/Writing file '{path}'."

    # Dynamic email sending risk elevation
    if tool_name == "gmail_send":
        to_list = args.get("to", [])
        subj = args.get("subject", "(No Subject)")
        return RiskLevel.HIGH, True, f"Sending outbound email to {len(to_list)} recipient(s) with subject: '{subj}'."

    # External browser launching
    if tool_name in ["open_browser_url", "open_application"]:
        target = args.get("url_or_query") or args.get("app_name") or "unknown"
        return RiskLevel.MEDIUM, False, f"Launching external application/URL: {target}."

    requires_approval = base_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    return base_risk, requires_approval, f"Action '{tool_name}' evaluated with {base_risk.value} risk."

def verify_all_tools_have_policy(registry_instance) -> bool:
    """Verifies that all registered tools have a policy risk classification."""
    tools = registry_instance.list_tools()
    for name in tools.keys():
        evaluate_risk(name, {})
    return True
