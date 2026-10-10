const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

function getRootDir() {
  return path.resolve(__dirname, '..', '..');
}

function getStockRows(symbols) {
  const rootDir = getRootDir();
  const dbPath = path.join(rootDir, '.db', 'divicheck.db');
  if (!isDbAvailable() || !symbols || symbols.length === 0) return [];
  try {
    const db = new Database(dbPath, { readonly: true });
    try {
      const placeholders = symbols.map(() => '?').join(',');
      const query = `SELECT * FROM stocks WHERE SYMBOL IN (${placeholders})`;
      return db.prepare(query).all(...symbols);
    } finally {
      db.close();
    }
  } catch (e) {
    return [];
  }
}

function isDbAvailable() {
  const rootDir = getRootDir();
  const dbPath = path.join(rootDir, '.db', 'divicheck.db');
  if (!fs.existsSync(dbPath)) return false;
  try {
    const st = fs.statSync(dbPath);
    if (st.size <= 0) return false;
  } catch (e) {
    return false;
  }
  return true;
}

function getStats() {
  const rootDir = getRootDir();
  const dbPath = path.join(rootDir, '.db', 'divicheck.db');
  const defaultSymbolsPath = path.join(rootDir, '.db', 'symbols_default.txt');
  const fallbackSymbols = ["AAPL", "MSFT", "JNJ", "PG", "KO", "PEP", "XOM", "CVX", "T", "VZ"];

  let file_size = 0;
  if (fs.existsSync(dbPath)) {
    try {
      file_size = fs.statSync(dbPath).size;
    } catch (e) {
      file_size = 0;
    }
  }

  let symbols = fallbackSymbols;
  let source = "FALLBACK_SYMBOLS";

  if (fs.existsSync(defaultSymbolsPath)) {
    try {
      const content = fs.readFileSync(defaultSymbolsPath, 'utf8');
      symbols = content.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
      source = "DEFAULT_SYMBOLS";
    } catch (e) {
      // keep fallback
    }
  }

  let total_rows = 0;
  let rows = [];

  if (isDbAvailable()) {
    try {
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
    } catch (e) {
      total_rows = 0;
      rows = [];
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
    col_info,
    db_available: isDbAvailable()
  };
}

module.exports = {
  getStats,
  getStockRows,
  isDbAvailable
};
