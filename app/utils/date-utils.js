function getFormattedDate() {
  const now = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}

function parseDateTimestamp(dateStr) {
  if (!dateStr) return 0;
  const normalized = typeof dateStr === 'string' ? dateStr.replace(' ', 'T') : dateStr;
  const ts = Date.parse(normalized);
  return isNaN(ts) ? 0 : ts;
}

function compareDbDates(dateStr1, dateStr2) {
  return parseDateTimestamp(dateStr1) - parseDateTimestamp(dateStr2);
}

module.exports = {
  getFormattedDate,
  parseDateTimestamp,
  compareDbDates
};
