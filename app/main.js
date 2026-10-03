const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
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
  const rootDir = path.resolve(__dirname, '..');
  const dbPath = path.join(rootDir, '.db', 'divicheck.db');
  const defaultSymbolsPath = path.join(rootDir, '.db', 'symbols_default.txt');
  const fallbackSymbols = ["AAPL", "MSFT", "JNJ", "PG", "KO", "PEP", "XOM", "CVX", "T", "VZ"];

  let file_size = 0;
  if (fs.existsSync(dbPath)) {
    file_size = fs.statSync(dbPath).size;
  }

  let symbols = fallbackSymbols;
  let source = "FALLBACK_SYMBOLS";

  if (fs.existsSync(defaultSymbolsPath)) {
    const content = fs.readFileSync(defaultSymbolsPath, 'utf8');
    symbols = content.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    source = "DEFAULT_SYMBOLS";
  }

  let total_rows = 0;
  let rows = [];

  if (fs.existsSync(dbPath)) {
    const db = new Database(dbPath, { readonly: true });
    try {
      const countRes = db.prepare("SELECT count(*) as cnt FROM stocks").get();
      total_rows = countRes ? countRes.cnt : 0;

      if (symbols.length > 0) {
        const placeholders = symbols.map(() => '?').join(',');
        const query = `SELECT * FROM stocks WHERE SYMBOL IN (${placeholders})`;
        rows = db.prepare(query).all(...symbols);
      }
    } finally {
      db.close();
    }
  }

  return {
    db_path: dbPath,
    file_size,
    total_rows,
    source,
    symbols,
    rows
  };
});
