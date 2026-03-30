// Type definitions for Electron API exposed via preload script

interface ElectronAPI {
  // App info
  getVersion: () => Promise<string>;
  
  // Dialogs
  showSaveDialog: (options: any) => Promise<any>;
  showOpenDialog: (options: any) => Promise<any>;
  
  // Platform info
  platform: string;
  
  // Events
  onAppClose: (callback: () => void) => void;
  removeAllListeners: (channel: string) => void;
  
  // Window controls
  minimizeWindow: () => Promise<void>;
  maximizeWindow: () => Promise<void>;
  closeWindow: () => Promise<void>;
  
  // Backend management
  isBackendRunning: () => Promise<boolean>;
  restartBackend: () => Promise<void>;
  stopBackend: () => Promise<void>;
  
  // File operations
  readFile: (filePath: string) => Promise<string>;
  writeFile: (filePath: string, data: string) => Promise<void>;
  
  // System info
  getSystemInfo: () => Promise<any>;
  
  // Notifications
  showNotification: (title: string, body: string) => Promise<void>;
  
  // Clipboard
  copyToClipboard: (text: string) => Promise<void>;
  readFromClipboard: () => Promise<string>;
  
  // Auto-update
  checkForUpdates: () => Promise<{ success: boolean; message?: string }>;
  onUpdateStatus: (callback: (status: string, info?: any) => void) => void;
  onUpdateProgress: (callback: (progress: any) => void) => void;
}

interface AppInfo {
  version: string;
  name: string;
}

interface Env {
  NODE_ENV: string;
  ELECTRON: boolean;
  isDev: boolean;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
    appInfo?: AppInfo;
    env?: Env;
  }
}

export {};
