"""
Clipboard Tools — Read/Write system clipboard text.
Uses pyperclip for cross-platform clipboard access.
"""

import subprocess
import sys
import os
from typing import Optional


def clipboard_read() -> str:
    """Read current text content from system clipboard."""
    try:
        import pyperclip
        text = pyperclip.paste()
        if text:
            return f"Clipboard content ({len(text)} chars):\n{text[:2000]}"
        return "Clipboard is empty — no text content found."
    except ImportError:
        pass

    # Fallback: platform-specific clipboard read
    try:
        if os.name == 'nt':
            result = subprocess.run(
                ['powershell', '-command', 'Get-Clipboard'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                text = result.stdout.strip()
                return f"Clipboard content ({len(text)} chars):\n{text[:2000]}"
        elif sys.platform == 'darwin':
            result = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                text = result.stdout.strip()
                return f"Clipboard content ({len(text)} chars):\n{text[:2000]}"
        else:
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-o'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                text = result.stdout.strip()
                return f"Clipboard content ({len(text)} chars):\n{text[:2000]}"
    except Exception as e:
        return f"Clipboard read error: {e}"

    return "Clipboard is empty — no text content found."


def clipboard_write(text: str) -> str:
    """Write text content to system clipboard."""
    if not text:
        return "Error: Cannot write empty text to clipboard."

    try:
        import pyperclip
        pyperclip.copy(text)
        return f"Successfully copied {len(text)} characters to system clipboard."
    except ImportError:
        pass

    # Fallback: platform-specific clipboard write
    try:
        if os.name == 'nt':
            # Use PowerShell Set-Clipboard
            result = subprocess.run(
                ['powershell', '-command', f'Set-Clipboard -Value "{text[:4000]}"'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return f"Successfully copied {len(text)} characters to system clipboard."
        elif sys.platform == 'darwin':
            proc = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            proc.communicate(text.encode('utf-8'))
            return f"Successfully copied {len(text)} characters to system clipboard."
        else:
            proc = subprocess.Popen(
                ['xclip', '-selection', 'clipboard'],
                stdin=subprocess.PIPE
            )
            proc.communicate(text.encode('utf-8'))
            return f"Successfully copied {len(text)} characters to system clipboard."
    except Exception as e:
        return f"Clipboard write error: {e}"

    return "Clipboard write failed — no clipboard backend available."
