const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { getStats, getPortfolioStats, setPortfolioDir, resetPortfolio, getLastOpenPath, getLastBrowsePath } = require('./services/db-service');

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

ipcMain.handle('get-stats', async () => {
  return getStats();
});

ipcMain.handle('get-portfolio-stats', async () => {
  return getPortfolioStats();
});

ipcMain.handle('select-portfolio-folder', async () => {
  const mainWindow = BrowserWindow.getFocusedWindow();
  const lastBrowse = getLastBrowsePath();
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
