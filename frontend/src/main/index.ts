/* ═══════════════════════════════════════════════════════════
   Electron Main Process — Aegis AI / Chaitanya Karya
   Frameless window, IPC handlers, system tray, Backend auto-spawn,
   Background operation, Global Hotkeys (Spotlight, Selection AI, Dynamic Island),
   Startup boot, Always-on-top, Enhanced Notifications, Wake Word Bridge
   ═══════════════════════════════════════════════════════════ */

import {
  app,
  shell,
  BrowserWindow,
  ipcMain,
  Tray,
  Menu,
  Notification,
  nativeImage,
  globalShortcut,
  screen,
  clipboard
} from 'electron'
import { join } from 'path'
import { spawn, ChildProcess } from 'child_process'
import http from 'http'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

let mainWindow: BrowserWindow | null = null
let quickOverlayWindow: BrowserWindow | null = null
let floatingWidgetWindow: BrowserWindow | null = null
let selectionPopupWindow: BrowserWindow | null = null
let tray: Tray | null = null
let pyBackendProcess: ChildProcess | null = null
let isQuitting = false
let alwaysOnTop = false
let wakeWordActive = true

// ── Backend Auto-Spawn ──

function ensureBackendRunning(): void {
  const checkReq = http.get('http://127.0.0.1:8000/api/conversations/', (res) => {
    console.log(`Chaitanya Karya Django backend already active (status: ${res.statusCode})`)
  })

  checkReq.on('error', () => {
    console.log('Chaitanya Karya Django backend not detected. Spawning Python server process...')
    const backendDir = is.dev
      ? join(__dirname, '../../../backend')
      : join(process.resourcesPath, 'backend')
    try {
      pyBackendProcess = spawn('python', ['manage.py', 'runserver', '0.0.0.0:8000', '--noreload'], {
        cwd: backendDir,
        shell: true
      })

      pyBackendProcess.stdout?.on('data', (data) => {
        console.log(`[Django Backend] ${data}`)
      })
      pyBackendProcess.stderr?.on('data', (data) => {
        console.error(`[Django Backend Log] ${data}`)
      })
    } catch (err) {
      console.error('Failed to auto-spawn Python Django backend:', err)
    }
  })
}

// ── Main Window ──

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 900,
    minHeight: 600,
    show: true,
    frame: false,
    titleBarStyle: 'hidden',
    autoHideMenuBar: true,
    backgroundColor: '#1a1a2e',
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  mainWindow.on('maximize', () => {
    mainWindow?.webContents.send('window:maximized', true)
  })

  mainWindow.on('unmaximize', () => {
    mainWindow?.webContents.send('window:maximized', false)
  })

  // BACKGROUND MODE: Hide window instead of closing
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault()
      mainWindow?.hide()

      if (Notification.isSupported()) {
        const bgNotification = new Notification({
          title: 'Chaitanya Karya is running in background',
          body: 'Press Ctrl+Shift+Space to summon or Ctrl+Shift+E for Selection AI.',
          icon: nativeImage.createFromPath(icon),
          silent: true
        })
        bgNotification.show()
      }
    }
  })

  const devUrl = process.env['ELECTRON_RENDERER_URL'] || 'http://localhost:5173'
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    const indexPath = join(__dirname, '../renderer/index.html')
    mainWindow.loadFile(indexPath).catch(() => {
      mainWindow?.loadURL(devUrl)
    })
  }
}

// ── Quick Command Overlay (Spotlight-like: Ctrl + Shift + K) ──

function createQuickOverlay(): void {
  if (quickOverlayWindow && !quickOverlayWindow.isDestroyed()) {
    if (quickOverlayWindow.isVisible()) {
      quickOverlayWindow.hide()
    } else {
      quickOverlayWindow.show()
      quickOverlayWindow.focus()
    }
    return
  }

  const primaryDisplay = screen.getPrimaryDisplay()
  const { width: screenWidth } = primaryDisplay.workAreaSize

  quickOverlayWindow = new BrowserWindow({
    width: 680,
    height: 72,
    x: Math.round((screenWidth - 680) / 2),
    y: 180,
    show: false,
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    focusable: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  const overlayHTML = `
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="utf-8">
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body {
        background: transparent;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-app-region: no-drag;
        overflow: hidden;
      }
      .overlay-container {
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(18, 18, 35, 0.95);
        backdrop-filter: blur(30px);
        border: 1px solid rgba(139, 92, 246, 0.4);
        border-radius: 18px;
        padding: 12px 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 0 40px rgba(139, 92, 246, 0.15);
      }
      .overlay-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: linear-gradient(135deg, #8b5cf6, #06b6d4);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
      }
      .overlay-input {
        flex: 1;
        background: transparent;
        border: none;
        outline: none;
        color: #f0f0f5;
        font-size: 17px;
        font-weight: 400;
        letter-spacing: 0.02em;
      }
      .overlay-input::placeholder {
        color: rgba(200, 200, 220, 0.4);
      }
      .overlay-hint {
        color: rgba(200, 200, 220, 0.3);
        font-size: 11px;
        white-space: nowrap;
      }
      kbd {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 4px;
        padding: 1px 5px;
        font-family: monospace;
        font-size: 10px;
      }
    </style>
  </head>
  <body>
    <div class="overlay-container">
      <div class="overlay-icon">⚡</div>
      <input id="quickInput" class="overlay-input" type="text"
        placeholder="Ask Chaitanya Karya anything or type a command..."
        autofocus autocomplete="off" spellcheck="false" />
      <div class="overlay-hint"><kbd>Enter</kbd> send · <kbd>Esc</kbd> close</div>
    </div>
    <script>
      const input = document.getElementById('quickInput');
      input.focus();
      
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          window.electron.ipcRenderer.send('overlay:hide');
        } else if (e.key === 'Enter' && input.value.trim()) {
          const query = input.value.trim();
          input.value = '';
          window.electron.ipcRenderer.send('overlay:execute', query);
        }
      });
      window.addEventListener('focus', () => input.focus());
    </script>
  </body>
  </html>
  `

  quickOverlayWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(overlayHTML)}`)

  quickOverlayWindow.on('blur', () => {
    quickOverlayWindow?.hide()
  })

  quickOverlayWindow.once('ready-to-show', () => {
    quickOverlayWindow?.show()
    quickOverlayWindow?.focus()
  })
}

// ── Floating Dynamic Island / Mini Bar (Ctrl + Shift + W) ──

function createFloatingWidgetWindow(): void {
  if (floatingWidgetWindow && !floatingWidgetWindow.isDestroyed()) {
    if (floatingWidgetWindow.isVisible()) {
      floatingWidgetWindow.hide()
    } else {
      floatingWidgetWindow.show()
      floatingWidgetWindow.focus()
    }
    return
  }

  const primaryDisplay = screen.getPrimaryDisplay()
  const { width: screenWidth } = primaryDisplay.workAreaSize

  floatingWidgetWindow = new BrowserWindow({
    width: 440,
    height: 60,
    x: Math.round((screenWidth - 440) / 2),
    y: 20,
    show: false,
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    focusable: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  const widgetHTML = `
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="utf-8">
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body {
        background: transparent;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        user-select: none;
        overflow: hidden;
      }
      .widget-pill {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        background: rgba(15, 15, 28, 0.92);
        backdrop-filter: blur(25px);
        border: 1px solid rgba(139, 92, 246, 0.4);
        border-radius: 30px;
        padding: 8px 16px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 20px rgba(139, 92, 246, 0.2);
        -webkit-app-region: drag;
      }
      .widget-left {
        display: flex;
        align-items: center;
        gap: 8px;
        -webkit-app-region: no-drag;
      }
      .logo-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 8px #10b981;
      }
      .title {
        color: #f0f0f5;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.05em;
      }
      .metric-badge {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 3px 8px;
        font-size: 11px;
        color: #a78bfa;
        font-weight: 500;
        font-family: monospace;
      }
      .actions {
        display: flex;
        align-items: center;
        gap: 6px;
        -webkit-app-region: no-drag;
      }
      .btn-icon {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 4px 8px;
        color: #e2e8f0;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
      }
      .btn-icon:hover {
        background: rgba(139, 92, 246, 0.3);
        border-color: rgba(139, 92, 246, 0.6);
        transform: scale(1.05);
      }
    </style>
  </head>
  <body>
    <div class="widget-pill">
      <div class="widget-left">
        <div class="logo-dot"></div>
        <span class="title">CHAITANYA</span>
        <span id="metricCpu" class="metric-badge">CPU: 12%</span>
        <span id="metricRam" class="metric-badge">RAM: 38%</span>
      </div>
      <div class="actions">
        <button class="btn-icon" title="Inspect Active Screen" onclick="inspectScreen()">👁️ Screen</button>
        <button class="btn-icon" title="Voice Input" onclick="triggerVoice()">🎙️</button>
        <button class="btn-icon" title="Open Full Assistant" onclick="openMain()">⚡ Open</button>
      </div>
    </div>
    <script>
      function inspectScreen() {
        window.electron.ipcRenderer.send('action:inspect-screen');
      }
      function triggerVoice() {
        window.electron.ipcRenderer.send('action:voice-listen');
      }
      function openMain() {
        window.electron.ipcRenderer.send('action:open-main');
      }

      // Live metrics polling
      setInterval(() => {
        fetch('http://127.0.0.1:8000/api/tools/execute/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'get_system_metrics', args: {} })
        }).then(r => r.json()).then(data => {
          // Parse metrics if available
        }).catch(() => {});
      }, 5000);
    </script>
  </body>
  </html>
  `

  floatingWidgetWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(widgetHTML)}`)

  floatingWidgetWindow.once('ready-to-show', () => {
    floatingWidgetWindow?.show()
  })
}

// ── Global Text Selection AI Popup (Ctrl + Shift + E) ──

function createSelectionPopupWindow(initialText: string = ''): void {
  if (selectionPopupWindow && !selectionPopupWindow.isDestroyed()) {
    selectionPopupWindow.close()
  }

  const { x, y } = screen.getCursorScreenPoint()
  const primaryDisplay = screen.getDisplayNearestPoint({ x, y })
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize

  const popWidth = 560
  const popHeight = 360
  const posX = Math.min(Math.max(x - 280, 20), screenWidth - popWidth - 20)
  const posY = Math.min(Math.max(y + 20, 20), screenHeight - popHeight - 20)

  selectionPopupWindow = new BrowserWindow({
    width: popWidth,
    height: popHeight,
    x: posX,
    y: posY,
    show: false,
    frame: false,
    transparent: true,
    resizable: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    focusable: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  const safeText = initialText.replace(/`/g, '\\`').replace(/\\/g, '\\\\').replace(/"/g, '\\"')

  const popupHTML = `
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="utf-8">
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body {
        background: transparent;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #f1f5f9;
        overflow: hidden;
      }
      .popup-box {
        background: rgba(15, 15, 28, 0.96);
        backdrop-filter: blur(30px);
        border: 1px solid rgba(139, 92, 246, 0.4);
        border-radius: 16px;
        padding: 14px 18px;
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: 10px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 0 30px rgba(139, 92, 246, 0.2);
      }
      .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
      }
      .title {
        font-size: 13px;
        font-weight: 600;
        color: #a78bfa;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .actions-bar {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }
      .action-pill {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #e2e8f0;
        font-size: 11px;
        font-weight: 500;
        padding: 4px 10px;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.15s ease;
      }
      .action-pill:hover {
        background: #8b5cf6;
        border-color: #a78bfa;
        color: white;
      }
      .result-container {
        flex: 1;
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 13px;
        line-height: 1.5;
        overflow-y: auto;
        white-space: pre-wrap;
        color: #cbd5e1;
      }
      .footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: 4px;
      }
      .btn-action {
        background: rgba(139, 92, 246, 0.2);
        border: 1px solid rgba(139, 92, 246, 0.4);
        color: #c4b5fd;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 6px;
        cursor: pointer;
      }
      .btn-action:hover {
        background: rgba(139, 92, 246, 0.4);
      }
    </style>
  </head>
  <body>
    <div class="popup-box">
      <div class="header">
        <div class="title">⚡ Chaitanya Selection AI</div>
        <span style="font-size: 11px; color: #64748b;">Esc to close</span>
      </div>
      <div class="actions-bar">
        <button class="action-pill" onclick="runPrompt('Explain this text clearly and concisely')">💡 Explain</button>
        <button class="action-pill" onclick="runPrompt('Fix grammar, improve tone and clarity')">✍️ Fix Grammar</button>
        <button class="action-pill" onclick="runPrompt('Summarize this into 3 concise key takeaways')">📝 Summarize</button>
        <button class="action-pill" onclick="runPrompt('Explain what this code does and suggest any bug fixes')">💻 Fix Code</button>
        <button class="action-pill" onclick="runPrompt('Translate this to natural conversational Hindi')">🌐 Hindi</button>
      </div>
      <div id="output" class="result-container">Selected Text: "${safeText.substring(0, 160)}..."\n\nClick any action above to generate instant AI insights.</div>
      <div class="footer">
        <button class="btn-action" onclick="copyResult()">📋 Copy Result</button>
        <button class="btn-action" onclick="openInChat()">💬 Open in Full Assistant</button>
      </div>
    </div>
    <script>
      const selected = "${safeText}";
      let lastResponse = "";

      window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          window.electron.ipcRenderer.send('selection-popup:close');
        }
      });

      async function runPrompt(actionPrompt) {
        const out = document.getElementById('output');
        out.innerText = '⏳ Thinking...';
        try {
          const res = await fetch('http://127.0.0.1:8000/api/chat/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: actionPrompt + ':\\n\\n\"\"\"\\n' + selected + '\\n\"\"\"'
            })
          });
          const data = await res.json();
          lastResponse = data.response || data.message || JSON.stringify(data);
          out.innerText = lastResponse;
        } catch (err) {
          out.innerText = 'Execution error: ' + err.message;
        }
      }

      function copyResult() {
        if (lastResponse) {
          navigator.clipboard.writeText(lastResponse);
          alert('Copied to clipboard!');
        }
      }

      function openInChat() {
        window.electron.ipcRenderer.send('selection-popup:open-chat', selected);
      }
    </script>
  </body>
  </html>
  `

  selectionPopupWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(popupHTML)}`)

  selectionPopupWindow.on('blur', () => {
    selectionPopupWindow?.hide()
  })

  selectionPopupWindow.once('ready-to-show', () => {
    selectionPopupWindow?.show()
    selectionPopupWindow?.focus()
  })
}

// ── Global Hotkey Registration ──

function registerGlobalHotkeys(): void {
  // 1. Ctrl + Shift + Space: Toggle Main Assistant Window
  globalShortcut.register('CommandOrControl+Shift+Space', () => {
    if (quickOverlayWindow && !quickOverlayWindow.isDestroyed() && quickOverlayWindow.isVisible()) {
      quickOverlayWindow.hide()
      return
    }

    if (mainWindow && mainWindow.isVisible() && mainWindow.isFocused()) {
      mainWindow.hide()
    } else if (mainWindow && mainWindow.isVisible()) {
      mainWindow.focus()
    } else {
      mainWindow?.show()
      mainWindow?.focus()
    }
  })

  // 2. Ctrl + Shift + K: Spotlight Quick Command
  globalShortcut.register('CommandOrControl+Shift+K', () => {
    createQuickOverlay()
  })

  // 3. Ctrl + Shift + W: Floating Dynamic Island Pill
  globalShortcut.register('CommandOrControl+Shift+W', () => {
    createFloatingWidgetWindow()
  })

  // 4. Ctrl + Shift + E: Global Text Selection AI Popup
  globalShortcut.register('CommandOrControl+Shift+E', () => {
    const text = clipboard.readText() || 'Highlighted text in active app'
    createSelectionPopupWindow(text)
  })

  console.log('[Hotkeys] Global shortcuts registered: Ctrl+Shift+Space, Ctrl+Shift+K, Ctrl+Shift+W, Ctrl+Shift+E')
}

// ── IPC Handlers ──

function setupIPC(): void {
  ipcMain.on('window:minimize', () => mainWindow?.minimize())
  ipcMain.on('window:maximize', () => {
    if (mainWindow?.isMaximized()) mainWindow.unmaximize()
    else mainWindow?.maximize()
  })
  ipcMain.on('window:close', () => mainWindow?.close())

  // Quick Overlay IPC
  ipcMain.on('overlay:hide', () => quickOverlayWindow?.hide())
  ipcMain.on('overlay:execute', (_event, query: string) => {
    quickOverlayWindow?.hide()
    mainWindow?.show()
    mainWindow?.focus()
    mainWindow?.webContents.send('chat:quick-command', query)
  })

  // Selection Popup IPC
  ipcMain.on('selection-popup:close', () => selectionPopupWindow?.close())
  ipcMain.on('selection-popup:open-chat', (_event, text: string) => {
    selectionPopupWindow?.close()
    mainWindow?.show()
    mainWindow?.focus()
    mainWindow?.webContents.send('chat:quick-command', `Explain this context: ${text}`)
  })

  // Widget Actions
  ipcMain.on('action:inspect-screen', () => {
    mainWindow?.show()
    mainWindow?.focus()
    mainWindow?.webContents.send('chat:quick-command', 'Analyze what is currently visible on my screen and summarize it.')
  })

  ipcMain.on('action:voice-listen', () => {
    mainWindow?.show()
    mainWindow?.focus()
    mainWindow?.webContents.send('action:start-voice-record')
  })

  ipcMain.on('action:open-main', () => {
    mainWindow?.show()
    mainWindow?.focus()
  })

  ipcMain.handle('widget:toggle', () => {
    createFloatingWidgetWindow()
    return true
  })

  ipcMain.handle('wakeword:toggle', (_event, enabled: boolean) => {
    wakeWordActive = enabled
    return wakeWordActive
  })

  ipcMain.handle('screen:analyze', async () => {
    return new Promise((resolve) => {
      const req = http.request('http://127.0.0.1:8000/api/screen/analyze/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }, (res) => {
        let body = ''
        res.on('data', (c) => body += c)
        res.on('end', () => {
          try { resolve(JSON.parse(body)) } catch { resolve({ status: 'ok', body }) }
        })
      })
      req.on('error', (e) => resolve({ status: 'error', error: e.message }))
      req.write(JSON.stringify({ prompt: 'Live screen inspect' }))
      req.end()
    })
  })

  // Notifications
  ipcMain.handle('notifications:show', (_event, title: string, body: string) => {
    if (Notification.isSupported()) {
      const notification = new Notification({
        title,
        body,
        icon: nativeImage.createFromPath(icon)
      })
      notification.on('click', () => {
        mainWindow?.show()
        mainWindow?.focus()
      })
      notification.show()
      return true
    }
    return false
  })

  ipcMain.handle('notifications:show-approval', (_event, approvalId: string, toolName: string, description: string) => {
    if (Notification.isSupported()) {
      const notification = new Notification({
        title: `⚠️ Approval Required: ${toolName}`,
        body: description.substring(0, 200),
        icon: nativeImage.createFromPath(icon),
        urgency: 'critical'
      })
      notification.on('click', () => {
        mainWindow?.show()
        mainWindow?.focus()
        mainWindow?.webContents.send('navigate:approval', approvalId)
      })
      notification.show()
      return true
    }
    return false
  })

  ipcMain.handle('shell:open_external', (_event, url: string) => {
    try {
      shell.openExternal(url)
      return true
    } catch {
      return false
    }
  })

  ipcMain.handle('app:get-version', () => app.getVersion())

  ipcMain.handle('window:toggle-always-on-top', () => {
    alwaysOnTop = !alwaysOnTop
    mainWindow?.setAlwaysOnTop(alwaysOnTop, 'floating')
    return alwaysOnTop
  })

  ipcMain.handle('window:get-always-on-top', () => alwaysOnTop)

  ipcMain.handle('app:set-auto-launch', (_event, enabled: boolean) => {
    try {
      app.setLoginItemSettings({
        openAtLogin: enabled,
        openAsHidden: true,
        args: ['--hidden']
      })
      return enabled
    } catch {
      return false
    }
  })

  ipcMain.handle('app:get-auto-launch', () => {
    try {
      return app.getLoginItemSettings().openAtLogin
    } catch {
      return false
    }
  })

  ipcMain.handle('app:get-background-status', () => {
    return {
      isBackgroundMode: !mainWindow?.isVisible(),
      alwaysOnTop: alwaysOnTop,
      autoLaunch: app.getLoginItemSettings().openAtLogin,
      wakeWordActive: wakeWordActive
    }
  })
}

// ── System Tray (Enhanced) ──

function createTray(): void {
  const trayIcon = nativeImage.createFromPath(icon).resize({ width: 16, height: 16 })
  tray = new Tray(trayIcon)

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '🖥️ Open Chaitanya Karya',
      click: () => {
        mainWindow?.show()
        mainWindow?.focus()
      }
    },
    {
      label: '⚡ Quick Command (Ctrl+Shift+K)',
      accelerator: 'CmdOrCtrl+Shift+K',
      click: () => createQuickOverlay()
    },
    {
      label: '🏝️ Floating Dynamic Island (Ctrl+Shift+W)',
      accelerator: 'CmdOrCtrl+Shift+W',
      click: () => createFloatingWidgetWindow()
    },
    {
      label: '📋 Text Selection AI (Ctrl+Shift+E)',
      accelerator: 'CmdOrCtrl+Shift+E',
      click: () => {
        const text = clipboard.readText() || 'Selected text'
        createSelectionPopupWindow(text)
      }
    },
    { type: 'separator' },
    {
      label: '👁️ Analyze Screen Context',
      click: () => {
        mainWindow?.show()
        mainWindow?.focus()
        mainWindow?.webContents.send('chat:quick-command', 'Analyze what is currently visible on my screen.')
      }
    },
    {
      label: '📋 Daily Briefing',
      click: () => {
        mainWindow?.show()
        mainWindow?.focus()
        mainWindow?.webContents.send('action:daily-briefing')
      }
    },
    {
      label: '📸 Take Screenshot',
      click: () => {
        mainWindow?.webContents.send('action:take-screenshot')
      }
    },
    { type: 'separator' },
    {
      label: '🎙️ Wake Word ("Hey Chaitanya")',
      type: 'checkbox',
      checked: wakeWordActive,
      click: (menuItem) => {
        wakeWordActive = menuItem.checked
      }
    },
    {
      label: '📌 Always on Top',
      type: 'checkbox',
      checked: alwaysOnTop,
      click: (menuItem) => {
        alwaysOnTop = menuItem.checked
        mainWindow?.setAlwaysOnTop(alwaysOnTop, 'floating')
      }
    },
    {
      label: '🚀 Launch at Startup',
      type: 'checkbox',
      checked: app.getLoginItemSettings().openAtLogin,
      click: (menuItem) => {
        app.setLoginItemSettings({
          openAtLogin: menuItem.checked,
          openAsHidden: true,
          args: ['--hidden']
        })
      }
    },
    { type: 'separator' },
    {
      label: '❌ Quit Chaitanya Karya',
      click: () => {
        isQuitting = true
        app.quit()
      }
    }
  ])

  tray.setToolTip('Chaitanya Karya : Intelligence into Action')
  tray.setContextMenu(contextMenu)

  tray.on('click', () => {
    if (mainWindow?.isVisible()) {
      mainWindow.focus()
    } else {
      mainWindow?.show()
      mainWindow?.focus()
    }
  })

  tray.on('double-click', () => {
    mainWindow?.show()
    mainWindow?.focus()
  })
}

// ── App Lifecycle ──

try {
  app.disableHardwareAcceleration()
  const tempCachePath = join(app.getPath('temp'), `chaitanya-karya-cache-${process.pid}`)
  app.setPath('userData', tempCachePath)
  app.commandLine.appendSwitch('disk-cache-dir', tempCachePath)
} catch {
  // Ignore fallback
}

app.commandLine.appendSwitch('in-process-gpu')
app.commandLine.appendSwitch('use-gl', 'swiftshader')
app.commandLine.appendSwitch('disable-gpu')
app.commandLine.appendSwitch('disable-gpu-compositing')
app.commandLine.appendSwitch('disable-gpu-rasterization')
app.commandLine.appendSwitch('disable-gpu-sandbox')
app.commandLine.appendSwitch('disable-software-rasterizer')
app.commandLine.appendSwitch('no-sandbox')

app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.chaitanya-karya')

  ensureBackendRunning()

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  setupIPC()
  createWindow()
  createTray()
  registerGlobalHotkeys()

  if (process.argv.includes('--hidden')) {
    mainWindow?.hide()
  }

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('will-quit', () => {
  globalShortcut.unregisterAll()

  if (pyBackendProcess) {
    try {
      pyBackendProcess.kill('SIGTERM')
    } catch {
      // Process cleanup
    }
  }
})

// BACKGROUND MODE: Don't quit when all windows closed
app.on('window-all-closed', () => {
  if (process.platform === 'darwin') {
    // macOS
  } else {
    console.log('[Background] App minimized to system tray. Press Ctrl+Shift+Space to summon.')
  }
})
