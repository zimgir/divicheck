export async function loadData() {
  try {
    const stats = await window.api.getStats();

    document.getElementById('stats-summary').innerHTML = `
      <table>
        <tr><td><strong>Database:</strong></td><td>${stats.db_path}</td></tr>
        <tr><td><strong>Size:</strong></td><td>${stats.file_size} bytes</td></tr>
        <tr><td><strong>Total Rows:</strong></td><td>${stats.total_rows}</td></tr>
        <tr><td><strong>Symbols Source:</strong></td><td>${stats.source} (${stats.rows.length} matching)</td></tr>
      </table>
    `;

    const theadTr = document.getElementById('search-header');
    const tbody = document.getElementById('search-body');

    if (stats.rows.length === 0) {
      theadTr.innerHTML = '<th>Symbol</th>';
      tbody.innerHTML = '<tr><td colspan="1">No matching rows found.</td></tr>';
      return;
    }

    const columns = Object.keys(stats.rows[0]);
    const colInfo = stats.col_info || {};
    const portfolioSymbols = new Set((stats.portfolio_symbols || []).map(s => s.toUpperCase()));

    theadTr.innerHTML = columns.map(col => {
      const desc = colInfo[col] || col;
      return `<th title="${desc}">${col}</th>`;
    }).join('');

    tbody.innerHTML = stats.rows.map(r => {
      const sym = (r.SYMBOL !== undefined ? r.SYMBOL : r[columns[0]]) || '';
      const isInPortfolio = portfolioSymbols.has(String(sym).toUpperCase());
      return `
        <tr ${isInPortfolio ? 'style="color: #10b981;"' : ''}>
          ${columns.map(col => {
            const desc = colInfo[col] || '';
            return `<td title="${desc}">${r[col] !== null && r[col] !== undefined ? r[col] : ''}</td>`;
          }).join('')}
        </tr>
      `;
    }).join('');
    document.querySelectorAll('divi-table').forEach(dt => dt.updateStickyHeader());
  } catch (err) {
    document.getElementById('stats-summary').innerHTML = `<span style="color: red;">Error: ${err.message}</span>`;
    document.getElementById('search-body').innerHTML = `<tr><td colspan="1" style="color: red;">Failed to data</td></tr>`;
  }
}
