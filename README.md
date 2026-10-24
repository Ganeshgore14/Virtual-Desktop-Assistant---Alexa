# Alexa Autonomous AI Voice Assistant & PC Control Agent

An intelligent desktop voice assistant and general-purpose Windows PC Control Agent, powered by Google Gemini AI, SpeechRecognition, PyAudio, Eel, and a dynamic Tool-Calling Engine.

---

## 🌟 Key Capabilities

1. **Continuous Listening & Fast Wake-up**:
   - Wake up the assistant **once** ("Alexa"), and it stays active for continuous multi-command workflows.
   - Non-blocking audio architecture for instantaneous speech recognition.

2. **Autonomous Agent Loop**:
   - Operates on a 7-phase execution loop:
     `UNDERSTAND REQUEST → PLAN → SELECT TOOLS → CHECK PERMISSIONS → EXECUTE → VERIFY → RESPOND`
   - Executes multi-step complex tasks dynamically without requiring hardcoded scripts.
   - Self-diagnoses errors, executes safe retries, and verifies task completion.

3. **Full Windows PC Control via Dynamic Tools**:
   - **Active Window & Tab Intelligence**: Inspects the currently focused window title and process in real time. Can capture the active screen or browser tab and pass it to Gemini Vision to summarize the current webpage, explain code on screen, read error messages, or inspect what the user is viewing.
   - **Browser Automation**: Extract active tab URL, search Google, close tabs (`Ctrl+W`), close all tabs (`Ctrl+Shift+W`), reopen closed tabs (`Ctrl+Shift+T`), switch tabs, zoom, search within page (`Ctrl+F`), and scroll.
   - **Application Control**: Opens any installed desktop app by scanning Windows Start Menu shortcuts and App Paths. Gracefully closes applications, tabs, and windows.
   - **File System & Organization**: Search files by pattern (`*.py`, `*.pdf`, `*.docx`), find large files consuming disk space, create folders, read/write files, and organize directories into categories.
   - **Terminal & Code Execution**: Runs PowerShell/CMD commands with timeout protection and permission safeguards; runs Python scripts and installs project dependencies.
   - **System Diagnostics**: Real-time CPU, RAM, Disk, Battery, and Network status reporting.
   - **Productivity**: Automated reports, notes, timers, dictation typing, and keyboard/mouse automation.

---

## 🛠️ Setup Instructions

### 1. Activate Environment
```cmd
envjarvis\Scripts\activate
```

### 2. Configuration (.env)
Create or verify your `.env` file in the project root:
```env
ASSISTANT_NAME=Alexa
GENAI_API_KEY=your_gemini_api_key
HF_TOKEN=your_huggingface_token
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_gmail_app_password
PORCUPINE_ACCESS_KEY=
```

### 3. Run the Assistant
```cmd
python run.py
```

---

## 💻 Voice Command Examples

### 🧠 Autonomous Multi-Step & Complex Agent Commands
- *"Create a folder on my desktop called ProjectAlpha and save a report inside it."*
- *"Find all my Python files on my Desktop and show me what is there."*
- *"Find the large files in my Downloads folder taking up space."*
- *"Organize the files on my Desktop into categorized folders."*
- *"Open VS Code and run my project."*
- *"Open Chrome, search for latest AI news, and summarize the topic."*
- *"Install the requests and pandas packages for this project."*

### ⚡ Quick PC Control Shortcuts
| Category | Spoken Command Example | Action |
|:---|:---|:---|
| **Tabs & Windows** | *"Close tab"*, *"Close this tab"*, *"Close all tabs"*, *"Close window"*, *"New tab"* | Native tab and window automation |
| **App Launching** | *"Open Photoshop"*, *"Open VS Code"*, *"Open Chrome"*, *"Open Settings"*, *"Open Task Manager"* | Scans Start Menu & launches any installed app |
| **App Closing** | *"Close Chrome"*, *"Close Edge"*, *"Close Notepad"*, *"Close Spotify"* | Graceful process termination |
| **System Power** | *"Lock PC"*, *"Sleep PC"*, *"Shutdown Computer"*, *"Restart PC"*, *"Cancel Shutdown"* | Workstation locking and power management |
| **Screenshots** | *"Take a screenshot"*, *"Capture screen"* | Saves screenshot to `Pictures/Screenshots` |
| **Diagnostics** | *"CPU usage"*, *"RAM usage"*, *"System info"*, *"Disk space"*, *"Battery status"* | Real-time diagnostic statistics |
| **Media & Audio** | *"Play Believer on YouTube"*, *"Pause music"*, *"Resume"*, *"Volume to 50%"*, *"Mute"* | Full playback and volume control |
| **Files & Folders** | *"Open C Drive"*, *"Open D Drive"*, *"Open Downloads"*, *"Open Documents"* | Opens Windows File Explorer paths |
| **Typing & Mouse** | *"Type Hello world"*, *"Select all"*, *"Copy"*, *"Paste"*, *"Double click"* | Hands-free dictation and shortcuts |
| **Settings** | *"Open WiFi settings"*, *"Bluetooth settings"*, *"Display settings"*, *"Sound settings"* | Launches Windows Settings categories |

---

## 🧪 Testing

Run the automated test suite covering unit tests, system control, tab closing, tool registry schemas, and agent planning:
```cmd
python test_suite.py
```