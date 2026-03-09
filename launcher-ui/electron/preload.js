const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('launcherApi', {
  version: '0.1.0',
  isDesktop: true,
  minimize: () => ipcRenderer.send('window:minimize'),
  close: () => ipcRenderer.send('window:close'),
  autoDetectGame: (gameId) => ipcRenderer.invoke('game:auto-detect', gameId)
})
