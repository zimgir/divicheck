const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { getStats } = require('./services/db-service');
const { getPortfolioStats, setPortfolioDir, resetPortfolio, getLastOpenPath, getLastBrowsePath, getPortfolioSymbols } = require('./services/portfolio-service');
const updateService = require('./services/update-service');

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 640,
    minHeight: 480,
    resizable: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  updateService.stop();
});

ipcMain.handle('get-stats', async () => {
  const stats = getStats();
  stats.portfolio_symbols = await getPortfolioSymbols();
  return stats;
});

ipcMain.handle('get-portfolio-stats', async () => {
  return getPortfolioStats();
});

ipcMain.handle('select-portfolio-folder', async () => {
  const mainWindow = BrowserWindow.getFocusedWindow();
  const lastBrowse = await getLastBrowsePath();
  const dialogOpts = { properties: ['openDirectory'] };
  if (lastBrowse) {
    dialogOpts.defaultPath = lastBrowse;
  }
  const result = await dialog.showOpenDialog(mainWindow, dialogOpts);
  if (result.canceled || result.filePaths.length === 0) {
    return null;
  }
  return result.filePaths[0];
});

ipcMain.handle('set-portfolio-dir', async (event, dirPath) => {
  return setPortfolioDir(dirPath);
});

ipcMain.handle('reset-portfolio', async () => {
  return resetPortfolio();
});

ipcMain.handle('get-last-open-path', async () => {
  return getLastOpenPath();
});

ipcMain.handle('start-portfolio-update', async () => {
  return updateService.start();
});

ipcMain.handle('stop-portfolio-update', async () => {
  return updateService.stop();
});

ipcMain.handle('get-db-task-state', async () => {
  return updateService.getState();
});
