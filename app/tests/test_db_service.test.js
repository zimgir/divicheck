const test = require('node:test');
const assert = require('node:assert');
const { parseDateTimestamp, compareDbDates, getFormattedDate } = require('../utils/date-utils');
const { isRecordComplete, isSnapshotComplete, computeDelta, setPortfolioDir, resetPortfolio, getLastOpenPath, getLastBrowsePath, writeLastUpdateSnapshot } = require('../services/portfolio-service');
const fs = require('fs');
const path = require('path');
const os = require('os');

process.env.DIVICHECK_META_PATH = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'divicheck-meta-')), 'analysis-meta.json');

test('parseDateTimestamp handles valid and invalid dates', () => {
  assert.strictEqual(parseDateTimestamp('2026-03-05 12:00:00'), Date.parse('2026-03-05T12:00:00'));
  assert.strictEqual(parseDateTimestamp('2026-03-05T12:00:00'), Date.parse('2026-03-05T12:00:00'));
  assert.strictEqual(parseDateTimestamp(null), 0);
  assert.strictEqual(parseDateTimestamp('invalid-date'), 0);
});

test('isRecordComplete validates required fields', () => {
  const completeRec = { date: '2026-01-01', price: 100, shares: 10, yearly_dividend: 5, yield: 5 };
  assert.strictEqual(isRecordComplete(completeRec), true);

  const incompleteRec = { date: '2026-01-01', price: 100 };
  assert.strictEqual(isRecordComplete(incompleteRec), false);

  assert.strictEqual(isRecordComplete(null), false);
  assert.strictEqual(isRecordComplete({}), false);
});

test('isSnapshotComplete requires date and symbols array', () => {
  assert.strictEqual(isSnapshotComplete({ date: '2026-01-01', symbols: ['AAPL'] }), true);
  assert.strictEqual(isSnapshotComplete({ date: '2026-01-01', symbols: [] }), true);
  assert.strictEqual(isSnapshotComplete({ date: '2026-01-01' }), false);
  assert.strictEqual(isSnapshotComplete({ symbols: ['AAPL'] }), false);
  assert.strictEqual(isSnapshotComplete(null), false);
});

test('computeDelta returns abs and pct', () => {
  assert.deepStrictEqual(computeDelta(110, 100), { abs: 10, pct: 10 });
  assert.deepStrictEqual(computeDelta(90, 100), { abs: -10, pct: -10 });
  assert.deepStrictEqual(computeDelta(100, 100), { abs: 0, pct: 0 });
});

test('computeDelta treats zero base as null pct', () => {
  assert.deepStrictEqual(computeDelta(5, 0), { abs: 5, pct: null });
  assert.deepStrictEqual(computeDelta(0, 0), { abs: 0, pct: null });
});

test('getFormattedDate returns formatted string', () => {
  const dateStr = getFormattedDate();
  assert.match(dateStr, /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
});

test('compareDbDates compares db format dates correctly', () => {
  assert.strictEqual(compareDbDates('2026-03-05 10:00:00', '2026-03-05 12:00:00') < 0, true);
  assert.strictEqual(compareDbDates('2026-03-05 12:00:00', '2026-03-05 10:00:00') > 0, true);
  assert.strictEqual(compareDbDates('2026-03-05 12:00:00', '2026-03-05 12:00:00'), 0);
});

test('analysis meta last_browse_path saves regardless of success or failure', async () => {
  await resetPortfolio();
  const metaPath = process.env.DIVICHECK_META_PATH;
  if (fs.existsSync(metaPath)) fs.unlinkSync(metaPath);
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'divicheck-test-'));
  const res = await setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, false);
  assert.strictEqual(await getLastBrowsePath(), tmpDir);
  assert.strictEqual(await getLastOpenPath(), null);

  fs.rmSync(tmpDir, { recursive: true, force: true });
});

test('analysis meta last_open_path updates and resets correctly', async () => {
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'divicheck-test-'));
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({ name: 'Test', holdings: [] }));

  const res = await setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, true);
  assert.strictEqual(await getLastOpenPath(), tmpDir);

  await resetPortfolio();
  assert.strictEqual(await getLastOpenPath(), null);

  fs.rmSync(tmpDir, { recursive: true, force: true });
});

test('setPortfolioDir validates holdings field and structure', async () => {
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'divicheck-test-'));

  // Missing holdings
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({ name: 'Test' }));
  let res = await setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, false);
  assert.match(res.error, /holdings/i);

  // Holdings not array
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({ name: 'Test', holdings: 'not-an-array' }));
  res = await setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, false);
  assert.match(res.error, /holdings/i);

  // Invalid holding structure
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({ name: 'Test', holdings: [{ s: 'AAPL' }] }));
  res = await setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, false);
  assert.match(res.error, /structure|holding/i);

  // Valid holdings
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({ name: 'Test', holdings: [{ s: 'AAPL', n: 10 }] }));
  res = await setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, true);

  fs.rmSync(tmpDir, { recursive: true, force: true });
});

test('writeLastUpdateSnapshot writes per-symbol last_update records', async () => {
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'divicheck-test-'));
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({
    name: 'Test', holdings: [{ s: 'AAPL', n: 10 }, { s: 'MSFT', n: 5 }]
  }));
  const res = await setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, true);

  const snap = await writeLastUpdateSnapshot();
  assert.strictEqual(snap.success, true);

  const meta = JSON.parse(fs.readFileSync(path.join(tmpDir, 'portfolio-meta.json'), 'utf8'));
  assert.ok(meta.records.AAPL.last_update);
  assert.strictEqual(meta.records.AAPL.last_update.shares, 10);
  assert.ok(meta.records.AAPL.last_update.date);
  assert.ok(meta.records.MSFT.last_update);
  assert.strictEqual(meta.records.MSFT.last_update.shares, 5);

  assert.ok(meta.snapshots.last_update);
  assert.ok(meta.snapshots.last_update.date);
  assert.deepStrictEqual(meta.snapshots.last_update.symbols.sort(), ['AAPL', 'MSFT']);

  fs.rmSync(tmpDir, { recursive: true, force: true });
});
