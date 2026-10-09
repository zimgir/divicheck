const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

function getStats() {
  const rootDir = path.resolve(__dirname, '..', '..');
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

  let portfolio_symbols = [];
  const portfolioPath = path.join(rootDir, '.app', 'portfolio.json');
  if (fs.existsSync(portfolioPath)) {
    try {
      const content = fs.readFileSync(portfolioPath, 'utf8');
      const parsed = JSON.parse(content);
      if (parsed.holdings && Array.isArray(parsed.holdings)) {
        portfolio_symbols = parsed.holdings.map(h => (h.s || '').toUpperCase());
      }
    } catch (e) {}
  }

  return {
    db_path: dbPath,
    file_size,
    total_rows,
    source,
    symbols,
    rows,
    col_info,
    portfolio_symbols
  };
}

function getFormattedDate() {
  const now = new Date();
  const pad = n => String(n).padStart(2, '0');
  const year = now.getFullYear();
  const month = pad(now.getMonth() + 1);
  const day = pad(now.getDate());
  const hours = pad(now.getHours());
  const minutes = pad(now.getMinutes());
  const seconds = pad(now.getSeconds());
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

function parseDateTimestamp(dateStr) {
  if (!dateStr) return 0;
  const normalized = typeof dateStr === 'string' ? dateStr.replace(' ', 'T') : dateStr;
  const ts = Date.parse(normalized);
  return isNaN(ts) ? 0 : ts;
}

function isRecordComplete(rec) {
  if (!rec || typeof rec !== 'object') return false;
  const required = ['date', 'price', 'shares', 'yearly_dividend', 'yield'];
  for (const field of required) {
    if (rec[field] === undefined || rec[field] === null || rec[field] === '') {
      return false;
    }
  }
  return true;
}

function getPortfolioStats() {
  const rootDir = path.resolve(__dirname, '..', '..');
  const dbPath = path.join(rootDir, '.db', 'divicheck.db');
  const portfolioPath = path.join(rootDir, '.app', 'portfolio.json');
  const metaPath = path.join(rootDir, '.app', 'portfolio-meta.json');

  let holdings = [];
  if (fs.existsSync(portfolioPath)) {
    try {
      const content = fs.readFileSync(portfolioPath, 'utf8');
      const parsed = JSON.parse(content);
      holdings = parsed.holdings || [];
    } catch (e) {}
  }

  let parsedMeta = { flags: {}, records: {} };
  if (fs.existsSync(metaPath)) {
    try {
      const content = fs.readFileSync(metaPath, 'utf8');
      parsedMeta = JSON.parse(content);
    } catch (e) {}
  }

  let dividendSymbols = new Set();
  const symbolsDivPath = path.join(rootDir, '.db', 'symbols_dividend.txt');
  if (fs.existsSync(symbolsDivPath)) {
    const content = fs.readFileSync(symbolsDivPath, 'utf8');
    dividendSymbols = new Set(content.split(/\r?\n/).map(s => s.trim().toUpperCase()).filter(Boolean));
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

  parsedMeta.records = parsedMeta.records || {};
  parsedMeta.flags = parsedMeta.flags || {};
  let portfolioUpdated = false;

  for (const h of holdings) {
    const sym = (h.s || '').toUpperCase();
    const isFiltered = dividendSymbols.size > 0 ? !dividendSymbols.has(sym) : false;

    parsedMeta.flags[sym] = parsedMeta.flags[sym] || {};
    if (parsedMeta.flags[sym].db_filtered !== isFiltered) {
      parsedMeta.flags[sym].db_filtered = isFiltered;
      portfolioUpdated = true;
    }

    parsedMeta.records[sym] = parsedMeta.records[sym] || {};
    const symbolRecords = parsedMeta.records[sym];

    const stock = dbRows[sym] || {};
    const price = Number(stock.PRICE) || 0;
    const shares = Number(h.n) || 0;
    const div1y = stock.DIV_1Y !== null && stock.DIV_1Y !== undefined ? Number(stock.DIV_1Y) : (Number(stock.CUR_DIV || 0) * Number(stock.NUM_DIV_1Y || 4));
    const yield1y = stock.YIELD_1Y !== null && stock.YIELD_1Y !== undefined ? Number(stock.YIELD_1Y) : (price > 0 ? (div1y / price) * 100 : 0);
    const dateStr = stock.UPDATED_AT || getFormattedDate();

    const recordData = {
      date: dateStr,
      price: Number(price.toFixed(2)),
      shares: shares,
      yearly_dividend: Number(div1y.toFixed(2)),
      yield: Number(yield1y.toFixed(2))
    };

    if (!isRecordComplete(symbolRecords.init)) {
      symbolRecords.init = recordData;
      portfolioUpdated = true;
    }
    if (!isRecordComplete(symbolRecords.last_update)) {
      symbolRecords.last_update = recordData;
      portfolioUpdated = true;
    }

    const initTs = parseDateTimestamp(symbolRecords.init?.date);
    const updateTs = parseDateTimestamp(symbolRecords.last_update?.date);
    if (symbolRecords.init && symbolRecords.last_update && initTs > updateTs) {
      symbolRecords.init = JSON.parse(JSON.stringify(symbolRecords.last_update));
      portfolioUpdated = true;
    }
  }

  if (portfolioUpdated) {
    try {
      fs.writeFileSync(metaPath, JSON.stringify(parsedMeta, null, 4), 'utf8');
    } catch (e) {}
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
      yield_1y: yield1y ? yield1y.toFixed(2) : '0.00',
      updated_at: stock.UPDATED_AT || 'N/A',
      db_filtered: !!(parsedMeta.flags && parsedMeta.flags[symbol] && parsedMeta.flags[symbol].db_filtered)
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
}

module.exports = {
  getStats,
  getPortfolioStats
};
