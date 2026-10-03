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

  let col_info = {};
  const colInfoPath = path.join(rootDir, 'db', 'col_info.json');
  if (fs.existsSync(colInfoPath)) {
    try {
      col_info = JSON.parse(fs.readFileSync(colInfoPath, 'utf8'));
    } catch (e) {}
  }

  return {
    db_path: dbPath,
    file_size,
    total_rows,
    source,
    symbols,
    rows,
    col_info
  };
});

ipcMain.handle('get-portfolio-stats', async () => {
  const rootDir = path.resolve(__dirname, '..');
  const dbPath = path.join(rootDir, '.db', 'divicheck.db');
  const portfolioPath = path.join(rootDir, '.app', 'portfolio.json');

  let holdings = [];
  if (fs.existsSync(portfolioPath)) {
    try {
      const content = fs.readFileSync(portfolioPath, 'utf8');
      const parsed = JSON.parse(content);
      holdings = parsed.holdings || [];
    } catch (e) {}
  }

  let dbRows = {};
  if (fs.existsSync(dbPath) && holdings.length > 0) {
    const db = new Database(dbPath, { readonly: true });
    try {
      const symbols = holdings.map(h => h.s);
      const placeholders = symbols.map(() => '?').join(',');
      const query = `SELECT * FROM stocks WHERE SYMBOL IN (${placeholders})`;
      const rows = db.prepare(query).all(...symbols);
      for (const r of rows) {
        dbRows[r.SYMBOL] = r;
      }
    } finally {
      db.close();
    }
  }

  let totalHoldingsValue = 0;
  let totalYearlyDividend = 0;
  const detailedHoldings = [];

  for (const h of holdings) {
    const symbol = h.s;
    const shares = Number(h.n) || 0;
    const stock = dbRows[symbol] || {};
    const price = Number(stock.PRICE) || 0;
    const div1y = stock.DIV_1Y !== null && stock.DIV_1Y !== undefined ? Number(stock.DIV_1Y) : (Number(stock.CUR_DIV || 0) * Number(stock.NUM_DIV_1Y || 4));
    const yield1y = stock.YIELD_1Y !== null && stock.YIELD_1Y !== undefined ? Number(stock.YIELD_1Y) : (price > 0 ? (div1y / price) * 100 : 0);

    const holdingValue = shares * price;
    const yearlyDividend = shares * div1y;

    totalHoldingsValue += holdingValue;
    totalYearlyDividend += yearlyDividend;

    detailedHoldings.push({
      symbol,
      company: stock.COMPANY || symbol,
      sector: stock.SECTOR || 'Unknown',
      shares,
      price: price ? price.toFixed(2) : 'N/A',
      holding_value: holdingValue ? holdingValue.toFixed(2) : '0.00',
      yearly_dividend: yearlyDividend ? yearlyDividend.toFixed(2) : '0.00',
      yield_1y: yield1y ? yield1y.toFixed(2) : '0.00'
    });
  }

  let sectorMap = {};
  for (const h of detailedHoldings) {
    const sec = h.sector;
    const val = Number(h.holding_value) || 0;
    sectorMap[sec] = (sectorMap[sec] || 0) + val;
  }
  const sectorLabels = Object.keys(sectorMap);
  const sectorValues = Object.values(sectorMap).map(v => Number(v.toFixed(2)));

  const averageDividendYield = totalHoldingsValue > 0 ? (totalYearlyDividend / totalHoldingsValue) * 100 : 0;
  const expectedMonthlyDividend = totalYearlyDividend / 12;

  return {
    total_holdings_value: totalHoldingsValue.toFixed(2),
    average_dividend_yield: averageDividendYield.toFixed(2),
    expected_total_yearly_dividend: totalYearlyDividend.toFixed(2),
    expected_monthly_dividend: expectedMonthlyDividend.toFixed(2),
    holdings: detailedHoldings,
    sectors: {
      labels: sectorLabels,
      values: sectorValues
    }
  };
});
