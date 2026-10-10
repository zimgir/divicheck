const path = require('path');
const fs = require('fs').promises;
const fsSync = require('fs');
const { getFormattedDate, compareDbDates } = require('../utils/date-utils');
const { getStockRows } = require('./db-service');

let currentPortfolioDir = null;

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

function getRootDir() {
  return path.resolve(__dirname, '..', '..');
}

async function getLastOpenPath() {
  const metaPath = path.join(getRootDir(), '.app', 'analysis-meta.json');
  try {
    const data = await fs.readFile(metaPath, 'utf8');
    const meta = JSON.parse(data);
    return meta.last_open_path || null;
  } catch (e) {
    return null;
  }
}

async function getLastBrowsePath() {
  const metaPath = path.join(getRootDir(), '.app', 'analysis-meta.json');
  try {
    const data = await fs.readFile(metaPath, 'utf8');
    const meta = JSON.parse(data);
    return meta.last_browse_path || null;
  } catch (e) {
    return null;
  }
}

async function setPortfolioDir(dirPath) {
  const rootDir = getRootDir();
  const appDir = path.join(rootDir, '.app');
  if (!fsSync.existsSync(appDir)) {
    await fs.mkdir(appDir, { recursive: true });
  }
  const metaPath = path.join(appDir, 'analysis-meta.json');
  let meta = {};
  try {
    const data = await fs.readFile(metaPath, 'utf8');
    meta = JSON.parse(data);
  } catch (e) {}

  meta.last_browse_path = dirPath;
  try {
    await fs.writeFile(metaPath, JSON.stringify(meta, null, 4), 'utf8');
  } catch (e) {}

  const portfolioPath = path.join(dirPath, 'portfolio.json');
  if (!fsSync.existsSync(portfolioPath)) {
    return { success: false, error: `portfolio.json not found at path: ${portfolioPath}` };
  }
  try {
    const content = await fs.readFile(portfolioPath, 'utf8');
    const parsed = JSON.parse(content);
    if (!parsed.holdings || !Array.isArray(parsed.holdings)) {
      return { success: false, error: `Invalid portfolio.json: Expected 'holdings' field as an array.` };
    }
    for (let i = 0; i < parsed.holdings.length; i++) {
      const h = parsed.holdings[i];
      if (!h || typeof h !== 'object' || typeof h.s !== 'string' || h.s.trim() === '' || h.n === undefined || h.n === null) {
        return { success: false, error: `Invalid portfolio.json: Holding at index ${i} has invalid structure (expected symbol 's' and shares 'n').` };
      }
    }
  } catch (err) {
    if (err.success === false || (err.message && err.message.startsWith('Invalid portfolio.json'))) {
      return err.success === false ? err : { success: false, error: err.message };
    }
    return { success: false, error: `Failed to parse JSON in ${portfolioPath}: ${err.message}` };
  }

  currentPortfolioDir = dirPath;
  meta.last_open_path = dirPath;
  try {
    await fs.writeFile(metaPath, JSON.stringify(meta, null, 4), 'utf8');
  } catch (e) {}

  return { success: true };
}

async function resetPortfolio() {
  currentPortfolioDir = null;
  const metaPath = path.join(getRootDir(), '.app', 'analysis-meta.json');
  try {
    const data = await fs.readFile(metaPath, 'utf8');
    const meta = JSON.parse(data);
    delete meta.last_open_path;
    await fs.writeFile(metaPath, JSON.stringify(meta, null, 4), 'utf8');
  } catch (e) {}
  return { success: true };
}

async function getPortfolioStats() {
  const rootDir = getRootDir();
  let holdings = [];
  let portfolioName = 'N/A';
  let portfolioPath = '';
  let metaPath = '';

  if (currentPortfolioDir) {
    portfolioPath = path.join(currentPortfolioDir, 'portfolio.json');
    metaPath = path.join(currentPortfolioDir, 'portfolio-meta.json');
    if (fsSync.existsSync(portfolioPath)) {
      try {
        const content = await fs.readFile(portfolioPath, 'utf8');
        const parsed = JSON.parse(content);
        holdings = parsed.holdings || [];
        portfolioName = parsed.name || 'N/A';
      } catch (e) {}
    }
  }

  let parsedMeta = { flags: {}, records: {} };
  if (metaPath && fsSync.existsSync(metaPath)) {
    try {
      const content = await fs.readFile(metaPath, 'utf8');
      parsedMeta = JSON.parse(content);
    } catch (e) {}
  }

  let dividendSymbols = new Set();
  const symbolsDivPath = path.join(rootDir, '.db', 'symbols_dividend.txt');
  if (fsSync.existsSync(symbolsDivPath)) {
    const content = fsSync.readFileSync(symbolsDivPath, 'utf8');
    dividendSymbols = new Set(content.split(/\r?\n/).map(s => s.trim().toUpperCase()).filter(Boolean));
  }

  let dbRows = {};
  if (holdings.length > 0) {
    const symbols = holdings.map(h => h.s);
    const rows = getStockRows(symbols);
    for (const r of rows) {
      dbRows[r.SYMBOL] = r;
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

    if (symbolRecords.init && symbolRecords.last_update && compareDbDates(symbolRecords.init.date, symbolRecords.last_update.date) > 0) {
      symbolRecords.init = JSON.parse(JSON.stringify(symbolRecords.last_update));
      portfolioUpdated = true;
    }
  }

  if (portfolioUpdated && metaPath) {
    try {
      await fs.writeFile(metaPath, JSON.stringify(parsedMeta, null, 4), 'utf8');
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
    portfolio_name: portfolioName,
    portfolio_path: currentPortfolioDir ? currentPortfolioDir : 'N/A',
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

async function getPortfolioSymbols() {
  if (!currentPortfolioDir) return [];
  const portfolioPath = path.join(currentPortfolioDir, 'portfolio.json');
  try {
    const content = await fs.readFile(portfolioPath, 'utf8');
    const parsed = JSON.parse(content);
    if (parsed.holdings && Array.isArray(parsed.holdings)) {
      return parsed.holdings.map(h => (h.s || '').toUpperCase());
    }
  } catch (e) {}
  return [];
}

module.exports = {
  getLastOpenPath,
  getLastBrowsePath,
  setPortfolioDir,
  resetPortfolio,
  getPortfolioStats,
  getPortfolioSymbols,
  isRecordComplete
};
