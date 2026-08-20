"""
Typed Metadata-Driven Tool Registry.
Registers all safe Local PC, Google Workspace, and Knowledge RAG tools.
"""

from typing import Dict, Any, Callable
from .tools.local_tools import (
    open_application, list_directory, read_file,
    write_file, delete_file, list_processes, system_search, open_browser_url,
    get_current_datetime, get_system_info, play_media_or_smart_app_launch,
    set_reminder, take_screenshot, set_system_volume,
    kill_process, create_folder, run_shell_command,
    get_system_metrics, control_media_playback, check_network_status,
    search_web_duckduckgo, lock_workstation,
    analyze_screen_context, clean_downloads_folder
)
from .tools.google_tools import (
    calendar_get_events, calendar_create_event,
    gmail_search, gmail_draft, gmail_send,
    drive_search_files, docs_create_doc
)
from .tools.rag_tools import search_knowledge_base, ingest_document
from .tools.calculator_tools import scientific_calculator
from .tools.clipboard_tools import clipboard_read, clipboard_write
from .tools.weather_tools import get_weather
from .tools.scheduler_tools import schedule_task, list_scheduled_tasks, cancel_scheduled_task

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def register(self, name: str, display_name: str, description: str, func: Callable, schema: Dict[str, Any]):
        self._tools[name] = {
            "name": name,
            "display_name": display_name,
            "description": description,
            "func": func,
            "schema": schema
        }

    def get_tool(self, name: str) -> Dict[str, Any]:
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        return self._tools


    def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        tool_info = self.get_tool(name)
        if not tool_info:
            return f"Error: Tool '{name}' not found in registry."
        try:
            return tool_info["func"](**args)
        except Exception as e:
            return f"Execution error in tool '{name}': {str(e)}"

    def _register_default_tools(self):
        # ── Scientific Calculator Tool ──
        self.register(
            "scientific_calculator", "Scientific Calculator — Deterministic Math", "Evaluate natural-language mathematics, algebra, calculus, statistics, financial math, and unit conversions",
            scientific_calculator, {"query": "str", "expression": "str"}
        )

        # Local PC Tools
        self.register(
            "open_application", "Open Application", "Open a safe local desktop application",
            open_application, {"app_name": "str"}
        )
        self.register(
            "list_directory", "List Directory", "List files in local folder",
            list_directory, {"dir_path": "str"}
        )
        self.register(
            "read_file", "Read File", "Read file contents",
            read_file, {"file_path": "str"}
        )
        self.register(
            "write_file", "Write File", "Write content to a file",
            write_file, {"file_path": "str", "content": "str"}
        )
        self.register(
            "delete_file", "Delete File", "Delete a file from disk",
            delete_file, {"file_path": "str"}
        )
        self.register(
            "list_processes", "List Processes", "List active system processes",
            list_processes, {}
        )
        self.register(
            "system_search", "System Search", "Search local workspace for files",
            system_search, {"query": "str"}
        )
        self.register(
            "open_browser_url", "Browser Automation — Open URL", "Open Chrome/Browser to URL or YouTube video",
            open_browser_url, {"url_or_query": "str"}
        )
        self.register(
            "get_current_datetime", "System Utility — Real-time Date & Time", "Fetch current date, day of week, time, and timezone",
            get_current_datetime, {}
        )
        self.register(
            "get_system_info", "System Utility — Local PC Info", "Fetch local OS version and system specs",
            get_system_info, {}
        )
        self.register(
            "play_media_or_smart_app_launch", "Smart PC Control — App vs Web Fallback", "Check local PC presence for app; launch local app if present, web browser if not",
            play_media_or_smart_app_launch, {"app_name": "str", "query": "str"}
        )

        # ── New Local PC Tools ──
        self.register(
            "set_reminder", "Reminder — Set Timed Notification", "Set a timed reminder that triggers a desktop notification after specified delay",
            set_reminder, {"message": "str", "delay_seconds": "int"}
        )
        self.register(
            "take_screenshot", "Screenshot — Capture Screen", "Capture a screenshot of the current screen and save to file",
            take_screenshot, {"save_path": "str"}
        )
        self.register(
            "set_system_volume", "Volume Control — System Audio", "Control system volume: set level, mute, unmute, increase, decrease",
            set_system_volume, {"level": "int", "action": "str"}
        )
        self.register(
            "kill_process", "Process Manager — Kill Process", "Terminate a running process by name",
            kill_process, {"process_name": "str"}
        )
        self.register(
            "create_folder", "File Manager — Create Folder", "Create a new folder/directory on local disk",
            create_folder, {"folder_path": "str"}
        )
        self.register(
            "run_shell_command", "Shell — Execute Command", "Run a shell command and return output (approval required)",
            run_shell_command, {"command": "str"}
        )

        # ── Extended System, Media & Network Tools ──
        self.register(
            "get_system_metrics", "System Health — CPU, RAM & Battery", "Fetch live system resource metrics (CPU load %, RAM usage, Disk space, Battery status)",
            get_system_metrics, {}
        )
        self.register(
            "control_media_playback", "Media Control — Playback & Audio", "Control PC media playback (play_pause, next, previous, stop, mute, volume_up, volume_down)",
            control_media_playback, {"action": "str"}
        )
        self.register(
            "check_network_status", "Network — Diagnostics & Latency", "Check internet connectivity, ping latency, local hostname and IP address",
            check_network_status, {"host": "str"}
        )
        self.register(
            "search_web_duckduckgo", "Web Search — Live Information", "Search the live web for instant answers, news, documentation, and real-time facts",
            search_web_duckduckgo, {"query": "str"}
        )
        self.register(
            "lock_workstation", "Security — Lock PC", "Lock the current computer screen immediately for security and privacy",
            lock_workstation, {}
        )
        self.register(
            "analyze_screen_context", "Vision — Active Screen Context & OCR", "Capture screen context, active app window, and OCR text for multimodal reasoning",
            analyze_screen_context, {"focus_prompt": "str"}
        )
        self.register(
            "clean_downloads_folder", "Storage — Clean Downloads Folder", "Clean old temporary and duplicate files from Downloads folder and archive them",
            clean_downloads_folder, {"days_old": "int"}
        )

        # ── Clipboard Tools ──
        self.register(
            "clipboard_read", "Clipboard — Read", "Read current text content from system clipboard",
            clipboard_read, {}
        )
        self.register(
            "clipboard_write", "Clipboard — Write", "Copy text to system clipboard",
            clipboard_write, {"text": "str"}
        )

        # ── Weather Tools ──
        self.register(
            "get_weather", "Weather — Current Conditions", "Fetch real-time weather for any city including temperature, humidity, wind, and forecast",
            get_weather, {"city": "str"}
        )

        # Google Workspace Tools
        self.register(
            "calendar_get_events", "Google Calendar — Get Events", "Fetch meetings for a date",
            calendar_get_events, {"date_str": "str"}
        )
        self.register(
            "calendar_create_event", "Google Calendar — Create Event", "Schedule a calendar meeting",
            calendar_create_event, {"title": "str", "start_time": "str", "end_time": "str"}
        )
        self.register(
            "gmail_search", "Gmail — Search Emails", "Search inbox messages",
            gmail_search, {"query": "str"}
        )
        self.register(
            "gmail_draft", "Gmail — Create Draft", "Create an email draft",
            gmail_draft, {"to": "list", "subject": "str", "body": "str"}
        )
        self.register(
            "gmail_send", "Gmail — Send Email", "Send an email message",
            gmail_send, {"to": "list", "subject": "str", "body": "str"}
        )
        self.register(
            "drive_search_files", "Google Drive — Search Files", "Search files in Google Drive",
            drive_search_files, {"query": "str"}
        )
        self.register(
            "docs_create_doc", "Google Docs — Create Document", "Create a Google Document",
            docs_create_doc, {"title": "str", "content": "str"}
        )

        # RAG Tools
        self.register(
            "search_knowledge_base", "Knowledge RAG — Search", "Retrieve grounded context snippets",
            search_knowledge_base, {"query": "str"}
        )
        self.register(
            "ingest_document", "Knowledge RAG — Ingest Document", "Ingest text into vector store",
            ingest_document, {"title": "str", "content": "str"}
        )

        # ── Scheduler Tools ──
        self.register(
            "schedule_task", "Scheduler — Create Task", "Schedule a one-time or recurring AI task to run later",
            schedule_task, {"prompt": "str", "run_at": "str", "repeat": "str"}
        )
        self.register(
            "list_scheduled_tasks", "Scheduler — List Tasks", "View all pending and active scheduled tasks",
            list_scheduled_tasks, {}
        )
        self.register(
            "cancel_scheduled_task", "Scheduler — Cancel Task", "Cancel a pending scheduled task",
            cancel_scheduled_task, {"task_id": "str"}
        )

registry = ToolRegistry()

