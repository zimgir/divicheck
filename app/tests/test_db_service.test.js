const test = require('node:test');
const assert = require('node:assert');
const { parseDateTimestamp, compareDbDates, isRecordComplete, getFormattedDate } = require('../services/db-service');

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
