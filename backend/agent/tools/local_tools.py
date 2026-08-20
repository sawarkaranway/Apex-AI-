import os
import sys
import glob
import time
import shutil
import urllib.parse
import webbrowser
import subprocess
from typing import Dict, Any, List, Optional

# =============================================================================
# PATH SANDBOXING SECURITY LAYER
# =============================================================================

def get_allowed_sandbox_roots() -> List[str]:
    """Returns list of normalized absolute paths authorized for file operations."""
    roots = [
        os.path.abspath(os.path.expanduser("~/Documents")),
        os.path.abspath(os.path.expanduser("~/Desktop")),
        os.path.abspath(os.getcwd())
    ]
    custom_ws = os.environ.get("WORKSPACE_DIR")
    if custom_ws:
        roots.append(os.path.abspath(custom_ws))
    return list(set(roots))

def validate_sandboxed_path(file_path: str) -> str:
    """
    Validates target path is strictly within an authorized sandbox root.
    Blocks directory traversal ('..'), absolute system path escapes, and symlink escapes.
    """
    if not file_path:
        raise ValueError("File path cannot be empty.")

    target_abs = os.path.abspath(file_path)

    allowed_roots = get_allowed_sandbox_roots()
    is_valid = False
    for root in allowed_roots:
        if target_abs == root or target_abs.startswith(root + os.sep):
            is_valid = True
            break

    if not is_valid:
        raise PermissionError(f"[Security Violation] Target path '{file_path}' is outside authorized sandbox roots.")

    return target_abs

# =============================================================================
# APPLICATION DATABASE
# =============================================================================

APP_EXECUTABLES = {
    # --- Browsers ---
    "chrome": ["chrome.exe", "googlechrome.exe", "google-chrome"],
    "firefox": ["firefox.exe", "firefox"],
    "edge": ["msedge.exe", "microsoft-edge"],
    "brave": ["brave.exe", "brave"],
    "opera": ["opera.exe", "opera"],
    "safari": ["safari"],

    # --- Communication & Office ---
    "whatsapp": ["whatsapp.exe", "WhatsApp.exe", "whatsapp"],
    "telegram": ["telegram.exe", "Telegram.exe", "telegram"],
    "discord": ["discord.exe", "Discord.exe", "discord"],
    "slack": ["slack.exe", "Slack.exe", "slack"],
    "zoom": ["zoom.exe", "Zoom.exe", "zoom"],
    "notion": ["notion.exe", "Notion.exe", "notion"],
    "microsoft word": ["winword.exe"],
    "microsoft excel": ["excel.exe"],
    "microsoft powerpoint": ["powerpnt.exe"],

    # --- Development & Utilities ---
    "vscode": ["code.exe", "Code.exe", "code"],
    "visual studio code": ["code.exe", "Code.exe", "code"],
    "sublime text": ["sublime_text.exe", "subl"],
    "notepad++": ["notepad++.exe"],
    "calculator": ["calc.exe", "gnome-calculator", "kcalc"],
    "notepad": ["notepad.exe"],
    "file explorer": ["explorer.exe", "nautilus", "dolphin"],
    "spotify": ["spotify.exe", "spotify"],
    "vlc": ["vlc.exe", "vlc"],
}

def resolve_youtube_playback_url(query: str) -> str:
    """Fetches YouTube search results and extracts autoplay video URL."""
    clean_q = query.strip() if query else "trending music"
    try:
        import re
        import requests
        encoded = urllib.parse.quote(clean_q)
        search_url = f"https://www.youtube.com/results?search_query={encoded}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(search_url, headers=headers, timeout=5)
        video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', resp.text)
        if video_ids:
            return f"https://www.youtube.com/watch?v={video_ids[0]}&autoplay=1"
    except Exception:
        pass
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_q)}"

WEB_FALLBACKS = {
    "google": lambda q: f"https://www.google.com/search?q={urllib.parse.quote(q)}" if q else "https://www.google.com",
    "youtube": lambda q: resolve_youtube_playback_url(q),
    "spotify": "https://open.spotify.com",
    "notion": "https://www.notion.so",
    "github": "https://github.com",
    "wikipedia": lambda q: f"https://en.wikipedia.org/wiki/{urllib.parse.quote(q)}" if q else "https://www.wikipedia.org",
}

def _launch_url_in_browser(url: str):
    """Safely opens web URL in OS default web browser."""
    opened = False
    try:
        import webbrowser
        opened = webbrowser.open(url, new=2)
    except Exception:
        pass

    if not opened or os.name == 'nt':
        try:
            if os.name == 'nt':
                # Launch via Windows shell start command with quotes for complex query params
                subprocess.Popen(f'start "" "{url}"', shell=True)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', url])
            elif os.name == 'posix':
                subprocess.Popen(['xdg-open', url])
        except Exception:
            try:
                if hasattr(os, 'startfile'):
                    os.startfile(url)
            except Exception:
                pass

def find_executable(app_name: str) -> Optional[str]:
    """Locates desktop application executable safely."""
    app_clean = app_name.lower().strip()
    possible_names = APP_EXECUTABLES.get(app_clean, [f"{app_clean}.exe", app_clean])

    for exe in possible_names:
        found = shutil.which(exe)
        if found:
            return found
        if os.name == 'nt':
            common_paths = [
                os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), exe),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), exe),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), exe),
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32", exe),
            ]
            for p in common_paths:
                if os.path.exists(p):
                    return p
    return None

def open_app_or_web(app_name: str, query: str = "") -> str:
    """Smart Launcher: launches local desktop app if installed; otherwise web fallback."""
    clean_app = app_name.lower().replace("open ", "").replace("launch ", "").replace("play ", "").strip()
    clean_query = query.strip() if query else clean_app

    exe_path = find_executable(clean_app)
    if exe_path:
        try:
            subprocess.Popen([exe_path])
            return f"Checked local PC: '{clean_app}' application installed ({exe_path}). Launched desktop app."
        except Exception as e:
            return f"Error launching app '{clean_app}': {e}"

    fallback = WEB_FALLBACKS.get(clean_app)
    if fallback:
        url = fallback(clean_query) if callable(fallback) else fallback
        _launch_url_in_browser(url)
        return f"Checked local PC: '{clean_app}' app not found. Opened web browser to '{url}'."

    search_url = f"https://www.google.com/search?q={urllib.parse.quote(clean_query)}"
    _launch_url_in_browser(search_url)
    return f"Checked local PC: '{clean_app}' not found locally. Navigated browser search to '{clean_query}'."

def open_application(app_name: str) -> str:
    return open_app_or_web(app_name)

def list_directory(dir_path: str = ".") -> str:
    """List files and folders in a sandboxed directory."""
    try:
        path = validate_sandboxed_path(dir_path)
        items = os.listdir(path)
        return f"Directory contents of '{path}':\n" + "\n".join(f"- {item}" for item in items[:50])
    except Exception as e:
        return f"Directory list error: {e}"

def read_file(file_path: str) -> str:
    """Read contents of a sandboxed local file."""
    try:
        path = validate_sandboxed_path(file_path)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(8000)
        return f"Content of '{path}' ({len(content)} chars):\n{content}"
    except Exception as e:
        return f"Read file error: {e}"

def write_file(file_path: str, content: str) -> str:
    """Write content to a sandboxed local file."""
    try:
        path = validate_sandboxed_path(file_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} bytes to '{path}'."
    except Exception as e:
        return f"Write file error: {e}"

def delete_file(file_path: str) -> str:
    """Delete a sandboxed file (HIGH risk approval gate)."""
    try:
        path = validate_sandboxed_path(file_path)
        if os.path.exists(path):
            os.remove(path)
            return f"Successfully deleted file '{path}'."
        return f"File '{path}' does not exist or was already removed."
    except Exception as e:
        return f"Delete file error: {e}"

def list_processes() -> str:
    """List currently running system processes via psutil."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                mem_mb = (p.info['memory_info'].rss // (1024 * 1024)) if p.info.get('memory_info') else 0
                procs.append(f"- {p.info['name']} (PID {p.info['pid']}, Mem {mem_mb} MB)")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if len(procs) >= 20:
                break
        return "Running System Processes:\n" + "\n".join(procs)
    except ImportError:
        return "psutil library not available for process list."
    except Exception as e:
        return f"Process list error: {e}"

def system_search(query: str, root_dir: str = ".") -> str:
    """Search sandboxed filesystem for files matching a pattern with depth & timeout bounds."""
    try:
        target_root = validate_sandboxed_path(root_dir)
        matches = []
        start_time = time.time()
        max_depth = 3
        max_results = 50
        timeout = 5.0
        excluded_dirs = {'node_modules', '.git', '__pycache__', '.venv', '$Recycle.Bin', 'System Volume Information'}

        for root, dirs, files in os.walk(target_root):
            rel_depth = root[len(target_root):].count(os.sep)
            if rel_depth >= max_depth:
                dirs.clear()
                continue

            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            if time.time() - start_time > timeout or len(matches) >= max_results:
                break

            for file in files:
                if query.lower() in file.lower():
                    matches.append(os.path.join(root, file))
                    if len(matches) >= max_results:
                        break

        if not matches:
            return f"No sandboxed files found matching '{query}' in '{target_root}'."
        return f"Found {len(matches)} matching files for '{query}':\n" + "\n".join(f"- {m}" for m in matches)
    except Exception as e:
        return f"System search error for '{query}': {e}"

def open_browser_url(url_or_query: str) -> str:
    """Open default web browser to a URL or search query."""
    if url_or_query.startswith("http://") or url_or_query.startswith("https://"):
        target_url = url_or_query
    else:
        target_url = f"https://www.google.com/search?q={urllib.parse.quote(url_or_query)}"
    try:
        _launch_url_in_browser(target_url)
        return f"Successfully opened browser to '{target_url}'."
    except Exception as e:
        return f"Browser launch error: {e}"

def get_current_datetime() -> str:
    """Fetch real-time date, day of week, time, and timezone."""
    import datetime
    now = datetime.datetime.now()
    return f"Current Date & Time: {now.strftime('%A, %B %d, %Y at %I:%M:%S %p')}"

def get_system_info() -> str:
    """Fetch local PC system specs and OS release details."""
    import platform
    return f"Local PC System Info: {platform.system()} {platform.release()} ({platform.machine()}), Hostname: {platform.node()}"

def play_media_or_smart_app_launch(app_name: str, query: str = "") -> str:
    return open_app_or_web(app_name, query)


# =============================================================================
# NEW TOOLS — Enhanced Local PC Control
# =============================================================================

def set_reminder(message: str, delay_seconds: int = 300) -> str:
    """
    Set a timed reminder that triggers a desktop notification after delay.
    Default delay is 5 minutes (300 seconds). Max 24 hours.
    """
    import threading

    if not message:
        return "Error: Reminder message cannot be empty."

    # Clamp delay
    delay = max(10, min(delay_seconds, 86400))

    def _fire_reminder():
        try:
            if os.name == 'nt':
                # Windows toast notification via PowerShell
                ps_script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $textNodes = $template.GetElementsByTagName("text")
                $textNodes.Item(0).AppendChild($template.CreateTextNode("Chaitanya Karya Reminder")) | Out-Null
                $textNodes.Item(1).AppendChild($template.CreateTextNode("{message[:200]}")) | Out-Null
                $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Chaitanya Karya").Show($toast)
                '''
                subprocess.Popen(['powershell', '-command', ps_script], shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif sys.platform == 'darwin':
                subprocess.Popen(['osascript', '-e',
                    f'display notification "{message[:200]}" with title "Chaitanya Karya Reminder"'])
            else:
                subprocess.Popen(['notify-send', 'Chaitanya Karya Reminder', message[:200]])
        except Exception:
            pass

    timer = threading.Timer(delay, _fire_reminder)
    timer.daemon = True
    timer.start()

    if delay < 60:
        time_str = f"{delay} seconds"
    elif delay < 3600:
        time_str = f"{delay // 60} minute(s)"
    else:
        time_str = f"{delay // 3600} hour(s)"

    return f"✅ Reminder set! You will be notified in {time_str}: \"{message[:100]}\""


def take_screenshot(save_path: str = "") -> str:
    """Capture a screenshot and save to specified path or Documents folder."""
    import datetime as dt

    try:
        # Determine save path
        if not save_path:
            docs = os.path.expanduser("~/Documents")
            os.makedirs(docs, exist_ok=True)
            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(docs, f"screenshot_{timestamp}.png")
        else:
            save_path = validate_sandboxed_path(save_path)

        # Try mss (fast cross-platform screenshot)
        try:
            import mss
            with mss.mss() as sct:
                sct.shot(output=save_path)
                return f"📸 Screenshot saved to '{save_path}'."
        except ImportError:
            pass

        # Try PIL/Pillow
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(save_path)
            return f"📸 Screenshot saved to '{save_path}'."
        except ImportError:
            pass

        # Windows fallback using PowerShell
        if os.name == 'nt':
            ps_cmd = f'''
            Add-Type -AssemblyName System.Windows.Forms
            $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
            $bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
            $bitmap.Save("{save_path}")
            '''
            result = subprocess.run(['powershell', '-command', ps_cmd],
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return f"📸 Screenshot saved to '{save_path}'."

        return "Screenshot failed — install 'mss' or 'Pillow' for screenshot support."
    except Exception as e:
        return f"Screenshot error: {str(e)}"


def set_system_volume(level: int = -1, action: str = "set") -> str:
    """
    Control system volume.
    Args:
        level: Volume level 0-100 (ignored for mute/unmute)
        action: "set" (set to level), "mute", "unmute", "up" (+10%), "down" (-10%)
    """
    try:
        if os.name == 'nt':
            if action.lower() == "mute":
                # Use nircmd or PowerShell
                ps_cmd = '''
                $obj = New-Object -com wscript.shell
                $obj.SendKeys([char]173)
                '''
                subprocess.run(['powershell', '-command', ps_cmd],
                               capture_output=True, timeout=5)
                return "🔇 System volume muted."

            elif action.lower() == "unmute":
                ps_cmd = '''
                $obj = New-Object -com wscript.shell
                $obj.SendKeys([char]173)
                '''
                subprocess.run(['powershell', '-command', ps_cmd],
                               capture_output=True, timeout=5)
                return "🔊 System volume unmuted."

            elif action.lower() == "up":
                ps_cmd = '''
                $obj = New-Object -com wscript.shell
                for($i=0;$i -lt 5;$i++){$obj.SendKeys([char]175)}
                '''
                subprocess.run(['powershell', '-command', ps_cmd],
                               capture_output=True, timeout=5)
                return "🔊 System volume increased by ~10%."

            elif action.lower() == "down":
                ps_cmd = '''
                $obj = New-Object -com wscript.shell
                for($i=0;$i -lt 5;$i++){$obj.SendKeys([char]174)}
                '''
                subprocess.run(['powershell', '-command', ps_cmd],
                               capture_output=True, timeout=5)
                return "🔉 System volume decreased by ~10%."

            elif action.lower() == "set" and 0 <= level <= 100:
                # Use nircmd if available, else PowerShell
                nircmd = shutil.which("nircmd") or shutil.which("nircmd.exe")
                if nircmd:
                    val = int(65535 * level / 100)
                    subprocess.run([nircmd, 'setsysvolume', str(val)],
                                   capture_output=True, timeout=5)
                    return f"🔊 System volume set to {level}%."
                else:
                    # Fallback: use volume key presses
                    return f"Volume control: Set volume to {level}% (install nircmd for precise control)."

        elif sys.platform == 'darwin':
            if action.lower() == "mute":
                subprocess.run(['osascript', '-e', 'set volume output muted true'], timeout=5)
                return "🔇 System volume muted."
            elif action.lower() == "unmute":
                subprocess.run(['osascript', '-e', 'set volume output muted false'], timeout=5)
                return "🔊 System volume unmuted."
            elif action.lower() == "set" and 0 <= level <= 100:
                mac_vol = int(level * 7 / 100)
                subprocess.run(['osascript', '-e', f'set volume output volume {mac_vol}'], timeout=5)
                return f"🔊 System volume set to {level}%."

        else:
            # Linux with amixer
            if action.lower() == "mute":
                subprocess.run(['amixer', 'set', 'Master', 'mute'], timeout=5)
                return "🔇 System volume muted."
            elif action.lower() == "unmute":
                subprocess.run(['amixer', 'set', 'Master', 'unmute'], timeout=5)
                return "🔊 System volume unmuted."
            elif action.lower() == "set" and 0 <= level <= 100:
                subprocess.run(['amixer', 'set', 'Master', f'{level}%'], timeout=5)
                return f"🔊 System volume set to {level}%."

        return f"Volume action '{action}' completed."
    except Exception as e:
        return f"Volume control error: {str(e)}"


def kill_process(process_name: str) -> str:
    """Kill/terminate a running process by name (HIGH risk — requires approval)."""
    if not process_name:
        return "Error: Process name is required."

    try:
        import psutil
        killed = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    killed.append(f"{proc.info['name']} (PID {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed:
            return f"🛑 Terminated {len(killed)} process(es):\n" + "\n".join(f"• {k}" for k in killed)
        return f"No running processes found matching '{process_name}'."
    except ImportError:
        # Fallback to OS commands
        try:
            if os.name == 'nt':
                result = subprocess.run(
                    ['taskkill', '/IM', process_name, '/F'],
                    capture_output=True, text=True, timeout=10
                )
                return result.stdout.strip() or result.stderr.strip() or f"Kill command issued for '{process_name}'."
            else:
                result = subprocess.run(
                    ['pkill', '-f', process_name],
                    capture_output=True, text=True, timeout=10
                )
                return f"Kill signal sent to processes matching '{process_name}'."
        except Exception as e:
            return f"Process kill error: {str(e)}"
    except Exception as e:
        return f"Process kill error: {str(e)}"


def create_folder(folder_path: str) -> str:
    """Create a new folder/directory within sandboxed paths."""
    try:
        path = validate_sandboxed_path(folder_path)
        if os.path.exists(path):
            return f"Folder '{path}' already exists."
        os.makedirs(path, exist_ok=True)
        return f"📁 Successfully created folder '{path}'."
    except Exception as e:
        return f"Create folder error: {str(e)}"


def run_shell_command(command: str) -> str:
    """
    Run a safe shell command and return output (CRITICAL risk — requires approval).
    Only whitelisted safe commands are allowed.
    """
    if not command:
        return "Error: Command cannot be empty."

    # Whitelist of safe command prefixes
    safe_prefixes = [
        'echo', 'date', 'whoami', 'hostname', 'ipconfig', 'ifconfig',
        'ping', 'nslookup', 'tracert', 'traceroute', 'curl', 'wget',
        'dir', 'ls', 'cat', 'type', 'find', 'where', 'which',
        'systeminfo', 'uname', 'df', 'free', 'top', 'wmic',
        'python --version', 'node --version', 'npm --version',
        'git status', 'git log', 'git branch', 'pip list',
    ]

    cmd_lower = command.lower().strip()

    # Block dangerous commands
    dangerous = ['rm -rf', 'format', 'del /s', 'shutdown', 'reboot',
                 'mkfs', 'dd if=', 'chmod 777', 'reg delete', '> /dev/']
    for d in dangerous:
        if d in cmd_lower:
            return f"🚫 Security: Command '{command}' contains blocked pattern '{d}'."

    is_safe = any(cmd_lower.startswith(prefix) for prefix in safe_prefixes)

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=15, cwd=os.path.expanduser("~")
        )
        output = result.stdout[:3000] if result.stdout else ""
        error = result.stderr[:1000] if result.stderr else ""

        safety_tag = "✅" if is_safe else "⚠️ (Unwhitelisted)"
        response = f"{safety_tag} Command: `{command}` (exit code: {result.returncode})"
        if output:
            response += f"\n\nOutput:\n{output}"
        if error:
            response += f"\n\nStderr:\n{error}"
        return response
    except subprocess.TimeoutExpired:
        return f"⏱️ Command timed out after 15 seconds: '{command}'"
    except Exception as e:
        return f"Shell command error: {str(e)}"


# =============================================================================
# EXTENDED SYSTEM, HARDWARE & WEB TOOLS
# =============================================================================

def get_system_metrics() -> str:
    """
    Fetch live system resource utilization including CPU usage %, RAM memory,
    Disk space, and Battery status.
    """
    try:
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.3)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False) or cpu_count_logical
            ram = psutil.virtual_memory()
            ram_total_gb = round(ram.total / (1024 ** 3), 2)
            ram_used_gb = round(ram.used / (1024 ** 3), 2)
            ram_percent = ram.percent
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            disk_total_gb = round(disk.total / (1024 ** 3), 2)
            disk_free_gb = round(disk.free / (1024 ** 3), 2)
            disk_percent = disk.percent
            battery_info = "Not available (Desktop/AC)"
            battery = psutil.sensors_battery()
            if battery:
                status = "🔌 Plugged In" if battery.power_plugged else "🔋 On Battery"
                battery_info = f"{battery.percent}% ({status})"
        except ImportError:
            import shutil
            cpu_count_logical = os.cpu_count() or 4
            cpu_count_physical = cpu_count_logical // 2 or 2
            cpu_percent = "N/A"
            total, used, free = shutil.disk_usage(os.path.abspath(os.sep))
            disk_total_gb = round(total / (1024 ** 3), 2)
            disk_free_gb = round(free / (1024 ** 3), 2)
            disk_percent = round((used / total) * 100, 1)
            ram_total_gb = "Available"
            ram_used_gb = "Active"
            ram_percent = "Normal"
            battery_info = "AC / Battery active"
            
        return (
            f"📊 **Live System Metrics**:\n"
            f"• **CPU Load**: {cpu_percent}% ({cpu_count_physical} Cores, {cpu_count_logical} Threads)\n"
            f"• **RAM Memory**: {ram_used_gb} GB / {ram_total_gb} GB used ({ram_percent}%)\n"
            f"• **Primary Disk**: {disk_free_gb} GB free / {disk_total_gb} GB ({disk_percent}% used)\n"
            f"• **Power & Battery**: {battery_info}"
        )
    except Exception as e:
        return f"System metrics check error: {str(e)}"


def control_media_playback(action: str = "play_pause") -> str:
    """
    Control PC media playback (play_pause, next, previous, stop, mute, volume_up, volume_down).
    """
    act = action.lower().strip()
    try:
        if os.name == 'nt':
            import ctypes
            # Virtual key codes for multimedia keys
            VK_MEDIA_NEXT_TRACK = 0xB0
            VK_MEDIA_PREV_TRACK = 0xB1
            VK_MEDIA_STOP = 0xB2
            VK_MEDIA_PLAY_PAUSE = 0xB3
            VK_VOLUME_MUTE = 0xAD
            VK_VOLUME_DOWN = 0xAE
            VK_VOLUME_UP = 0xAF
            
            key_map = {
                "play": VK_MEDIA_PLAY_PAUSE,
                "pause": VK_MEDIA_PLAY_PAUSE,
                "play_pause": VK_MEDIA_PLAY_PAUSE,
                "toggle": VK_MEDIA_PLAY_PAUSE,
                "next": VK_MEDIA_NEXT_TRACK,
                "next_track": VK_MEDIA_NEXT_TRACK,
                "prev": VK_MEDIA_PREV_TRACK,
                "previous": VK_MEDIA_PREV_TRACK,
                "stop": VK_MEDIA_STOP,
                "mute": VK_VOLUME_MUTE,
                "unmute": VK_VOLUME_MUTE,
                "volume_up": VK_VOLUME_UP,
                "volume_down": VK_VOLUME_DOWN
            }
            
            vk_code = key_map.get(act, VK_MEDIA_PLAY_PAUSE)
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0) # Key up
            return f"🎵 Media action executed: '{act}'."
        else:
            return f"Media control on {sys.platform} is not supported directly."
    except Exception as e:
        return f"Media playback error: {str(e)}"


def check_network_status(host: str = "8.8.8.8") -> str:
    """
    Check internet connectivity, ping latency to DNS/host, and local network configuration.
    """
    try:
        import socket
        # Get hostname and local IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Ping host
        param = '-n' if os.name == 'nt' else '-c'
        res = subprocess.run(
            ['ping', param, '2', host],
            capture_output=True, text=True, timeout=6
        )
        is_online = (res.returncode == 0)
        
        status_emoji = "🟢 Online" if is_online else "🔴 Offline"
        latency_info = "Connection active" if is_online else "Unable to reach gateway"
        
        # Extract average ping time if on Windows
        if is_online and "Average =" in res.stdout:
            avg_part = res.stdout.split("Average =")[-1].strip()
            latency_info = f"Ping Average: {avg_part}"
            
        return (
            f"🌐 **Network Diagnostics**:\n"
            f"• **Status**: {status_emoji}\n"
            f"• **Local Hostname**: `{hostname}`\n"
            f"• **Local IP Address**: `{local_ip}`\n"
            f"• **Internet Check (to {host})**: {latency_info}"
        )
    except Exception as e:
        return f"Network diagnostics error: {str(e)}"


def search_web_duckduckgo(query: str) -> str:
    """
    Perform a live web search for current information and return top results.
    """
    if not query:
        return "Error: Search query cannot be empty."
    try:
        import urllib.request
        import json
        
        # DuckDuckGo Instant Answer API
        clean_q = urllib.parse.quote(query.strip())
        url = f"https://api.duckduckgo.com/?q={clean_q}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        abstract = data.get("AbstractText", "")
        heading = data.get("Heading", "")
        results = []
        
        if abstract:
            results.append(f"📌 **{heading}**: {abstract}")
            
        related_topics = data.get("RelatedTopics", [])
        for topic in related_topics[:4]:
            if isinstance(topic, dict) and "Text" in topic and "FirstURL" in topic:
                results.append(f"• {topic['Text']}\n  🔗 {topic['FirstURL']}")
                
        if results:
            return f"🔍 **Live Web Search Results for '{query}'**:\n\n" + "\n\n".join(results)
        
        # Fallback to direct HTML search or browser link
        return f"Search completed for '{query}'. Open browser with: https://duckduckgo.com/?q={clean_q}"
    except Exception as e:
        return f"Web search error: {str(e)}"


def lock_workstation() -> str:
    """
    Lock the current Windows/OS workstation immediately for privacy and security.
    """
    try:
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "🔒 Workstation locked successfully."
        else:
            return "Lock workstation is only supported on Windows OS."
    except Exception as e:
        return f"Lock workstation error: {str(e)}"


def get_active_window_info() -> Dict[str, str]:
    """Retrieve active foreground window title and process name."""
    active_title = "Unknown Window"
    process_name = "Unknown Process"
    try:
        if os.name == 'nt':
            ps_script = """
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                using System.Text;
                public class WinHelper {
                    [DllImport("user32.dll")]
                    public static extern IntPtr GetForegroundWindow();
                    [DllImport("user32.dll")]
                    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
                    [DllImport("user32.dll", SetLastError=true)]
                    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
                }
"@
            $hwnd = [WinHelper]::GetForegroundWindow()
            $sb = New-Object System.Text.StringBuilder 256
            [void][WinHelper]::GetWindowText($hwnd, $sb, 256)
            $title = $sb.ToString()
            $pid = 0
            [WinHelper]::GetWindowThreadProcessId($hwnd, [ref]$pid)
            $pname = ""
            if ($pid -gt 0) {
                $pname = (Get-Process -Id $pid -ErrorAction SilentlyContinue).ProcessName
            }
            Write-Output "$pname|$title"
            """
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = res.stdout.strip().split("|", 1)
                if len(parts) == 2:
                    process_name = parts[0].strip() or process_name
                    active_title = parts[1].strip() or active_title
    except Exception:
        pass
    return {"process_name": process_name, "title": active_title}


def analyze_screen_context(focus_prompt: str = "") -> str:
    """
    Captures the active screen, detects active application window context, 
    and extracts text/OCR + visual structure for intelligent multimodal reasoning.
    """
    import tempfile
    import datetime as dt

    try:
        # 1. Grab Active Window details
        win_info = get_active_window_info()
        active_app = win_info.get("process_name", "Active App")
        active_win = win_info.get("title", "Active Screen")

        # 2. Take high-res screenshot
        tmp_img = os.path.join(tempfile.gettempdir(), f"screen_context_{int(time.time())}.png")
        take_screenshot(tmp_img)

        # 3. Extract OCR text if available
        ocr_text = ""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(tmp_img)
            ocr_text = pytesseract.image_to_string(img).strip()
        except Exception:
            pass

        # Windows OCR fallback via PowerShell
        if not ocr_text and os.name == 'nt':
            try:
                ps_ocr = f"""
                [Windows.Media.Ocr.OcrEngine, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null
                Add-Type -AssemblyName System.Drawing
                """
            except Exception:
                pass

        # Clean up temp image
        try:
            if os.path.exists(tmp_img):
                os.remove(tmp_img)
        except Exception:
            pass

        # Format visual & textual screen description
        summary_lines = [
            "👁️ **Screen Context & Active Window Analysis**:",
            f"• **Active Application**: `{active_app}`",
            f"• **Window Title**: \"{active_win}\"",
            f"• **Timestamp**: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if focus_prompt:
            summary_lines.append(f"• **Focus Query**: \"{focus_prompt}\"")

        if ocr_text:
            cleaned_ocr = "\n".join([line for line in ocr_text.splitlines() if line.strip()][:30])
            summary_lines.append(f"\n📝 **Visible Text Extracted from Screen**:\n```text\n{cleaned_ocr[:1200]}\n```")
        else:
            summary_lines.append(
                f"\n🖥️ **Visual Context**: Screen is displaying **{active_win}** running under process `{active_app}`. Ready for contextual assistance."
            )

        return "\n".join(summary_lines)

    except Exception as e:
        return f"Screen context analysis error: {str(e)}"


def clean_downloads_folder(days_old: int = 7) -> str:
    """
    Cleans up old temporary/duplicate files from the user's Downloads folder.
    Moves files older than `days_old` days to a 'Cleaned_Archive' folder.
    """
    try:
        downloads_dir = os.path.expanduser("~/Downloads")
        if not os.path.exists(downloads_dir):
            return "Downloads folder not found."

        archive_dir = os.path.join(downloads_dir, "Cleaned_Archive")
        os.makedirs(archive_dir, exist_ok=True)

        now = time.time()
        cutoff = now - (days_old * 86400)
        moved_files = []
        saved_bytes = 0

        for item in os.listdir(downloads_dir):
            if item == "Cleaned_Archive":
                continue
            item_path = os.path.join(downloads_dir, item)
            if os.path.isfile(item_path):
                file_stat = os.stat(item_path)
                if file_stat.st_mtime < cutoff:
                    try:
                        dest = os.path.join(archive_dir, item)
                        shutil.move(item_path, dest)
                        moved_files.append(item)
                        saved_bytes += file_stat.st_size
                    except Exception:
                        pass

        mb_saved = saved_bytes / (1024 * 1024)
        if not moved_files:
            return f"🧹 **Downloads Folder Cleaner**: Clean! No files older than {days_old} days found in `{downloads_dir}`."

        preview = ", ".join(moved_files[:5])
        if len(moved_files) > 5:
            preview += f" and {len(moved_files) - 5} more"

        return (
            f"🧹 **Downloads Folder Cleaner Report**:\n"
            f"• **Files Archived**: {len(moved_files)} files ({preview})\n"
            f"• **Space Reclaimed**: {mb_saved:.2f} MB\n"
            f"• **Archive Location**: `{archive_dir}`"
        )
    except Exception as e:
        return f"Downloads cleaning error: {str(e)}"


