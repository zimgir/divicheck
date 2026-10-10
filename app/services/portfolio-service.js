const path = require('path');
const fs = require('fs').promises;
const fsSync = require('fs');
const { getFormattedDate, compareDbDates } = require('../utils/date-utils');
const { getStockRows, isDbAvailable } = require('./db-service');

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

function isSnapshotComplete(snap) {
  return !!(snap && typeof snap === 'object' && snap.date && Array.isArray(snap.symbols));
}

function symbolsFromRecords(parsedMeta, key) {
  const records = (parsedMeta && parsedMeta.records) || {};
  return Object.keys(records).filter(sym => isRecordComplete(records[sym] && records[sym][key]));
}

function computeDelta(cur, base) {
  const c = Number(cur) || 0;
  const b = Number(base) || 0;
  return {
    abs: Number((c - b).toFixed(2)),
    pct: b !== 0 ? Number((((c - b) / b) * 100).toFixed(2)) : null
  };
}

function aggregateBaseline(parsedMeta, key) {
  const snap = (parsedMeta.snapshots && parsedMeta.snapshots[key]) || {};
  const symbols = Array.isArray(snap.symbols) ? snap.symbols : [];
  const records = parsedMeta.records || {};
  let count = 0, value = 0, yearly = 0;
  for (const sym of symbols) {
    const rec = records[sym] && records[sym][key];
    if (!isRecordComplete(rec)) continue;
    const shares = Number(rec.shares) || 0;
    value += shares * (Number(rec.price) || 0);
    yearly += shares * (Number(rec.yearly_dividend) || 0);
    count += 1;
  }
  return { count, value, yearly };
}

function getRootDir() {
  return path.resolve(__dirname, '..', '..');
}

function buildRecordData(stock, shares) {
  stock = stock || {};
  const price = Number(stock.PRICE) || 0;
  const div1y = stock.DIV_1Y !== null && stock.DIV_1Y !== undefined ? Number(stock.DIV_1Y) : (Number(stock.CUR_DIV || 0) * Number(stock.NUM_DIV_1Y || 4));
  const yield1y = stock.YIELD_1Y !== null && stock.YIELD_1Y !== undefined ? Number(stock.YIELD_1Y) : (price > 0 ? (div1y / price) * 100 : 0);
  const dateStr = stock.UPDATED_AT || getFormattedDate();
  return {
    date: dateStr,
    price: Number(price.toFixed(2)),
    shares: shares,
    yearly_dividend: Number(div1y.toFixed(2)),
    yield: Number(yield1y.toFixed(2))
  };
}

function getMetaPath() {
  return process.env.DIVICHECK_META_PATH || path.join(getRootDir(), '.app', 'analysis-meta.json');
}

async function getLastOpenPath() {
  const metaPath = getMetaPath();
  try {
    const data = await fs.readFile(metaPath, 'utf8');
    const meta = JSON.parse(data);
    return meta.last_open_path || null;
  } catch (e) {
    return null;
  }
}

async function getLastBrowsePath() {
  const metaPath = getMetaPath();
  try {
    const data = await fs.readFile(metaPath, 'utf8');
    const meta = JSON.parse(data);
    return meta.last_browse_path || null;
  } catch (e) {
    return null;
  }
}

async function setPortfolioDir(dirPath) {
  const metaPath = getMetaPath();
  const appDir = path.dirname(metaPath);
  if (!fsSync.existsSync(appDir)) {
    await fs.mkdir(appDir, { recursive: true });
  }
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
  const metaPath = getMetaPath();
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
    const inDbHolding = !!dbRows[sym];
    const isFiltered = inDbHolding && dividendSymbols.size > 0 ? !dividendSymbols.has(sym) : false;

    parsedMeta.flags[sym] = parsedMeta.flags[sym] || {};
    if (parsedMeta.flags[sym].db_filtered !== isFiltered) {
      parsedMeta.flags[sym].db_filtered = isFiltered;
      portfolioUpdated = true;
    }

    parsedMeta.records[sym] = parsedMeta.records[sym] || {};
    const symbolRecords = parsedMeta.records[sym];

    const stock = dbRows[sym] || {};
    const shares = Number(h.n) || 0;
    const recordData = buildRecordData(stock, shares);

    if (inDbHolding) {
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
    } else {
      if (isRecordComplete(symbolRecords.init)) {
        portfolioUpdated = false;
      }
      if (isRecordComplete(symbolRecords.last_update)) {
        portfolioUpdated = false;
      }
    }
  }

  parsedMeta.snapshots = parsedMeta.snapshots || {};
  if (!isSnapshotComplete(parsedMeta.snapshots.init)) {
    parsedMeta.snapshots.init = { date: getFormattedDate(), symbols: symbolsFromRecords(parsedMeta, 'init') };
    portfolioUpdated = true;
  }
  if (!isSnapshotComplete(parsedMeta.snapshots.last_update)) {
    parsedMeta.snapshots.last_update = { date: getFormattedDate(), symbols: symbolsFromRecords(parsedMeta, 'last_update') };
    portfolioUpdated = true;
  }
  const baselineSymbols = {
    init: new Set((parsedMeta.snapshots.init.symbols || []).map(s => String(s).toUpperCase())),
    last_update: new Set((parsedMeta.snapshots.last_update.symbols || []).map(s => String(s).toUpperCase()))
  };

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
    const inDb = !!dbRows[symbol];
    const price = inDb && stock.PRICE !== null && stock.PRICE !== undefined ? Number(stock.PRICE) : NaN;
    const div1y = inDb ? (
      stock.DIV_1Y !== null && stock.DIV_1Y !== undefined ? Number(stock.DIV_1Y) : (Number(stock.CUR_DIV || 0) * Number(stock.NUM_DIV_1Y || 4))
    ) : NaN;
    const yield1y = inDb ? (
      stock.YIELD_1Y !== null && stock.YIELD_1Y !== undefined ? Number(stock.YIELD_1Y) : (price > 0 ? (div1y / price) * 100 : 0)
    ) : NaN;

    const holdingValue = !isNaN(price) ? shares * price : NaN;
    const yearlyDividend = !isNaN(div1y) ? shares * div1y : NaN;

    if (!isNaN(holdingValue)) totalHoldingsValue += holdingValue;
    if (!isNaN(yearlyDividend)) totalYearlyDividend += yearlyDividend;

    const symKey = (symbol || '').toUpperCase();
    const diff = {};
    const status = {};
    for (const key of ['init', 'last_update']) {
      const rec = (parsedMeta.records[symKey] && parsedMeta.records[symKey][key]) || null;
      const isNew = !baselineSymbols[key].has(symKey);
      status[key] = isNew ? 'new' : 'shared';
      if (inDb && rec && !isNew) {
        const baseShares = Number(rec.shares) || 0;
        const basePrice = Number(rec.price) || 0;
        diff[key] = {
          shares: computeDelta(shares, baseShares),
          price: computeDelta(price, basePrice),
          holding_value: computeDelta(holdingValue, baseShares * basePrice),
          yearly_dividend: computeDelta(yearlyDividend, baseShares * (Number(rec.yearly_dividend) || 0)),
          yield: computeDelta(yield1y, Number(rec.yield) || 0)
        };
      } else {
        diff[key] = null;
      }
    }

    const sectorVal = inDb && stock.SECTOR && String(stock.SECTOR).trim() !== '' ? String(stock.SECTOR).trim() : 'Unknown';

    detailedHoldings.push({
      symbol,
      company: inDb && stock.COMPANY ? stock.COMPANY : symbol,
      sector: sectorVal,
      shares,
      price: !isNaN(price) ? price.toFixed(2) : 'N/A',
      holding_value: !isNaN(holdingValue) ? holdingValue.toFixed(2) : 'N/A',
      yearly_dividend: !isNaN(yearlyDividend) ? yearlyDividend.toFixed(2) : 'N/A',
      yield_1y: !isNaN(yield1y) ? yield1y.toFixed(2) : 'N/A',
      updated_at: inDb && stock.UPDATED_AT ? stock.UPDATED_AT : 'N/A',
      db_filtered: !!(parsedMeta.flags && parsedMeta.flags[symbol] && parsedMeta.flags[symbol].db_filtered),
      in_db: inDb,
      status,
      diff
    });
  }

  let sectorMap = {};
  for (const h of detailedHoldings) {
    if (!h.in_db) continue;
    const val = Number(h.holding_value) || 0;
    if (val <= 0) continue;
    const sec = h.sector || 'Unknown';
    sectorMap[sec] = (sectorMap[sec] || 0) + val;
  }
  const sectorLabels = Object.keys(sectorMap);
  const sectorValues = Object.values(sectorMap).map(v => Number(v.toFixed(2)));

  const averageDividendYield = totalHoldingsValue > 0 ? (totalYearlyDividend / totalHoldingsValue) * 100 : 0;
  const expectedMonthlyDividend = totalYearlyDividend / 12;

  const summaryDiff = {};
  for (const key of ['init', 'last_update']) {
    const base = aggregateBaseline(parsedMeta, key);
    const baseAvgYield = base.value > 0 ? (base.yearly / base.value) * 100 : 0;
    summaryDiff[key] = {
      holdings_count: computeDelta(detailedHoldings.length, base.count),
      total_holdings_value: computeDelta(totalHoldingsValue, base.value),
      average_dividend_yield: computeDelta(averageDividendYield, baseAvgYield),
      expected_total_yearly_dividend: computeDelta(totalYearlyDividend, base.yearly),
      expected_monthly_dividend: computeDelta(expectedMonthlyDividend, base.yearly / 12)
    };
  }

  const dbAvailable = isDbAvailable();
  const totalHoldingsValueNum = totalHoldingsValue;
  const totalYearlyDividendNum = totalYearlyDividend;
  return {
    portfolio_name: portfolioName,
    portfolio_path: currentPortfolioDir ? currentPortfolioDir : 'N/A',
    total_holdings_value: (totalHoldingsValueNum && totalHoldingsValueNum > 0) || totalHoldingsValueNum === 0 ? totalHoldingsValueNum.toFixed(2) : 'N/A',
    average_dividend_yield: averageDividendYield ? averageDividendYield.toFixed(2) : 'N/A',
    expected_total_yearly_dividend: (totalYearlyDividendNum && totalYearlyDividendNum > 0) || totalYearlyDividendNum === 0 ? totalYearlyDividendNum.toFixed(2) : 'N/A',
    expected_monthly_dividend: expectedMonthlyDividend ? expectedMonthlyDividend.toFixed(2) : 'N/A',
    holdings: detailedHoldings,
    summary_diff: summaryDiff,
    sectors: {
      labels: sectorLabels,
      values: sectorValues
    },
    db_available: dbAvailable
  };
}

async function writeLastUpdateSnapshot() {
  if (!currentPortfolioDir) {
    return { success: false, error: 'No portfolio open.' };
  }
  const portfolioPath = path.join(currentPortfolioDir, 'portfolio.json');
  const metaPath = path.join(currentPortfolioDir, 'portfolio-meta.json');

  let holdings = [];
  try {
    const parsed = JSON.parse(await fs.readFile(portfolioPath, 'utf8'));
    holdings = parsed.holdings || [];
  } catch (e) {
    return { success: false, error: `Failed to read portfolio: ${e.message}` };
  }

  const dbRows = {};
  if (holdings.length > 0) {
    const rows = getStockRows(holdings.map(h => h.s));
    for (const r of rows) dbRows[r.SYMBOL] = r;
  }

  let meta = { flags: {}, records: {} };
  try {
    meta = JSON.parse(await fs.readFile(metaPath, 'utf8'));
  } catch (e) {}
  meta.records = meta.records || {};
  meta.flags = meta.flags || {};
  meta.snapshots = meta.snapshots || {};

  const snapshotSymbols = [];
  for (const h of holdings) {
    const sym = (h.s || '').toUpperCase();
    const inDb = !!dbRows[sym];
    if (!inDb) continue;
    const shares = Number(h.n) || 0;
    meta.records[sym] = meta.records[sym] || {};
    meta.records[sym].last_update = buildRecordData(dbRows[sym], shares);
    snapshotSymbols.push(sym);
  }
  meta.snapshots.last_update = { date: getFormattedDate(), symbols: snapshotSymbols };

  try {
    await fs.writeFile(metaPath, JSON.stringify(meta, null, 4), 'utf8');
  } catch (e) {
    return { success: false, error: `Failed to write meta: ${e.message}` };
  }
  return { success: true };
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
  writeLastUpdateSnapshot,
  isRecordComplete,
  isSnapshotComplete,
  computeDelta
};
