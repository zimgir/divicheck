import { showError } from '../components/modal.js';

let hasInitializedStartup = false;
let hasPortfolio = false;
let taskEventsBound = false;

function initAnalysisView() {
  const openBtn = document.getElementById('open-portfolio-btn');
  if (openBtn && !openBtn.dataset.bound) {
    openBtn.dataset.bound = 'true';
    openBtn.addEventListener('click', async () => {
      const dirPath = await window.api.selectPortfolioFolder();
      if (!dirPath) return;
      const res = await window.api.setPortfolioDir(dirPath);
      if (!res.success) {
        showError(res.error);
        await window.api.resetPortfolio();
        loadAnalysis();
      } else {
        loadAnalysis();
      }
    });
  }
  const updateBtn = document.getElementById('update-portfolio-btn');
  if (updateBtn && !updateBtn.dataset.bound) {
    updateBtn.dataset.bound = 'true';
    updateBtn.addEventListener('click', async () => {
      updateBtn.disabled = true;
      try {
        const res = await window.api.startPortfolioUpdate();
        if (!res.success) showError(res.error);
      } finally {
        syncUpdateButton();
      }
    });
  }
  if (!taskEventsBound) {
    taskEventsBound = true;
    window.api.onDbTaskUpdate(() => syncUpdateButton());
    window.api.onDbTaskFinished(() => syncUpdateButton());
  }
}

async function syncUpdateButton() {
  const btn = document.getElementById('update-portfolio-btn');
  if (!btn) return;
  const state = await window.api.getDbTaskState();
  btn.disabled = !hasPortfolio || state.running;
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAnalysisView);
} else {
  initAnalysisView();
}

async function checkStartupPortfolio() {
  if (hasInitializedStartup) return;
  hasInitializedStartup = true;
  try {
    const lastPath = await window.api.getLastOpenPath();
    if (lastPath) {
      const res = await window.api.setPortfolioDir(lastPath);
      if (!res.success) {
        showError(res.error);
        await window.api.resetPortfolio();
      }
    }
  } catch (e) {}
}

let lastStats = null;
let currentBaseline = 'last_update';

function formatDiff(delta) {
  if (!delta) return '';
  const abs = Number(delta.abs) || 0;
  const pct = delta.pct;
  let cls = 'diff-flat';
  if (abs > 0) cls = 'diff-up';
  else if (abs < 0) cls = 'diff-down';
  let text;
  if (abs === 0) {
    text = '+0.00 (0.00%)';
  } else {
    const sign = abs > 0 ? '+' : '-';
    const p = (pct === null || pct === undefined) ? '' : ` (${sign}${Math.abs(pct).toFixed(2)}%)`;
    text = `${sign}${Math.abs(abs).toFixed(2)}${p}`;
  }
  return `<div><span class="diff ${cls}">${text}</span></div>`;
}

function cellDiff(holding, baseline, metric) {
  if (holding.status && holding.status[baseline] === 'new') {
    return '<div><span class="diff diff-up">\u2014</span></div>';
  }
  const d = holding.diff && holding.diff[baseline];
  return formatDiff(d ? d[metric] : null);
}

function diffSelectorHtml() {
  const opt = (val, label) =>
    `<option value="${val}" ${currentBaseline === val ? 'selected' : ''}>${label}</option>`;
  return `
    <label for="diff-baseline" style="font-size: 13px; color: #cccccc; margin-left: auto;">Compare to:</label>
    <select id="diff-baseline" style="padding: 4px 8px; font-size: 13px; background: #3c3c3c; color: #ffffff; border: 1px solid #555555; border-radius: 3px; cursor: pointer;">
      ${opt('last_update', 'Last Update')}
      ${opt('init', 'Init')}
    </select>`;
}

function renderAnalysis(stats) {
  const sd = (stats.summary_diff && stats.summary_diff[currentBaseline]) || {};

  const dbWarningHtml = '';
  document.getElementById('analysis-summary').innerHTML = `
    ${dbWarningHtml}
    <table>
      <tr><td><strong>Portfolio Name:</strong></td><td>${stats.portfolio_name}</td></tr>
      <tr><td><strong>Number of Holdings:</strong></td><td>${stats.holdings.length}${formatDiff(sd.holdings_count)}</td></tr>
      <tr><td><strong>Total Holdings Value:</strong></td><td>${stats.total_holdings_value === 'N/A' ? 'N/A' : ('$' + stats.total_holdings_value)}${formatDiff(sd.total_holdings_value)}</td></tr>
      <tr><td><strong>Average Dividend Yield:</strong></td><td>${stats.average_dividend_yield === 'N/A' ? 'N/A' : (stats.average_dividend_yield + '%')}${formatDiff(sd.average_dividend_yield)}</td></tr>
      <tr><td><strong>Expected Total Yearly Dividend:</strong></td><td>${stats.expected_total_yearly_dividend === 'N/A' ? 'N/A' : ('$' + stats.expected_total_yearly_dividend)}${formatDiff(sd.expected_total_yearly_dividend)}</td></tr>
      <tr><td><strong>Expected Monthly Dividend:</strong></td><td>${stats.expected_monthly_dividend === 'N/A' ? 'N/A' : ('$' + stats.expected_monthly_dividend)}${formatDiff(sd.expected_monthly_dividend)}</td></tr>
      <tr><td><strong>Portfolio Path:</strong></td><td>${stats.portfolio_path}</td></tr>
    </table>
    <div style="display: flex; align-items: center; justify-content: flex-start; gap: 10px; margin-top: 15px; padding-top: 12px; border-top: 1px solid #333333;">
      <button id="open-portfolio-btn" class="tab-btn" style="padding: 6px 14px; font-size: 13px; background: #0e639c; color: white; cursor: pointer;">Open</button>
      <button id="update-portfolio-btn" class="tab-btn" style="padding: 6px 14px; font-size: 13px; background: #0e639c; color: white; cursor: pointer;">Update</button>
      ${diffSelectorHtml()}
    </div>
  `;
  initAnalysisView();
  syncUpdateButton();

  const baselineSel = document.getElementById('diff-baseline');
  if (baselineSel) {
    baselineSel.addEventListener('change', () => {
      currentBaseline = baselineSel.value;
      if (lastStats) renderAnalysis(lastStats);
    });
  }

  const theadTr = document.getElementById('analysis-header');
  if (theadTr) {
    theadTr.innerHTML = `
      <th>Symbol</th>
      <th>Company</th>
      <th>Shares</th>
      <th>Price ($)</th>
      <th>Holding Value ($)</th>
      <th>Yearly Dividend ($)</th>
      <th>Yield (%)</th>
      <th>Last Updated</th>
    `;
  }

  const tbody = document.getElementById('analysis-body');
  const noDataMsg = document.getElementById('pie-no-data-msg');

  if (window.sectorChartInstance) {
    window.sectorChartInstance.destroy();
    window.sectorChartInstance = null;
  }

  if (!stats.holdings || stats.holdings.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8">No data</td></tr>';
    if (noDataMsg) noDataMsg.style.display = 'flex';
    document.querySelectorAll('divi-table').forEach(dt => dt.updateStickyHeader());
    if (window.sectorChartInstance) {
      window.sectorChartInstance.destroy();
      window.sectorChartInstance = null;
    }
    return;
  }

  tbody.innerHTML = stats.holdings.map(h => {
    const badge = (h.status && h.status[currentBaseline] === 'new') ? ' <span class="badge-new">new</span>' : '';
    const legendKeys = [];
    const isMissing = h.in_db === false;
    if (isMissing) legendKeys.push('missing');
    if (!isMissing && h.db_filtered) legendKeys.push('filtered');
    const legendAttrs = legendKeys.length > 0 ? `data-legend-key="${legendKeys.join(' ')}"` : '';
    let symbolStyle = '';
    if (isMissing) symbolStyle = 'style="color: #ef4444;"';
    else if (h.db_filtered) symbolStyle = 'style="color: #facc15;"';
    return `
      <tr ${legendAttrs}>
        <td ${symbolStyle}>${h.symbol}${badge}</td>
        <td>${h.company}</td>
        <td>${h.shares}${cellDiff(h, currentBaseline, 'shares')}</td>
        <td>${h.price === 'N/A' ? 'N/A' : ('$' + h.price)}${cellDiff(h, currentBaseline, 'price')}</td>
        <td>${h.holding_value === 'N/A' ? 'N/A' : ('$' + h.holding_value)}${cellDiff(h, currentBaseline, 'holding_value')}</td>
        <td>${h.yearly_dividend === 'N/A' ? 'N/A' : ('$' + h.yearly_dividend)}${cellDiff(h, currentBaseline, 'yearly_dividend')}</td>
        <td>${h.yield_1y === 'N/A' ? 'N/A' : (h.yield_1y + '%')}${cellDiff(h, currentBaseline, 'yield')}</td>
        <td>${h.updated_at}</td>
      </tr>
    `;
  }).join('');

  const hasValidSectors = stats.sectors && stats.sectors.values && stats.sectors.values.length > 0 && stats.sectors.values.some(v => Number(v) > 0);
  if (!hasValidSectors) {
    if (window.sectorChartInstance) {
      window.sectorChartInstance.destroy();
      window.sectorChartInstance = null;
    }
    if (noDataMsg) noDataMsg.style.display = 'flex';
  } else {
    if (noDataMsg) noDataMsg.style.display = 'none';
    const ctx = document.getElementById('sectorPieChart').getContext('2d');
    const sectorColors = [
      '#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444',
      '#ec4899', '#8b5cf6', '#3b82f6', '#14b8a6', '#84cc16',
      '#f97316', '#6366f1'
    ];

    window.sectorChartInstance = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: stats.sectors.labels,
        datasets: [{
          data: stats.sectors.values,
          backgroundColor: sectorColors.slice(0, stats.sectors.labels.length),
          borderWidth: 1,
          borderColor: '#252526'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            align: 'start',
            labels: {
              color: '#cccccc',
              boxWidth: 12,
              padding: 10,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || '';
                const value = context.parsed || 0;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const pct = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                return ` ${label}: $${value.toFixed(2)} (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }
  document.querySelectorAll('divi-table').forEach(dt => dt.updateStickyHeader());
}

export async function loadAnalysis() {
  await checkStartupPortfolio();
  try {
    const stats = await window.api.getPortfolioStats();
    hasPortfolio = true;
    lastStats = stats;
    currentBaseline = 'last_update';
    if (window.updateDbBanner) window.updateDbBanner();
    renderAnalysis(stats);
  } catch (err) {
    hasPortfolio = false;
    lastStats = null;
    document.getElementById('analysis-summary').innerHTML = `
      <span style="color: red;">Error: ${err.message}</span>
      <div style="display: flex; align-items: center; justify-content: flex-start; gap: 10px; margin-top: 15px; padding-top: 12px; border-top: 1px solid #333333;">
        <button id="open-portfolio-btn" class="tab-btn" style="padding: 6px 14px; font-size: 13px; background: #0e639c; color: white; cursor: pointer;">Open</button>
        <button id="update-portfolio-btn" class="tab-btn" style="padding: 6px 14px; font-size: 13px; background: #0e639c; color: white; cursor: pointer;">Update</button>
      </div>
    `;
    initAnalysisView();
    syncUpdateButton();
    document.getElementById('analysis-body').innerHTML = `<tr><td colspan="8" style="color: red;">Failed to load portfolio analysis</td></tr>`;
    const noDataMsg = document.getElementById('pie-no-data-msg');
    if (noDataMsg) noDataMsg.style.display = 'flex';
    if (window.updateDbBanner) window.updateDbBanner();
  }
}
