import { ElectronAPI } from '@electron-toolkit/preload'

interface AegisAPI {
  auth: {
    startOAuth: () => Promise<unknown>
    getToken: () => Promise<string | null>
    logout: () => Promise<void>
  }
  notifications: {
    show: (title: string, body: string) => Promise<boolean>
  }
  app: {
    getVersion: () => Promise<string>
  }
}

declare global {
  interface Window {
    electron: ElectronAPI
    api: AegisAPI
  }
}
