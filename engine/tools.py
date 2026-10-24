import os
import re
import sys
import time
import shutil
import datetime
import subprocess
import webbrowser
from pathlib import Path

try:
    import pyautogui
    pyautogui.PAUSE = 0.05
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

try:
    import psutil
except ImportError:
    psutil = None

# User common directory shortcuts
HOME_DIR = Path.home()
DESKTOP_DIR = HOME_DIR / "Desktop"
DOCUMENTS_DIR = HOME_DIR / "Documents"
DOWNLOADS_DIR = HOME_DIR / "Downloads"
PICTURES_DIR = HOME_DIR / "Pictures"

# Tool Registry
TOOL_REGISTRY = {}

class Tool:
    def __init__(self, name, description, parameters, func, tier="SAFE"):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func
        self.tier = tier  # "SAFE", "WRITE", "DESTRUCTIVE"

    def to_schema(self):
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "tier": self.tier
        }

def register_tool(name, description, parameters, tier="SAFE"):
    def decorator(func):
        TOOL_REGISTRY[name] = Tool(name, description, parameters, func, tier)
        return func
    return decorator

# ==============================================================================
# 1. APPLICATION & WINDOW MANAGEMENT TOOLS
# ==============================================================================

@register_tool(
    name="open_app",
    description="Opens an installed application, tool, or website on Windows by name (e.g. 'chrome', 'vs code', 'notepad', 'calculator', 'word', 'excel', 'spotify', 'vlc').",
    parameters={
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "Name of application or website to open"}
        },
        "required": ["app_name"]
    },
    tier="SAFE"
)
def tool_open_app(app_name: str) -> dict:
    from engine.system_control import open_app_or_web
    res = open_app_or_web(app_name)
    if res:
        return {"success": True, "message": f"Successfully launched {app_name}"}
    return {"success": False, "error": f"Could not find or open application: {app_name}"}

@register_tool(
    name="close_app",
    description="Closes a running application or process on Windows gracefully (e.g. 'chrome', 'edge', 'notepad', 'calculator', 'vs code', 'spotify', 'word').",
    parameters={
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "Name of application or process to close"}
        },
        "required": ["app_name"]
    },
    tier="SAFE"
)
def tool_close_app(app_name: str) -> dict:
    from engine.system_control import close_app
    res = close_app(f"close {app_name}")
    return {"success": res, "message": f"Closed {app_name}" if res else f"Could not close {app_name}"}

@register_tool(
    name="close_tab",
    description="Closes the active browser tab (Ctrl+W) or all open tabs in the browser window (Ctrl+Shift+W).",
    parameters={
        "type": "object",
        "properties": {
            "all_tabs": {"type": "boolean", "description": "True to close all tabs, False for only current active tab"}
        }
    },
    tier="SAFE"
)
def tool_close_tab(all_tabs: bool = False) -> dict:
    if not pyautogui:
        return {"success": False, "error": "PyAutoGUI not available"}
    if all_tabs:
        pyautogui.hotkey('ctrl', 'shift', 'w')
        return {"success": True, "message": "Closed all browser tabs"}
    else:
        pyautogui.hotkey('ctrl', 'w')
        return {"success": True, "message": "Closed active tab"}

@register_tool(
    name="window_action",
    description="Performs window state manipulation: 'maximize', 'minimize', 'show_desktop', 'switch_window', 'snap_left', 'snap_right', 'fullscreen'.",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["maximize", "minimize", "show_desktop", "switch_window", "snap_left", "snap_right", "fullscreen"],
                "description": "Window action to perform"
            }
        },
        "required": ["action"]
    },
    tier="SAFE"
)
def tool_window_action(action: str) -> dict:
    from engine.system_control import window_control
    window_control(action)
    return {"success": True, "message": f"Window action {action} completed"}

@register_tool(
    name="open_settings",
    description="Opens a specific Windows Settings page (e.g. 'wifi', 'bluetooth', 'display', 'sound', 'apps', 'windows update').",
    parameters={
        "type": "object",
        "properties": {
            "setting_page": {
                "type": "string",
                "enum": ["wifi", "bluetooth", "display", "sound", "apps", "windows update", "main"],
                "description": "Settings category"
            }
        },
        "required": ["setting_page"]
    },
    tier="SAFE"
)
def tool_open_settings(setting_page: str) -> dict:
    uri_map = {
        "wifi": "ms-settings:network-wifi",
        "bluetooth": "ms-settings:bluetooth",
        "display": "ms-settings:display",
        "sound": "ms-settings:sound",
        "apps": "ms-settings:appsfeatures",
        "windows update": "ms-settings:windowsupdate",
        "main": "ms-settings:"
    }
    uri = uri_map.get(setting_page.lower(), "ms-settings:")
    subprocess.Popen(f'start {uri}', shell=True)
    return {"success": True, "message": f"Opened Windows {setting_page} settings"}

# ==============================================================================
# 2. KEYBOARD & MOUSE AUTOMATION TOOLS
# ==============================================================================

@register_tool(
    name="keyboard_shortcut",
    description="Sends a keyboard shortcut (e.g. 'ctrl+c', 'ctrl+v', 'ctrl+s', 'alt+tab', 'ctrl+t', 'ctrl+shift+t', 'ctrl+w', 'ctrl+a', 'f5').",
    parameters={
        "type": "object",
        "properties": {
            "shortcut": {"type": "string", "description": "Key combinations separated by '+', e.g. 'ctrl+s'"}
        },
        "required": ["shortcut"]
    },
    tier="SAFE"
)
def tool_keyboard_shortcut(shortcut: str) -> dict:
    if not pyautogui:
        return {"success": False, "error": "PyAutoGUI not available"}
    keys = [k.strip().lower() for k in shortcut.split("+")]
    try:
        pyautogui.hotkey(*keys)
        return {"success": True, "message": f"Executed shortcut: {shortcut}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="type_text",
    description="Types text into the currently active window or input box.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text content to type"}
        },
        "required": ["text"]
    },
    tier="SAFE"
)
def tool_type_text(text: str) -> dict:
    if not pyautogui:
        return {"success": False, "error": "PyAutoGUI not available"}
    time.sleep(0.3)
    pyautogui.write(text, interval=0.01)
    return {"success": True, "message": f"Typed {len(text)} characters"}

@register_tool(
    name="press_key",
    description="Presses a single keyboard key (e.g. 'enter', 'esc', 'tab', 'backspace', 'home', 'end', 'space').",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Key name"}
        },
        "required": ["key"]
    },
    tier="SAFE"
)
def tool_press_key(key: str) -> dict:
    if not pyautogui:
        return {"success": False, "error": "PyAutoGUI not available"}
    pyautogui.press(key.lower())
    return {"success": True, "message": f"Pressed key: {key}"}

@register_tool(
    name="scroll_screen",
    description="Scrolls the active window 'up', 'down', 'top', or 'bottom'.",
    parameters={
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["up", "down", "top", "bottom"],
                "description": "Scroll direction"
            },
            "amount": {"type": "integer", "description": "Number of scroll clicks, default 600"}
        },
        "required": ["direction"]
    },
    tier="SAFE"
)
def tool_scroll_screen(direction: str, amount: int = 600) -> dict:
    if not pyautogui:
        return {"success": False, "error": "PyAutoGUI not available"}
    if direction == "top":
        pyautogui.press('home')
    elif direction == "bottom":
        pyautogui.press('end')
    elif direction == "up":
        pyautogui.scroll(amount)
    else:
        pyautogui.scroll(-amount)
    return {"success": True, "message": f"Scrolled {direction}"}

# ==============================================================================
# 3. FILE SYSTEM & CODE AUTOMATION TOOLS
# ==============================================================================

def _resolve_dir(path_str: str) -> Path:
    p = Path(path_str.strip())
    alias = path_str.strip().lower()
    if alias in ["desktop", "my desktop"]:
        return DESKTOP_DIR
    elif alias in ["documents", "my documents"]:
        return DOCUMENTS_DIR
    elif alias in ["downloads", "my downloads"]:
        return DOWNLOADS_DIR
    elif alias in ["pictures", "my pictures"]:
        return PICTURES_DIR
    elif alias in ["project", "cwd", "here"]:
        return Path(__file__).resolve().parent.parent

    if p.is_absolute():
        return p

    first_part = p.parts[0].lower() if p.parts else ""
    remaining = Path(*p.parts[1:]) if len(p.parts) > 1 else Path(".")

    if first_part in ["desktop", "my desktop"]:
        return DESKTOP_DIR / remaining
    elif first_part in ["documents", "my documents"]:
        return DOCUMENTS_DIR / remaining
    elif first_part in ["downloads", "my downloads"]:
        return DOWNLOADS_DIR / remaining
    elif first_part in ["pictures", "my pictures"]:
        return PICTURES_DIR / remaining
    elif first_part in ["project", "cwd", "here"]:
        return Path(__file__).resolve().parent.parent / remaining

    return DESKTOP_DIR / p

@register_tool(
    name="list_directory",
    description="Lists files and folders inside a given directory (e.g. 'Desktop', 'Documents', 'Downloads', or specific path).",
    parameters={
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Directory to list, defaults to 'Desktop'"}
        }
    },
    tier="SAFE"
)
def tool_list_directory(directory: str = "Desktop") -> dict:
    target = _resolve_dir(directory)
    if not target.exists():
        return {"success": False, "error": f"Directory not found: {target}"}
    items = []
    try:
        for entry in list(target.iterdir())[:40]:
            items.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size_kb": round(entry.stat().st_size / 1024, 1) if entry.is_file() else None
            })
        return {"success": True, "path": str(target), "count": len(items), "items": items}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="search_files",
    description="Recursively searches for files matching a pattern (e.g. '*.py', '*.docx', '*.pdf', 'report*') inside a directory.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern to match, e.g. '*.py' or '*test*'"},
            "directory": {"type": "string", "description": "Directory to search in, defaults to 'Desktop'"},
            "max_results": {"type": "integer", "description": "Maximum number of results to return, default 20"}
        },
        "required": ["pattern"]
    },
    tier="SAFE"
)
def tool_search_files(pattern: str, directory: str = "Desktop", max_results: int = 20) -> dict:
    target = _resolve_dir(directory)
    if not target.exists():
        return {"success": False, "error": f"Directory does not exist: {target}"}
    matches = []
    try:
        for p in target.rglob(pattern):
            if len(matches) >= max_results:
                break
            try:
                matches.append({
                    "path": str(p),
                    "name": p.name,
                    "size_kb": round(p.stat().st_size / 1024, 1) if p.is_file() else 0
                })
            except Exception:
                continue
        return {"success": True, "count": len(matches), "matches": matches}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="find_large_files",
    description="Scans a directory to find the largest files taking up disk space.",
    parameters={
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Directory to search, defaults to 'Downloads' or 'Documents'"},
            "min_size_mb": {"type": "integer", "description": "Minimum file size in MB, default 20"},
            "top_n": {"type": "integer", "description": "Number of largest files to return, default 10"}
        }
    },
    tier="SAFE"
)
def tool_find_large_files(directory: str = "Downloads", min_size_mb: int = 20, top_n: int = 10) -> dict:
    target = _resolve_dir(directory)
    if not target.exists():
        return {"success": False, "error": f"Directory does not exist: {target}"}
    large_files = []
    min_bytes = min_size_mb * 1024 * 1024
    try:
        for p in target.rglob("*"):
            try:
                if p.is_file():
                    sz = p.stat().st_size
                    if sz >= min_bytes:
                        large_files.append({
                            "path": str(p),
                            "name": p.name,
                            "size_mb": round(sz / (1024 * 1024), 2)
                        })
            except Exception:
                continue
        large_files.sort(key=lambda x: x["size_mb"], reverse=True)
        return {"success": True, "count": len(large_files[:top_n]), "files": large_files[:top_n]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="read_file",
    description="Reads and returns the text content of a file (code, config, notes, markdown).",
    parameters={
        "type": "object",
        "properties": {
            "filepath": {"type": "string", "description": "Path to file to read"},
            "max_lines": {"type": "integer", "description": "Maximum number of lines to read, default 150"}
        },
        "required": ["filepath"]
    },
    tier="SAFE"
)
def tool_read_file(filepath: str, max_lines: int = 150) -> dict:
    target = _resolve_dir(filepath)
    if not target.exists() or not target.is_file():
        return {"success": False, "error": f"File does not exist: {target}"}
    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(max_lines)]
            content = "".join(lines)
        return {"success": True, "filepath": str(target), "lines_read": len(lines), "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="write_file",
    description="Creates a new file or writes/appends content to an existing file.",
    parameters={
        "type": "object",
        "properties": {
            "filepath": {"type": "string", "description": "Path where file should be created or updated"},
            "content": {"type": "string", "description": "Text content to write into file"},
            "mode": {"type": "string", "enum": ["w", "a"], "description": "'w' to overwrite/create, 'a' to append"}
        },
        "required": ["filepath", "content"]
    },
    tier="WRITE"
)
def tool_write_file(filepath: str, content: str, mode: str = "w") -> dict:
    target = _resolve_dir(filepath)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, mode, encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "filepath": str(target), "bytes_written": len(content)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="create_folder",
    description="Creates a new folder at the specified directory path (e.g. 'Desktop/ProjectReports').",
    parameters={
        "type": "object",
        "properties": {
            "folder_path": {"type": "string", "description": "Path of the folder to create"}
        },
        "required": ["folder_path"]
    },
    tier="WRITE"
)
def tool_create_folder(folder_path: str) -> dict:
    target = _resolve_dir(folder_path)
    try:
        target.mkdir(parents=True, exist_ok=True)
        return {"success": True, "path": str(target), "message": f"Created folder {target.name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="organize_files",
    description="Organizes files in a directory into categorized subfolders (Documents, Python_Code, Images, Archives, Audio).",
    parameters={
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Directory to organize, defaults to 'Desktop'"}
        }
    },
    tier="WRITE"
)
def tool_organize_files(directory: str = "Desktop") -> dict:
    target = _resolve_dir(directory)
    if not target.exists():
        return {"success": False, "error": f"Directory not found: {target}"}

    category_map = {
        "Python_Code": [".py", ".ipynb"],
        "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv"],
        "Images": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".bmp"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "Audio_Video": [".mp3", ".wav", ".mp4", ".mkv", ".avi"]
    }

    moved_count = 0
    try:
        for item in list(target.iterdir()):
            if item.is_file():
                ext = item.suffix.lower()
                for cat, extensions in category_map.items():
                    if ext in extensions:
                        cat_dir = target / cat
                        cat_dir.mkdir(exist_ok=True)
                        dest = cat_dir / item.name
                        if not dest.exists():
                            shutil.move(str(item), str(dest))
                            moved_count += 1
                        break
        return {"success": True, "message": f"Organized {moved_count} files into categories in {target.name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="delete_file",
    description="Permanently deletes a file. Destructive operation that enforces permission verification.",
    parameters={
        "type": "object",
        "properties": {
            "filepath": {"type": "string", "description": "Path of file to delete"}
        },
        "required": ["filepath"]
    },
    tier="DESTRUCTIVE"
)
def tool_delete_file(filepath: str) -> dict:
    target = _resolve_dir(filepath)
    if not target.exists() or not target.is_file():
        return {"success": False, "error": f"File does not exist: {target}"}
    try:
        target.unlink()
        return {"success": True, "message": f"Deleted file {target.name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==============================================================================
# 4. TERMINAL & CODE EXECUTION TOOLS
# ==============================================================================

@register_tool(
    name="execute_terminal_command",
    description="Executes a shell command on Windows PowerShell and returns stdout, stderr, and exit code. Useful for running scripts, git commands, npm, pip, diagnostics.",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command string to execute"},
            "cwd": {"type": "string", "description": "Working directory, defaults to project root or Desktop"},
            "timeout": {"type": "integer", "description": "Execution timeout in seconds, default 30"}
        },
        "required": ["command"]
    },
    tier="SAFE"
)
def tool_execute_terminal_command(command: str, cwd: str = None, timeout: int = 30) -> dict:
    # Security filter against malicious or system-destructive commands
    blocked_patterns = [
        r"format\s+[a-z]:",
        r"del\s+/[a-z\s]*c:\\windows",
        r"rmdir\s+/[a-z\s]*c:\\",
        r":\(\)\s*\{",  # fork bomb
        r"bcdedit",
    ]
    for pat in blocked_patterns:
        if re.search(pat, command, re.IGNORECASE):
            return {"success": False, "error": "Command blocked by security policy"}

    working_dir = str(_resolve_dir(cwd)) if cwd else str(Path(__file__).resolve().parent.parent)

    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout} seconds"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="run_python_script",
    description="Runs a Python script using the active project virtual environment and captures output.",
    parameters={
        "type": "object",
        "properties": {
            "script_path": {"type": "string", "description": "Path to Python script"},
            "args": {"type": "string", "description": "Command line arguments string"}
        },
        "required": ["script_path"]
    },
    tier="SAFE"
)
def tool_run_python_script(script_path: str, args: str = "") -> dict:
    target = _resolve_dir(script_path)
    if not target.exists():
        return {"success": False, "error": f"Python script not found: {target}"}

    python_exe = sys.executable
    cmd = f'"{python_exe}" "{target}" {args}'.strip()
    return tool_execute_terminal_command(cmd, cwd=str(target.parent), timeout=45)

@register_tool(
    name="install_python_packages",
    description="Installs Python packages into the environment using pip.",
    parameters={
        "type": "object",
        "properties": {
            "packages": {"type": "string", "description": "Space-separated package names, e.g. 'requests pandas'"}
        },
        "required": ["packages"]
    },
    tier="WRITE"
)
def tool_install_python_packages(packages: str) -> dict:
    python_exe = sys.executable
    cmd = f'"{python_exe}" -m pip install {packages}'
    return tool_execute_terminal_command(cmd, timeout=90)

# ==============================================================================
# 5. BROWSER & WEB RESEARCH TOOLS
# ==============================================================================

@register_tool(
    name="web_search",
    description="Performs a Google search in browser or retrieves search query URL.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Keywords to search for"}
        },
        "required": ["query"]
    },
    tier="SAFE"
)
def tool_web_search(query: str) -> dict:
    from engine.system_control import google_search
    google_search(query)
    return {"success": True, "message": f"Searched Google for: {query}"}

@register_tool(
    name="open_website",
    description="Opens any web URL in the default web browser (e.g. 'https://github.com', 'https://youtube.com').",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Full URL or website domain to open"}
        },
        "required": ["url"]
    },
    tier="SAFE"
)
def tool_open_website(url: str) -> dict:
    clean_url = url.strip()
    if not clean_url.startswith("http"):
        clean_url = f"https://{clean_url}"
    subprocess.Popen(f'start "" "{clean_url}"', shell=True)
    return {"success": True, "message": f"Opened {clean_url}"}

@register_tool(
    name="play_youtube_video",
    description="Searches YouTube and starts playback for a specific song, artist, video, or tutorial.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Song or video name"}
        },
        "required": ["query"]
    },
    tier="SAFE"
)
def tool_play_youtube_video(query: str) -> dict:
    from engine.feature import PlayYoutube
    PlayYoutube(query)
    return {"success": True, "message": f"Playing {query} on YouTube"}

# ==============================================================================
# 6. SYSTEM MONITORING & PRODUCTIVITY TOOLS
# ==============================================================================

@register_tool(
    name="get_system_diagnostics",
    description="Returns current CPU usage, RAM utilization, Disk space, and Battery status.",
    parameters={"type": "object", "properties": {}},
    tier="SAFE"
)
def tool_get_system_diagnostics() -> dict:
    from engine.system_control import system_stats
    stats_msg = system_stats()
    return {"success": True, "diagnostics": stats_msg}

@register_tool(
    name="get_running_processes",
    description="Lists the top running applications and background processes.",
    parameters={
        "type": "object",
        "properties": {
            "top_n": {"type": "integer", "description": "Number of top processes to return, default 10"}
        }
    },
    tier="SAFE"
)
def tool_get_running_processes(top_n: int = 10) -> dict:
    if not psutil:
        return {"success": False, "error": "psutil not available"}
    procs = []
    for p in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
        try:
            procs.append({
                "name": p.info['name'],
                "memory_mb": round(p.info['memory_info'].rss / (1024 * 1024), 1)
            })
        except Exception:
            continue
    procs.sort(key=lambda x: x["memory_mb"], reverse=True)
    return {"success": True, "top_processes": procs[:top_n]}

@register_tool(
    name="create_report",
    description="Creates a formatted text report or summary document on Desktop or Documents.",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title of report"},
            "content": {"type": "string", "description": "Body text/summary of report"},
            "folder": {"type": "string", "description": "'Desktop' or 'Documents', default 'Desktop'"}
        },
        "required": ["title", "content"]
    },
    tier="WRITE"
)
def tool_create_report(title: str, content: str, folder: str = "Desktop") -> dict:
    target_dir = _resolve_dir(folder)
    safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
    filename = f"{safe_title}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = target_dir / filename
    
    report_text = f"========================================\n{title.upper()}\nGenerated: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n========================================\n\n{content}\n"
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_text)
        return {"success": True, "filepath": str(filepath), "message": f"Report saved to {filepath.name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="get_active_window_info",
    description="Detects and returns details about the currently active foreground window (title, application name, window type).",
    parameters={"type": "object", "properties": {}},
    tier="SAFE"
)
def tool_get_active_window_info() -> dict:
    try:
        import win32gui
        import win32process
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd).strip()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc_name = "unknown"
        if psutil and pid:
            try:
                proc_name = psutil.Process(pid).name()
            except Exception:
                pass
        is_browser = any(b in proc_name.lower() or b in title.lower() for b in ["chrome", "edge", "msedge", "firefox", "brave", "opera"])
        return {
            "success": True,
            "hwnd": hwnd,
            "window_title": title,
            "process_name": proc_name,
            "is_browser": is_browser
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="get_current_tab_url",
    description="Extracts the current URL from the active browser tab (Chrome, Edge, Firefox, Brave) using address bar automation.",
    parameters={"type": "object", "properties": {}},
    tier="SAFE"
)
def tool_get_current_tab_url() -> dict:
    if not pyautogui:
        return {"success": False, "error": "PyAutoGUI not available"}
    try:
        import pyperclip
        old_cb = pyperclip.paste()
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.12)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.12)
        pyautogui.press('esc')
        url = pyperclip.paste().strip()
        if url.startswith("http://") or url.startswith("https://") or "www." in url or ".com" in url:
            return {"success": True, "url": url}
        pyperclip.copy(old_cb)
        return {"success": False, "error": "Could not extract valid URL from active window"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="analyze_current_window_or_tab",
    description="Takes an instant screenshot of the current active window or tab and analyzes its contents using AI Vision. Can summarize the current webpage, explain code on screen, read error messages, or inspect what the user is looking at.",
    parameters={
        "type": "object",
        "properties": {
            "instruction": {
                "type": "string",
                "description": "Specific question or instruction about the current screen/tab (e.g. 'Summarize this webpage', 'Explain the code', 'What error is shown?')"
            }
        },
        "required": ["instruction"]
    },
    tier="SAFE"
)
def tool_analyze_current_window_or_tab(instruction: str) -> dict:
    if not pyautogui:
        return {"success": False, "error": "PyAutoGUI not available"}
    try:
        from engine.config import GENAI_API_KEY
        import google.generativeai as genai
        genai.configure(api_key=GENAI_API_KEY, transport='rest')

        screenshot = None
        try:
            screenshot = pyautogui.screenshot()
        except Exception:
            try:
                from PIL import ImageGrab
                screenshot = ImageGrab.grab()
            except Exception:
                screenshot = None

        model = genai.GenerativeModel("gemini-3.5-flash-lite")

        if screenshot is not None:
            prompt = f"""You are analyzing a screenshot of the user's current computer screen/active tab.
User Request: "{instruction}"

Carefully inspect the visual content of the screen (text, headers, tabs, code, articles, or errors).
Provide a clear, accurate, and concise answer directly addressing the user's request. Keep your response conversational and suitable for speech (1-3 sentences or short bullet points without complex markdown).
"""
            response = model.generate_content([prompt, screenshot])
            analysis = response.text.strip() if response and response.text else "Could not analyze screen content."
        else:
            # Fallback using active window text
            winfo = tool_get_active_window_info()
            wtitle = winfo.get("window_title", "Desktop")
            wproc = winfo.get("process_name", "Explorer")
            prompt = f"The user is currently looking at active window '{wtitle}' ({wproc}). User question: '{instruction}'. Answer concisely."
            response = model.generate_content(prompt)
            analysis = response.text.strip() if response and response.text else f"You are currently viewing {wtitle}."

        return {
            "success": True,
            "instruction": instruction,
            "analysis": analysis
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="interact_with_current_tab",
    description="Performs an interaction on the active browser tab: 'refresh', 'new_tab', 'close_tab', 'reopen_tab', 'next_tab', 'previous_tab', 'bookmark', 'find_in_page', 'zoom_in', 'zoom_out'.",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["refresh", "new_tab", "close_tab", "reopen_tab", "next_tab", "previous_tab", "bookmark", "find_in_page", "zoom_in", "zoom_out"],
                "description": "Tab interaction action"
            },
            "query": {"type": "string", "description": "Search query if action is 'find_in_page'"}
        },
        "required": ["action"]
    },
    tier="SAFE"
)
def tool_interact_with_current_tab(action: str, query: str = "") -> dict:
    if not pyautogui:
        return {"success": False, "error": "PyAutoGUI not available"}
    try:
        if action == "refresh":
            pyautogui.press('f5')
        elif action == "new_tab":
            pyautogui.hotkey('ctrl', 't')
        elif action == "close_tab":
            pyautogui.hotkey('ctrl', 'w')
        elif action == "reopen_tab":
            pyautogui.hotkey('ctrl', 'shift', 't')
        elif action == "next_tab":
            pyautogui.hotkey('ctrl', 'tab')
        elif action == "previous_tab":
            pyautogui.hotkey('ctrl', 'shift', 'tab')
        elif action == "bookmark":
            pyautogui.hotkey('ctrl', 'd')
            time.sleep(0.2)
            pyautogui.press('enter')
        elif action == "zoom_in":
            pyautogui.hotkey('ctrl', '=')
        elif action == "zoom_out":
            pyautogui.hotkey('ctrl', '-')
        elif action == "find_in_page":
            pyautogui.hotkey('ctrl', 'f')
            if query:
                time.sleep(0.1)
                pyautogui.write(query, interval=0.01)
                pyautogui.press('enter')
        return {"success": True, "action": action, "message": f"Executed {action} on active tab"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@register_tool(
    name="take_screenshot",
    description="Captures the PC screen and saves it into Pictures/Screenshots.",
    parameters={"type": "object", "properties": {}},
    tier="SAFE"
)
def tool_take_screenshot() -> dict:
    from engine.system_control import take_screenshot
    path = take_screenshot()
    return {"success": bool(path), "path": path}

@register_tool(
    name="empty_recycle_bin",
    description="Cleans out the Windows Recycle Bin.",
    parameters={"type": "object", "properties": {}},
    tier="DESTRUCTIVE"
)
def tool_empty_recycle_bin() -> dict:
    from engine.system_control import empty_recycle_bin
    empty_recycle_bin()
    return {"success": True, "message": "Recycle Bin emptied"}

# Return complete registry schemas
def get_all_tool_schemas():
    return [t.to_schema() for t in TOOL_REGISTRY.values()]
