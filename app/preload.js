const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getStats: () => ipcRenderer.invoke('get-stats'),
  getPortfolioStats: () => ipcRenderer.invoke('get-portfolio-stats')
});
