import os
import re
import time
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

# Common Windows App and Shell mappings
APP_MAP = {
    "notepad": "notepad.exe",
    "notes": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "command prompt": "cmd.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "paint": "mspaint.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "control panel": "control.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "my computer": "explorer.exe",
    "files": "explorer.exe",
    "downloads": "explorer shell:Downloads",
    "documents": "explorer shell:Personal",
    "pictures": "explorer shell:My Pictures",
    "desktop": "explorer shell:Desktop",
    "music": "explorer shell:My Music",
    "videos": "explorer shell:My Video",
    "c drive": "explorer C:\\",
    "d drive": "explorer D:\\",
    "settings": "start ms-settings:",
    "wifi": "start ms-settings:network-wifi",
    "bluetooth": "start ms-settings:bluetooth",
    "display": "start ms-settings:display",
    "sound": "start ms-settings:sound",
    "apps": "start ms-settings:appsfeatures",
    "windows update": "start ms-settings:windowsupdate",
    "chrome": "start chrome",
    "google chrome": "start chrome",
    "edge": "start msedge",
    "microsoft edge": "start msedge",
    "vscode": "code",
    "vs code": "code",
    "code": "code",
    "spotify": "start spotify:",
    "camera": "start microsoft.windows.camera:",
}

WEB_SHORTCUTS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://www.github.com",
    "whatsapp": "https://web.whatsapp.com",
    "chatgpt": "https://chat.openai.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://www.twitter.com",
    "facebook": "https://www.facebook.com",
    "netflix": "https://www.netflix.com",
    "wikipedia": "https://www.wikipedia.org",
}

PROCESS_KILL_MAP = {
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "browser": ["msedge.exe", "chrome.exe", "firefox.exe", "brave.exe"],
    "firefox": ["firefox.exe"],
    "brave": ["brave.exe"],
    "notepad": ["notepad.exe"],
    "notepad++": ["notepad++.exe"],
    "calculator": ["CalculatorApp.exe", "calc.exe"],
    "calc": ["CalculatorApp.exe", "calc.exe"],
    "spotify": ["Spotify.exe"],
    "vs code": ["Code.exe"],
    "vscode": ["Code.exe"],
    "code": ["Code.exe"],
    "paint": ["mspaint.exe"],
    "word": ["WINWORD.EXE"],
    "excel": ["EXCEL.EXE"],
    "powerpoint": ["POWERPNT.EXE"],
    "task manager": ["taskmgr.exe"],
    "discord": ["Discord.exe"],
    "telegram": ["Telegram.exe"],
    "vlc": ["vlc.exe"],
    "steam": ["steam.exe"],
    "cmd": ["cmd.exe"],
    "terminal": ["WindowsTerminal.exe", "wt.exe"],
    "powershell": ["powershell.exe"],
}

def find_start_menu_shortcut(app_name):
    """Searches Windows Start Menu for an installed application shortcut."""
    clean = app_name.strip().lower()
    start_dirs = [
        Path(os.environ.get('PROGRAMDATA', 'C:/ProgramData')) / 'Microsoft/Windows/Start Menu/Programs',
        Path(os.environ.get('APPDATA', '')) / 'Microsoft/Windows/Start Menu/Programs'
    ]
    for sdir in start_dirs:
        if not sdir.exists():
            continue
        for lnk in sdir.rglob('*.lnk'):
            stem = lnk.stem.lower()
            if clean == stem or clean in stem:
                return str(lnk)
    return None

def open_app_or_web(app_query, speak_func=None):
    """Opens local applications, shell locations, or websites cleanly."""
    query = app_query.strip().lower()

    # 1. Check known web shortcuts
    for site, url in WEB_SHORTCUTS.items():
        if query == site or query == f"open {site}":
            if speak_func:
                speak_func(f"Opening {site}")
            subprocess.Popen(f'start "" "{url}"', shell=True)
            return True

    # 2. Check local application aliases & Windows Settings
    for alias, target in APP_MAP.items():
        if query == alias or query == f"open {alias}":
            if speak_func:
                speak_func(f"Opening {alias}")
            subprocess.Popen(target, shell=True)
            return True

    # 3. Search Windows Start Menu for installed applications (e.g. Photoshop, Word, VLC)
    shortcut = find_start_menu_shortcut(query)
    if shortcut:
        if speak_func:
            speak_func(f"Opening {query}")
        try:
            os.startfile(shortcut)
            return True
        except Exception as e:
            print(f"Error launching shortcut {shortcut}: {e}")

    # 4. If ends with a domain extension, open in browser
    if re.search(r'\.(com|org|net|in|io|co|ai|edu|gov)$', query):
        url = query if query.startswith('http') else f"https://{query}"
        if speak_func:
            speak_func(f"Navigating to {query}")
        subprocess.Popen(f'start "" "{url}"', shell=True)
        return True

    # 5. Fallback: try opening with Windows start command
    try:
        if speak_func:
            speak_func(f"Opening {query}")
        subprocess.Popen(f"start {query}", shell=True)
        return True
    except Exception as e:
        print(f"open_app_or_web error: {e}")
        if speak_func:
            speak_func(f"I couldn't locate {query} on your computer.")
        return False

def close_app(query, speak_func=None):
    """
    Robustly closes opened tabs, windows, or applications.
    Handles 'close tab', 'close this tab', 'close all tabs', 'close window', 'close youtube', etc.
    """
    clean = query.lower()
    for prefix in ["close ", "exit ", "kill ", "quit "]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):].strip()

    # --- A. CLOSING BROWSER TABS ---
    tab_keywords = [
        "tab", "tabs", "current tab", "this tab", "the tab", "open tab", "open tabs",
        "opened tab", "opened tabs", "active tab", "browser tab", "youtube tab", "page", "this page"
    ]
    if clean in tab_keywords or any(clean == k for k in tab_keywords) or "tab" in clean:
        if pyautogui:
            if "all" in clean:
                # Close all tabs in the active browser window
                pyautogui.hotkey('ctrl', 'shift', 'w')
                if speak_func:
                    speak_func("Closed all tabs.")
            else:
                # Close current active tab
                pyautogui.hotkey('ctrl', 'w')
                if speak_func:
                    speak_func("Closed tab.")
            return True

    # --- B. CLOSING ACTIVE WINDOW ---
    window_keywords = ["window", "this window", "active window", "current window", "this app", "this", "application"]
    if clean in window_keywords:
        if pyautogui:
            pyautogui.hotkey('alt', 'f4')
            if speak_func:
                speak_func("Closed window.")
            return True

    # --- C. CLOSING YOUTUBE ---
    if clean == "youtube":
        # YouTube is typically a browser tab: close tab via Ctrl+W
        if pyautogui:
            pyautogui.hotkey('ctrl', 'w')
            if speak_func:
                speak_func("Closed YouTube.")
            return True

    # --- D. CLOSING EYE MOUSE ---
    if "eye mouse" in clean or clean in ["eyemouse", "mouse tracker"]:
        try:
            from engine.feature import stop_eyemouse
            stop_eyemouse()
            return True
        except Exception:
            pass

    # --- E. CLOSING SPECIFIC PROCESSES ---
    targets = PROCESS_KILL_MAP.get(clean)
    if targets:
        killed = False
        for proc in targets:
            res = subprocess.run(f"taskkill /IM {proc} /F", shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                killed = True
        if killed:
            if speak_func:
                speak_func(f"Closed {clean}.")
            return True
        else:
            if speak_func:
                speak_func(f"{clean} does not appear to be running.")
            return False

    # --- E. SEARCH RUNNING PROCESSES VIA PSUTIL ---
    if psutil:
        terminated = False
        for p in psutil.process_iter(['name', 'pid']):
            try:
                pname = p.info['name']
                if pname and (clean in pname.lower() or pname.lower().startswith(clean)):
                    p.terminate()
                    terminated = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if terminated:
            if speak_func:
                speak_func(f"Closed {clean}.")
            return True

    # --- F. FALLBACK TASKKILL ---
    try:
        result = subprocess.run(f"taskkill /IM {clean}.exe /F", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            if speak_func:
                speak_func(f"Closed {clean}.")
            return True
        else:
            # If nothing else worked, try closing active window gracefully
            if pyautogui:
                pyautogui.hotkey('alt', 'f4')
                if speak_func:
                    speak_func(f"Closed {clean}.")
                return True
    except Exception as e:
        print(f"close_app error: {e}")

    if speak_func:
        speak_func(f"Could not close {clean}.")
    return False

def window_control(action, speak_func=None):
    """Controls windows and browser tabs with full voice feedback."""
    if not pyautogui:
        return
    clean = action.lower()
    try:
        # Tab management
        if "new tab" in clean or "open tab" in clean:
            pyautogui.hotkey('ctrl', 't')
            if speak_func:
                speak_func("Opened new tab.")
        elif any(k in clean for k in ["reopen tab", "restore tab", "undo close tab"]):
            pyautogui.hotkey('ctrl', 'shift', 't')
            if speak_func:
                speak_func("Restored closed tab.")
        elif "next tab" in clean or "switch tab" in clean:
            pyautogui.hotkey('ctrl', 'tab')
        elif "previous tab" in clean or "prev tab" in clean or "last tab" in clean:
            pyautogui.hotkey('ctrl', 'shift', 'tab')
        elif any(k in clean for k in ["close tab", "close this tab", "close the tab"]):
            pyautogui.hotkey('ctrl', 'w')
            if speak_func:
                speak_func("Closed tab.")
        elif any(k in clean for k in ["reload page", "refresh page", "refresh"]):
            pyautogui.press('f5')
            if speak_func:
                speak_func("Page refreshed.")
        elif "bookmark" in clean:
            pyautogui.hotkey('ctrl', 'd')
            if speak_func:
                speak_func("Bookmarked page.")
        elif "zoom in" in clean:
            pyautogui.hotkey('ctrl', '=')
        elif "zoom out" in clean:
            pyautogui.hotkey('ctrl', '-')
        elif "reset zoom" in clean:
            pyautogui.hotkey('ctrl', '0')

        # Scrolling
        elif "scroll to top" in clean:
            pyautogui.press('home')
        elif "scroll to bottom" in clean:
            pyautogui.press('end')
        elif "scroll down" in clean:
            pyautogui.scroll(-600)
        elif "scroll up" in clean:
            pyautogui.scroll(600)

        # Window layout & state
        elif "show desktop" in clean or "minimize all" in clean:
            pyautogui.hotkey('win', 'd')
            if speak_func:
                speak_func("Showing desktop.")
        elif "switch window" in clean or "alt tab" in clean:
            pyautogui.hotkey('alt', 'tab')
        elif "maximize" in clean:
            pyautogui.hotkey('win', 'up')
            if speak_func:
                speak_func("Maximized window.")
        elif "minimize" in clean:
            pyautogui.hotkey('win', 'down')
            if speak_func:
                speak_func("Minimized window.")
        elif "snap left" in clean or "split left" in clean:
            pyautogui.hotkey('win', 'left')
        elif "snap right" in clean or "split right" in clean:
            pyautogui.hotkey('win', 'right')

    except Exception as e:
        print(f"window_control error: {e}")

def media_control(action, speak_func=None):
    """Controls media playback: play, pause, next, previous, mute."""
    if not pyautogui:
        return
    clean = action.lower()
    try:
        if any(k in clean for k in ["pause", "play", "resume"]):
            pyautogui.press('playpause')
            if speak_func:
                speak_func("Media playback toggled.")
        elif "next" in clean:
            pyautogui.press('nexttrack')
            if speak_func:
                speak_func("Playing next track.")
        elif "previous" in clean or "prev" in clean:
            pyautogui.press('prevtrack')
            if speak_func:
                speak_func("Playing previous track.")
        elif "mute" in clean:
            pyautogui.press('volumemute')
            if speak_func:
                speak_func("Volume muted.")
        elif "unmute" in clean:
            pyautogui.press('volumemute')
            if speak_func:
                speak_func("Volume unmuted.")
        elif "volume up" in clean or "increase volume" in clean:
            for _ in range(5):
                pyautogui.press('volumeup')
            if speak_func:
                speak_func("Volume increased.")
        elif "volume down" in clean or "decrease volume" in clean:
            for _ in range(5):
                pyautogui.press('volumedown')
            if speak_func:
                speak_func("Volume decreased.")
    except Exception as e:
        print(f"media_control error: {e}")

def system_power(action, speak_func=None):
    """Handles power operations: shutdown, restart, sleep, lock."""
    action = action.lower()
    try:
        if "lock" in action:
            if speak_func:
                speak_func("Locking your PC.")
            subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
        elif "shutdown" in action or "turn off" in action:
            if speak_func:
                speak_func("Shutting down the computer in ten seconds. Say cancel shutdown to abort.")
            subprocess.run("shutdown /s /t 10", shell=True)
        elif "restart" in action or "reboot" in action:
            if speak_func:
                speak_func("Restarting the computer in ten seconds. Say cancel shutdown to abort.")
            subprocess.run("shutdown /r /t 10", shell=True)
        elif "cancel shutdown" in action or "abort" in action:
            subprocess.run("shutdown /a", shell=True)
            if speak_func:
                speak_func("Scheduled shutdown has been cancelled.")
        elif "sleep" in action:
            if speak_func:
                speak_func("Putting the computer to sleep.")
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
    except Exception as e:
        print(f"system_power error: {e}")
        if speak_func:
            speak_func("Could not complete the system power operation.")

def system_stats(speak_func=None):
    """Reports CPU usage, RAM utilization, and disk status."""
    if not psutil:
        if speak_func:
            speak_func("System diagnostics library is unavailable.")
        return

    try:
        cpu_pct = psutil.cpu_percent(interval=0.4)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        ram_used_gb = ram.used / (1024**3)
        ram_total_gb = ram.total / (1024**3)
        disk_free_gb = disk.free / (1024**3)

        msg = f"CPU usage is at {cpu_pct:.0f} percent. RAM usage is {ram.percent:.0f} percent, using {ram_used_gb:.1f} of {ram_total_gb:.1f} gigabytes. Main drive has {disk_free_gb:.0f} gigabytes free."
        
        # Include battery info if available
        battery = psutil.sensors_battery()
        if battery:
            plugged = "plugged in" if battery.power_plugged else "on battery"
            msg += f" Battery is at {battery.percent:.0f} percent and {plugged}."

        if speak_func:
            speak_func(msg)
        return msg
    except Exception as e:
        print(f"system_stats error: {e}")
        if speak_func:
            speak_func("Could not retrieve system statistics.")

def tell_time_and_date(query, speak_func=None):
    """Tells current time or date in natural language."""
    now = datetime.datetime.now()
    if "time" in query:
        current_time = now.strftime("%I:%M %p")
        msg = f"The current time is {current_time}."
    else:
        current_date = now.strftime("%A, %B %d, %Y")
        msg = f"Today is {current_date}."
    
    if speak_func:
        speak_func(msg)
    return msg

def google_search(query, speak_func=None):
    """Opens a Google search for the extracted keywords."""
    clean = re.sub(r'^(search for|search|google|look up)\s+', '', query, flags=re.IGNORECASE).strip()
    clean = re.sub(r'\s+on google$', '', clean, flags=re.IGNORECASE).strip()
    if clean:
        if speak_func:
            speak_func(f"Searching Google for {clean}")
        url = f"https://www.google.com/search?q={clean.replace(' ', '+')}"
        subprocess.Popen(f'start "" "{url}"', shell=True)
    else:
        if speak_func:
            speak_func("What would you like me to search for?")

def take_screenshot(speak_func=None):
    """Captures the entire screen and saves it to Pictures/Screenshots."""
    try:
        pictures_dir = Path.home() / "Pictures" / "Screenshots"
        pictures_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = pictures_dir / f"Screenshot_{timestamp}.png"

        if pyautogui:
            img = pyautogui.screenshot()
            img.save(str(filename))
            if speak_func:
                speak_func("Screenshot captured and saved to your Pictures folder.")
            return str(filename)
    except Exception as e:
        print(f"take_screenshot error: {e}")
        if speak_func:
            speak_func("Could not capture screenshot.")

def type_text(query, speak_func=None):
    """Types dictated text into the active window."""
    if not pyautogui:
        return
    text = query.replace("type", "", 1).replace("write", "", 1).strip()
    if text:
        time.sleep(0.3)
        pyautogui.write(text, interval=0.01)
        if speak_func:
            speak_func(f"Typed: {text}")

def keyboard_shortcut(query, speak_func=None):
    """Executes common keyboard shortcuts."""
    if not pyautogui:
        return
    clean = query.lower()
    try:
        if "select all" in clean:
            pyautogui.hotkey('ctrl', 'a')
        elif "copy" in clean:
            pyautogui.hotkey('ctrl', 'c')
            if speak_func:
                speak_func("Copied.")
        elif "paste" in clean:
            pyautogui.hotkey('ctrl', 'v')
            if speak_func:
                speak_func("Pasted.")
        elif "cut" in clean:
            pyautogui.hotkey('ctrl', 'x')
            if speak_func:
                speak_func("Cut to clipboard.")
        elif "undo" in clean:
            pyautogui.hotkey('ctrl', 'z')
        elif "redo" in clean:
            pyautogui.hotkey('ctrl', 'y')
        elif "save" in clean:
            pyautogui.hotkey('ctrl', 's')
            if speak_func:
                speak_func("Saved.")
        elif "press enter" in clean:
            pyautogui.press('enter')
        elif "press escape" in clean or "press esc" in clean or clean == "escape":
            pyautogui.press('esc')
        elif "press tab" in clean:
            pyautogui.press('tab')
        elif "press backspace" in clean:
            pyautogui.press('backspace')
        elif "fullscreen" in clean or "full screen" in clean:
            pyautogui.press('f11')
    except Exception as e:
        print(f"keyboard_shortcut error: {e}")

def mouse_click(action, speak_func=None):
    """Performs mouse click actions."""
    if not pyautogui:
        return
    clean = action.lower()
    try:
        if "double click" in clean:
            pyautogui.doubleClick()
        elif "right click" in clean:
            pyautogui.rightClick()
        else:
            pyautogui.click()
    except Exception as e:
        print(f"mouse_click error: {e}")

def empty_recycle_bin(speak_func=None):
    """Empties the Windows Recycle Bin."""
    try:
        subprocess.run('powershell -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"', shell=True)
        if speak_func:
            speak_func("Recycle Bin has been emptied.")
    except Exception as e:
        print(f"empty_recycle_bin error: {e}")
        if speak_func:
            speak_func("Could not empty the Recycle Bin.")

def take_note(query, speak_func=None):
    """Saves a note to Documents/Alexa_Notes.txt with timestamp."""
    note_text = query.replace("take a note", "").replace("take note", "").replace("save note", "").strip()
    if not note_text:
        if speak_func:
            speak_func("What note would you like me to save?")
        return

    notes_dir = Path.home() / "Documents"
    notes_dir.mkdir(parents=True, exist_ok=True)
    notes_file = notes_dir / "Alexa_Notes.txt"
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    try:
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {note_text}\n")
        if speak_func:
            speak_func("Note saved to your Documents.")
    except Exception as e:
        print(f"take_note error: {e}")

def read_notes(speak_func=None):
    """Reads the latest notes from Documents/Alexa_Notes.txt (or legacy JARVIS_Notes.txt) and opens the file."""
    notes_file = Path.home() / "Documents" / "Alexa_Notes.txt"
    legacy_file = Path.home() / "Documents" / "JARVIS_Notes.txt"
    if not notes_file.exists() and legacy_file.exists():
        notes_file = legacy_file
    if not notes_file.exists():
        if speak_func:
            speak_func("You have no saved notes yet.")
        return

    try:
        lines = notes_file.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            latest = lines[-1]
            if speak_func:
                speak_func(f"Your latest note is: {latest}")
        subprocess.Popen(f'notepad.exe "{notes_file}"', shell=True)
    except Exception as e:
        print(f"read_notes error: {e}")

def set_timer(query, speak_func=None):
    """Sets a countdown timer and chimes when complete."""
    import threading
    clean = query.lower()
    match = re.search(r'(\d+)\s*(second|seconds|sec|minute|minutes|min)', clean)
    if not match:
        if speak_func:
            speak_func("Please specify a duration, such as 10 seconds or 5 minutes.")
        return

    amount = int(match.group(1))
    unit = match.group(2)
    total_seconds = amount * 60 if "min" in unit else amount

    if speak_func:
        speak_func(f"Timer set for {amount} {unit}.")

    def timer_thread():
        time.sleep(total_seconds)
        if speak_func:
            speak_func(f"Time is up! Your {amount} {unit} timer has ended.")

    t = threading.Thread(target=timer_thread, daemon=True)
    t.start()

def get_ip_address(speak_func=None):
    """Gets local IP address."""
    import socket
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if speak_func:
            speak_func(f"Your computer's local IP address is {local_ip}")
        return local_ip
    except Exception as e:
        print(f"get_ip_address error: {e}")

def create_folder(query, speak_func=None):
    """Creates a folder on the Desktop with the given name."""
    clean = re.sub(r'^(create folder|make folder|create a folder|make a folder)\s+', '', query, flags=re.IGNORECASE).strip()
    if not clean:
        clean = f"New_Folder_{int(time.time())}"
    
    desktop_dir = Path.home() / "Desktop"
    target_dir = desktop_dir / clean
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        if speak_func:
            speak_func(f"Created folder {clean} on your Desktop.")
    except Exception as e:
        print(f"create_folder error: {e}")
        if speak_func:
            speak_func(f"Could not create folder {clean}.")
