"""
Smart Clipboard Monitor — Background Thread.
Watches clipboard for changes, auto-categorizes content (URL, email, phone, code, text),
and stores in ClipboardEntry history with optional smart action suggestions.
"""

import re
import time
import threading
from typing import Optional


_monitor_thread: Optional[threading.Thread] = None
_monitor_running = False
_last_clipboard_content = ""


def categorize_clipboard_content(text: str) -> str:
    """Auto-categorize clipboard content by pattern matching."""
    if not text or not text.strip():
        return "text"

    text_clean = text.strip()

    # URL detection
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    if re.match(url_pattern, text_clean):
        return "url"

    # Email detection
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, text_clean):
        return "email"

    # Phone number detection
    phone_pattern = r'^[\+]?[\d\s\-\(\)]{7,15}$'
    if re.match(phone_pattern, text_clean):
        return "phone"

    # Code detection (heuristic: contains common code patterns)
    code_indicators = [
        'def ', 'class ', 'import ', 'from ', 'function ', 'const ', 'let ', 'var ',
        'if (', 'for (', 'while (', '=> {', '};', '();', 'return ', '#include',
        'public class', 'private ', 'protected ', '#!/', '<?php'
    ]
    if any(indicator in text_clean for indicator in code_indicators):
        return "code"

    return "text"


def _save_clipboard_entry(content: str, category: str):
    """Save a clipboard entry to the database."""
    try:
        from api.models import ClipboardEntry
        # Avoid duplicates: check if same content was captured in last 60 seconds
        from django.utils import timezone
        from datetime import timedelta
        recent_cutoff = timezone.now() - timedelta(seconds=60)
        existing = ClipboardEntry.objects.filter(
            content=content[:500],
            captured_at__gte=recent_cutoff
        ).exists()

        if not existing:
            ClipboardEntry.objects.create(
                content=content[:5000],  # Limit stored content
                category=category
            )
    except Exception:
        pass


def _clipboard_monitor_loop():
    """Background loop that polls clipboard every 2 seconds for changes."""
    global _last_clipboard_content, _monitor_running

    while _monitor_running:
        try:
            current_text = ""

            # Read clipboard
            try:
                import pyperclip
                current_text = pyperclip.paste() or ""
            except ImportError:
                import subprocess, os
                if os.name == 'nt':
                    result = subprocess.run(
                        ['powershell', '-command', 'Get-Clipboard'],
                        capture_output=True, text=True, timeout=3
                    )
                    current_text = result.stdout.strip() if result.returncode == 0 else ""

            # Check for change
            if current_text and current_text != _last_clipboard_content:
                _last_clipboard_content = current_text
                category = categorize_clipboard_content(current_text)
                _save_clipboard_entry(current_text, category)

        except Exception:
            pass

        time.sleep(2)  # Poll every 2 seconds


def start_clipboard_monitor():
    """Start the background clipboard monitoring thread."""
    global _monitor_thread, _monitor_running

    if _monitor_running and _monitor_thread and _monitor_thread.is_alive():
        return "Clipboard monitor is already running."

    _monitor_running = True
    _monitor_thread = threading.Thread(target=_clipboard_monitor_loop, daemon=True)
    _monitor_thread.start()
    return "✅ Clipboard monitor started — tracking clipboard changes in background."


def stop_clipboard_monitor():
    """Stop the background clipboard monitoring thread."""
    global _monitor_running

    if not _monitor_running:
        return "Clipboard monitor is not running."

    _monitor_running = False
    return "🛑 Clipboard monitor stopped."


def get_clipboard_history(limit: int = 20) -> str:
    """Retrieve recent clipboard history entries."""
    try:
        from api.models import ClipboardEntry
        entries = ClipboardEntry.objects.all()[:limit]

        if not entries.exists():
            return "No clipboard history available. Start the clipboard monitor first."

        lines = [f"📋 **Clipboard History** ({entries.count()} entries):"]
        for e in entries:
            icon_map = {"url": "🔗", "email": "📧", "phone": "📞", "code": "💻", "text": "📝"}
            icon = icon_map.get(e.category, "📝")
            time_str = e.captured_at.strftime("%H:%M:%S") if e.captured_at else ""
            preview = e.content[:80].replace("\n", " ")
            lines.append(f"• {icon} [{e.category}] {preview}... ({time_str})")

        return "\n".join(lines)
    except ImportError:
        return "Clipboard history unavailable — ClipboardEntry model not migrated."
    except Exception as e:
        return f"Clipboard history error: {str(e)}"
