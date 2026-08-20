import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Custom APIs for renderer
const api = {
  auth: {
    startOAuth: (): Promise<unknown> => ipcRenderer.invoke('auth:start-oauth'),
    getToken: (): Promise<string | null> => ipcRenderer.invoke('auth:get-token'),
    logout: (): Promise<void> => ipcRenderer.invoke('auth:logout')
  },
  notifications: {
    show: (title: string, body: string): Promise<boolean> =>
      ipcRenderer.invoke('notifications:show', title, body),
    showApproval: (approvalId: string, toolName: string, description: string): Promise<boolean> =>
      ipcRenderer.invoke('notifications:show-approval', approvalId, toolName, description)
  },
  app: {
    getVersion: (): Promise<string> => ipcRenderer.invoke('app:get-version'),
    toggleAlwaysOnTop: (): Promise<boolean> => ipcRenderer.invoke('window:toggle-always-on-top'),
    getAlwaysOnTop: (): Promise<boolean> => ipcRenderer.invoke('window:get-always-on-top'),
    setAutoLaunch: (enabled: boolean): Promise<boolean> =>
      ipcRenderer.invoke('app:set-auto-launch', enabled),
    getAutoLaunch: (): Promise<boolean> => ipcRenderer.invoke('app:get-auto-launch'),
    getBackgroundStatus: (): Promise<{ isBackgroundMode: boolean; alwaysOnTop: boolean; autoLaunch: boolean }> =>
      ipcRenderer.invoke('app:get-background-status'),
    toggleWidget: (): Promise<boolean> => ipcRenderer.invoke('widget:toggle'),
    toggleWakeWord: (enabled: boolean): Promise<boolean> => ipcRenderer.invoke('wakeword:toggle', enabled),
    analyzeScreen: (): Promise<unknown> => ipcRenderer.invoke('screen:analyze')
  }
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}
