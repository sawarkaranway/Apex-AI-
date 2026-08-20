# Chaitanya Karya : Intelligence into Action

A permission-aware, memory-driven AI executive assistant desktop application powered by **Electron + React + TypeScript** and a **Python Django + LangGraph** backend service.

---

# Chaitanya Karya : Intelligence into Action

A permission-aware, memory-driven autonomous AI executive assistant desktop application powered by **Electron + React + TypeScript** and a **Python Django + LangGraph** backend service.

---

## ⚡ Background Operation & Global Shortcuts

Chaitanya Karya runs seamlessly in the background behind all other applications:

| Shortcut / Trigger | Action / Purpose |
|---|---|
| **`Ctrl + Shift + Space`** | **Global Summon / Minimize** — Instantly show or hide the AI assistant over any active application (Chrome, VS Code, Slack, Word). |
| **`Ctrl + Shift + K`** | **Spotlight Quick Command** — Floating search bar for rapid one-line AI queries and PC commands. |
| **`Ctrl + Shift + W`** | **Floating Dynamic Island (Mini Pill)** — Draggable, semi-transparent top bar with live CPU/RAM metrics, Screen OCR button, and voice trigger. |
| **`Ctrl + Shift + E`** | **Global Selection AI Popup** — Highlight text in *any* desktop app and trigger instant Explain / Fix Grammar / Summarize / Code Fix / Hindi Translation. |
| **`"Hey Chaitanya"`** | **Hands-free Wake Word Detection** — Background microphone listener to summon the assistant hands-free. |
| **System Tray Mode** | Closing `(X)` minimizes to Windows System Tray so background workers, autonomous loops, and clipboard monitor remain active. |
| **Always on Top** | Pin the window over other apps in floating assistant mode. |

---

## 🛠️ Complete Feature Capabilities

### 1. Local PC Automation & Hardware Control (15 Tools)
- **App Launcher**: Safe execution of desktop applications (`open_application`)
- **System Audio & Media**: Volume control, playback toggles (`set_system_volume`, `control_media_playback`)
- **Screenshot & Vision AI**: Full screen capture & active window context OCR analysis (`take_screenshot`, `analyze_screen_context`)
- **Smart Storage Cleaner**: Automated cleanup and archival of downloads folder (`clean_downloads_folder`)
- **File System**: Read, write, create folders, search workspace, and safe deletion with approval gate (`read_file`, `write_file`, `create_folder`, `system_search`, `delete_file`)
- **Process Manager**: Real-time process listing & termination with safety confirmation (`list_processes`, `kill_process`)
- **System Health**: Real-time CPU, RAM, Disk, and Battery diagnostics (`get_system_metrics`, `get_system_info`)
- **Network Diagnostics**: Latency ping, IP address, and connection testing (`check_network_status`)
- **Security**: Instant workstation lock (`lock_workstation`)
- **Shell Execution**: Sandboxed terminal command execution with Human-in-the-Loop policy gate (`run_shell_command`)

### 2. Live Cloud & Google Workspace Integration (7 Tools)
- **Google Calendar**: Retrieve schedule & create events (`calendar_get_events`, `calendar_create_event`)
- **Gmail**: Search inbox, generate drafts, send emails with human approval (`gmail_search`, `gmail_draft`, `gmail_send`)
- **Google Drive & Docs**: Search documents & generate Google Docs (`drive_search_files`, `docs_create_doc`)
- **Multi-Provider OAuth2 Vault**: Google, Microsoft, Slack, GitHub with AES-256-GCM encrypted credential storage

### 3. Intelligence, Memory & Autonomous Proactive Systems
- **LangGraph State Machine Engine**: `Plan → Policy Check → Execute → Observe` deterministic loop
- **Multi-Tier Memory**: Working, Episodic, Semantic (Vector), and Procedural (Preferences) memory
- **Autonomous Background Workflows**: Periodic loops for Downloads Cleaner, Priority Inbox Watcher, Resource Guard, and Morning Briefings
- **Meeting Intelligence (Whisper AI)**: Live speech transcription & structured Minutes of Meeting (MoM) generator
- **Smart Clipboard Monitor**: Automatic background categorization of copied text, code, links, and emails
- **Task Scheduler**: One-time, hourly, daily, and weekly AI task execution engine
- **Live Web Search & Weather**: DuckDuckGo instant web search & real-time weather forecasts

---

## 🚀 Quick Start Guide

### 1. Start the Backend API Service (Django)
```bash
cd backend
python manage.py runserver 8000
```

### 2. Start the Desktop App Shell (Electron + React)
```bash
cd frontend
npm run dev
```

---

## 📁 Repository Structure
- `frontend/` — Electron Desktop Application (React UI, Glassmorphism Titlebar, Sidebar, Approval Modal, Quick Overlay, Dynamic Island, Selection AI Popup)
- `backend/` — Django REST API + LangGraph Agent Runtime (Policy Engine, 39 Tool Registry, RAG, Memory, Workflow Loops, Scheduler, Wake Word Engine)
- `Chaitanya_Karya_E2E_Testing_Report.docx` — Complete End-to-End verification report.


