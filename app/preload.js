const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getStats: () => ipcRenderer.invoke('get-stats'),
  getPortfolioStats: () => ipcRenderer.invoke('get-portfolio-stats'),
  selectPortfolioFolder: () => ipcRenderer.invoke('select-portfolio-folder'),
  setPortfolioDir: (dirPath) => ipcRenderer.invoke('set-portfolio-dir', dirPath),
  resetPortfolio: () => ipcRenderer.invoke('reset-portfolio')
});
