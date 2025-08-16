const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('builder', {
  signIn: (email, password, remember) => ipcRenderer.invoke('auth-sign-in', { email, password, remember }),
  signOut: () => ipcRenderer.invoke('auth-sign-out'),
  getAuth: () => ipcRenderer.invoke('auth-get'),
  setApiKey: (key, remember) => ipcRenderer.invoke('auth-set-api-key', { key, remember }),
  clearApiKey: () => ipcRenderer.invoke('auth-clear-api-key'),
  getApiKeyStatus: () => ipcRenderer.invoke('auth-get-api-key-status'),
  quickResearch: (topic) => ipcRenderer.invoke('quick-research', topic),
  runResearch: (topic) => ipcRenderer.invoke('run-research', topic),
  getPersonalRun: (taskId) => ipcRenderer.invoke('get-personal-run', taskId),
  runAgent: (goal, agent) => ipcRenderer.invoke('run-agent', goal, agent),
  expandCoverage: (topics) => ipcRenderer.invoke('expand-coverage', topics),
});


