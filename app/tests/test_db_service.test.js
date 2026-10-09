const test = require('node:test');
const assert = require('node:assert');
const { parseDateTimestamp, compareDbDates, isRecordComplete, getFormattedDate, setPortfolioDir, resetPortfolio, getLastOpenPath } = require('../services/db-service');
const fs = require('fs');
const path = require('path');

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

test('getFormattedDate returns formatted string', () => {
  const dateStr = getFormattedDate();
  assert.match(dateStr, /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
});

test('compareDbDates compares db format dates correctly', () => {
  assert.strictEqual(compareDbDates('2026-03-05 10:00:00', '2026-03-05 12:00:00') < 0, true);
  assert.strictEqual(compareDbDates('2026-03-05 12:00:00', '2026-03-05 10:00:00') > 0, true);
  assert.strictEqual(compareDbDates('2026-03-05 12:00:00', '2026-03-05 12:00:00'), 0);
});

test('analysis meta last_open_path updates and resets correctly', () => {
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'divicheck-test-'));
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({ name: 'Test', holdings: [] }));

  const res = setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, true);
  assert.strictEqual(getLastOpenPath(), tmpDir);

  resetPortfolio();
  assert.strictEqual(getLastOpenPath(), null);

  fs.rmSync(tmpDir, { recursive: true, force: true });
});

test('setPortfolioDir validates holdings field and structure', () => {
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'divicheck-test-'));

  // Missing holdings
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({ name: 'Test' }));
  let res = setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, false);
  assert.match(res.error, /holdings/i);

  // Holdings not array
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({ name: 'Test', holdings: 'not-an-array' }));
  res = setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, false);
  assert.match(res.error, /holdings/i);

  // Invalid holding structure (missing s or n)
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({ name: 'Test', holdings: [{ s: 'AAPL' }] }));
  res = setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, false);
  assert.match(res.error, /structure|holding/i);

  // Valid holdings
  fs.writeFileSync(path.join(tmpDir, 'portfolio.json'), JSON.stringify({ name: 'Test', holdings: [{ s: 'AAPL', n: 10 }] }));
  res = setPortfolioDir(tmpDir);
  assert.strictEqual(res.success, true);

  fs.rmSync(tmpDir, { recursive: true, force: true });
});
