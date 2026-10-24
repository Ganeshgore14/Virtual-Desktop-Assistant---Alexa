# J.A.R.V.I.S / Alexa AI Assistant: Complete Features Guide

Comprehensive documentation of all architectural components, autonomous agent capabilities, voice control tools, vision modules, and command references.

---

## 1. 🧠 Core Speech & Wake Word Architecture

- **Single Wake Word ("Alexa")**:
  - Powered by Picovoice Porcupine hotword engine.
  - Non-blocking audio pipeline using a daemon thread, enabling instant speech capture without wake-up lag.
- **Continuous Hands-Free Listening Session**:
  - Wake up the assistant **once**, and it stays awake for consecutive commands.
  - Automatically resets its silence timer on every spoken command.
  - Exits to idle sleep cleanly on explicit command (*"Go to sleep"*, *"Stop listening"*, *"Bye"*) or after 60 seconds of complete silence.
- **Natural Voice Output (TTS)**:
  - Windows SAPI5 text-to-speech with COM thread initialization for thread safety.
  - Responsive visual feedback synchronized with the animated SiriWave and glowing Eel web UI.

---

## 2. 🤖 Autonomous 7-Phase Agent Engine

When given complex, multi-step, or previously unhardcoded tasks, the assistant executes a structured agent loop powered by Google Gemini AI:

```
UNDERSTAND REQUEST ➔ PLAN ➔ SELECT TOOLS ➔ CHECK PERMISSIONS ➔ EXECUTE ➔ VERIFY ➔ RESPOND
```

1. **Understand Request**: Interprets user intent, natural phrasing, and requirements.
2. **Plan**: Formulates an ordered multi-step execution plan with real-time system context.
3. **Select Tools**: Dynamically selects registered tools from `engine/tools.py` and validates arguments against JSON schemas.
4. **Check Permissions**: Enforces a 3-tier security model (`SAFE`, `WRITE`, `DESTRUCTIVE`).
5. **Execute**: Calls native Python functions with argument validation, timeout limits, and Eel UI progress updates.
6. **Verify & Self-Correct**: Inspects return codes and outputs. If a tool fails (e.g. file not found), Gemini diagnoses the error and executes an alternative safe fix.
7. **Respond**: Synthesizes a natural, concise spoken summary of what was completed and verified.

---

## 3. 🖥️ Active Window & Screen Vision Intelligence

- **Active Foreground Window Context**:
  - Automatically identifies the currently focused application and window title (`win32gui` + `psutil`) on every turn.
- **AI Screen & Tab Vision Analysis**:
  - Captures instant snapshots of your screen and passes them to **Google Gemini Vision**.
  - Summarizes long articles or open browser tabs.
  - Explains code on screen or finds syntax/compilation errors.
  - Reads error dialogs, system alerts, or visible text.
- **Active Browser Tab URL Extraction**:
  - Extracts the active URL from Chrome, Edge, Firefox, or Brave via address bar automation (`Ctrl+L` → `Ctrl+C`).
- **Tab Interactions**:
  - Refresh (`F5`), Bookmark (`Ctrl+D`), Find in Page (`Ctrl+F`), Zoom In/Out (`Ctrl++`/`-`), and Scroll.

---

## 4. 📂 File System, Organization & Disk Management

- **File Search (`search_files`)**:
  - Recursively searches for files matching wildcard patterns (`*.py`, `*.docx`, `*.pdf`, `report*`) across user folders or custom directories.
- **Large File Discovery (`find_large_files`)**:
  - Scans directories (e.g. `Downloads`, `Documents`) and identifies the largest space-consuming files.
- **File Reading & Writing (`read_file`, `write_file`)**:
  - Reads and creates text, code, markdown, and config files with UTF-8 encoding.
- **Folder Creation (`create_folder`)**:
  - Creates folders on Desktop, Documents, or any specified path.
- **Automatic File Organization (`organize_files`)**:
  - Automatically sorts cluttered directories into categorized subfolders:
    - `Python_Code`: `.py`, `.ipynb`
    - `Documents`: `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.txt`, `.csv`
    - `Images`: `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`
    - `Archives`: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`
    - `Audio_Video`: `.mp3`, `.wav`, `.mp4`, `.mkv`
- **Safe Deletion (`delete_file`)**:
  - File deletion guarded by confirmation checks.

---

## 5. 💻 Windows PC & Application Control

- **Open Any Application (`open_app`)**:
  - Dynamically scans Windows Start Menu shortcuts (`.lnk` files across `ProgramData` and `AppData`), Windows Registry `App Paths`, and system aliases to launch any installed desktop application (Photoshop, VS Code, Word, Excel, VLC, Chrome, Edge, Spotify, Discord, etc.).
- **Graceful Application & Process Termination (`close_app`)**:
  - Closes processes via `psutil` and `taskkill` cleanly.
- **Tab & Window Closing**:
  - Close active tab (`Ctrl+W`) or close all tabs (`Ctrl+Shift+W`).
  - Close active window (`Alt+F4`).
- **Window State Manipulation (`window_action`)**:
  - Maximize (`Win+Up`), Minimize (`Win+Down`), Minimize All / Show Desktop (`Win+D`), Switch Window (`Alt+Tab`), Snap Left (`Win+Left`), Snap Right (`Win+Right`).
- **Windows Settings Shortcuts (`open_settings`)**:
  - Direct URI launching for WiFi (`ms-settings:network-wifi`), Bluetooth (`ms-settings:bluetooth`), Display, Sound, Apps, and Windows Update.
- **Power Management (`system_power`)**:
  - Lock workstation (`LockWorkStation`), Sleep, Timed Shutdown (`shutdown /s /t 10`), Restart, and Cancel Scheduled Shutdown (`shutdown /a`).

---

## 6. ⌨️ Keyboard & Mouse Automation

- **Keyboard Shortcuts (`keyboard_shortcut`)**:
  - `Ctrl+C`, `Ctrl+V`, `Ctrl+X`, `Ctrl+Z`, `Ctrl+Y`, `Ctrl+S`, `Ctrl+A`, `Ctrl+T`, `Ctrl+Shift+T`, `F5`, `F11`.
- **Dictation Typing (`type_text`)**:
  - Dictates and types dictated text into the active window at natural typing cadence.
- **Single Key Press (`press_key`)**:
  - `Enter`, `Escape`, `Tab`, `Backspace`, `Home`, `End`, `Space`.
- **Mouse Control (`mouse_click`)**:
  - Single click, double click, right click.
- **Scrolling (`scroll_screen`)**:
  - Scroll up, scroll down, jump to top (`Home`), jump to bottom (`End`).

---

## 7. 💻 Terminal Execution & Developer Tools

- **Terminal Command Runner (`execute_terminal_command`)**:
  - Runs commands in PowerShell or CMD with configurable timeout protection (default 30s).
  - Captures `stdout`, `stderr`, and `returncode`.
  - Built-in security filter blocks destructive patterns (e.g. `format`, system directory deletion, fork bombs).
- **Python Script Execution (`run_python_script`)**:
  - Runs Python scripts using the active virtual environment (`sys.executable`) and captures execution output.
- **Package Installation (`install_python_packages`)**:
  - Runs `pip install` directly into the active environment.

---

## 8. 🎵 Media, Audio & YouTube

- **YouTube Playback (`play_youtube_video`)**:
  - Searches YouTube and starts playback for requested songs, artists, or tutorials.
- **Hardware Media Controls (`media_control`)**:
  - Play/Pause toggle (`playpause` media key).
  - Next Track (`nexttrack`), Previous Track (`prevtrack`).
- **System Volume & Brightness**:
  - Set volume to exact percentage (0-100%).
  - Volume up / down in 5-10% increments.
  - System mute and unmute via NirCmd / media keys.
  - Screen brightness adjustment via `screen_brightness_control`.

---

## 9. 📧 Communication & Contacts

- **Email Dispatch (`send_email`)**:
  - Sends emails using secure Gmail SMTP (`SSL 465`) with your configured Google App Password.
  - Speech normalization converts spoken addresses (e.g. *"john at gmail dot com"*) into valid email formats.
- **WhatsApp Web Integration (`whatsApp`)**:
  - Opens WhatsApp Web or desktop URI with pre-filled encoded text.
- **Phone Calls & SMS via ADB (`makeCall`, `sendMessage`)**:
  - Android Debug Bridge integration to initiate phone calls or send SMS via connected Android devices (when ADB is enabled).

---

## 10. 👁️ Vision & Interactive Tools

- **Eye-Controlled Mouse (`eyemouse`)**:
  - Uses MediaPipe FaceMesh to track iris landmarks and control the mouse cursor.
  - Detects eye blinks to perform left-clicks.
  - **Thread-safe**: Runs in a non-blocking daemon thread.
  - **Safe Exit**: Can be closed by pressing `Q`, `Esc`, clicking the window `'X'` button, or speaking *"Close eye mouse"*.
- **Virtual Air Canvas (`virtual_canvas`)**:
  - Uses MediaPipe Hands to draw in mid-air using your index finger.
  - Includes virtual on-screen color buttons (Red, Blue, Black, Green, Clear, Close).
- **Webcam Photo Capture (`camera`)**:
  - Captures high-resolution webcam snapshots and saves them to `Pictures/Camera Roll`.
- **AI Image Generator (`image_generate`)**:
  - Generates images locally from text prompts using HuggingFace Stable Diffusion.

---

## 11. ⏱️ Productivity, Notes & Utilities

- **Time & Date Announcement**:
  - Speaks current local time or full formatted date.
- **Desktop Notes (`take_note`, `read_notes`)**:
  - Appends timestamped notes to `Documents/JARVIS_Notes.txt`.
  - Reads back the latest note and opens the file in Notepad.
- **Voice Timers (`set_timer`)**:
  - Asynchronous countdown timers for seconds or minutes with voice completion alerts.
- **Recycle Bin Cleanup (`empty_recycle_bin`)**:
  - Clears Windows Recycle Bin safely using PowerShell.
- **Network Diagnostics (`get_ip_address`, `check_internet_speed`)**:
  - Reports local network IP and runs internet speed tests (download, upload, ping).

---

## 12. 🗣️ Complete Voice Command Quick Reference

| Category | Voice Command Example | Action |
|:---|:---|:---|
| **Autonomous Agent** | *"Create a folder on my desktop called ProjectAlpha and save a report inside it."* | Multi-step agent planning and execution |
| **Autonomous Agent** | *"Find all Python files on my Desktop."* | Recursive search and file reporting |
| **Autonomous Agent** | *"Find large files in my Downloads folder taking up space."* | Disk space audit |
| **Autonomous Agent** | *"Organize the files on my Desktop into folders."* | Categorizes files into subfolders |
| **Active Tab** | *"Summarize the current tab"* | Analyzes active webpage via Gemini Vision |
| **Active Tab** | *"Explain what is on my screen"* | Inspects open window text and visual content |
| **Active Tab** | *"Close this tab"* / *"Close all tabs"* | Closes active tab (`Ctrl+W`) or all tabs (`Ctrl+Shift+W`) |
| **Active Tab** | *"Reopen closed tab"* / *"New tab"* | `Ctrl+Shift+T` / `Ctrl+T` |
| **Active Tab** | *"Bookmark this page"* / *"Refresh page"* | `Ctrl+D` / `F5` |
| **Apps** | *"Open Photoshop"*, *"Open VS Code"*, *"Open Chrome"* | Scans Start Menu and launches application |
| **Apps** | *"Close Chrome"*, *"Close Notepad"*, *"Close Spotify"* | Terminates process safely |
| **Eye Mouse** | *"Open eye mouse"* / *"Close eye mouse"* | Starts or terminates eye tracking |
| **Windows** | *"Maximize window"*, *"Minimize window"*, *"Show desktop"* | Window layout management |
| **Media** | *"Play Believer on YouTube"*, *"Pause music"*, *"Resume"* | Media playback automation |
| **Audio** | *"Set volume to 50%"*, *"Mute volume"*, *"Unmute"* | System volume control |
| **Power** | *"Lock PC"*, *"Sleep PC"*, *"Shutdown computer"*, *"Cancel shutdown"* | Windows power subsystem |
| **Productivity** | *"Take a note buy groceries"*, *"Read notes"* | Saves note to Documents |
| **Timers** | *"Set timer for 5 minutes"*, *"Set timer for 30 seconds"* | Background countdown timer |
| **Typing** | *"Type Hello world"*, *"Press Enter"*, *"Select all"*, *"Copy"* | Keyboard automation |
| **Screenshots** | *"Take a screenshot"*, *"Capture screen"* | Saves to `Pictures/Screenshots` |
| **Diagnostics** | *"CPU usage"*, *"RAM usage"*, *"System info"*, *"Battery"* | Real-time system diagnostics |
| **Recycle Bin** | *"Empty recycle bin"* | Clears Recycle Bin |
| **Sleep** | *"Go to sleep"*, *"Stop listening"*, *"Bye"* | Returns assistant to idle sleep |
