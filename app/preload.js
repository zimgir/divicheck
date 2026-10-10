const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getStats: () => ipcRenderer.invoke('get-stats'),
  getPortfolioStats: () => ipcRenderer.invoke('get-portfolio-stats'),
  selectPortfolioFolder: () => ipcRenderer.invoke('select-portfolio-folder'),
  setPortfolioDir: (dirPath) => ipcRenderer.invoke('set-portfolio-dir', dirPath),
  resetPortfolio: () => ipcRenderer.invoke('reset-portfolio'),
  getLastOpenPath: () => ipcRenderer.invoke('get-last-open-path'),
  startPortfolioUpdate: () => ipcRenderer.invoke('start-portfolio-update'),
  stopPortfolioUpdate: () => ipcRenderer.invoke('stop-portfolio-update'),
  getDbTaskState: () => ipcRenderer.invoke('get-db-task-state'),
  onDbTaskUpdate: (callback) => ipcRenderer.on('db-task-update', (_event, data) => callback(data)),
  onDbTaskFinished: (callback) => ipcRenderer.on('db-task-finished', (_event, data) => callback(data))
});
