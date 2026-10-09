function showPopup(msg, title = 'Error') {
  const titleEl = document.getElementById('popup-title');
  if (titleEl) titleEl.textContent = title;
  document.getElementById('popup-message').textContent = msg;
  document.getElementById('popup-modal').style.display = 'flex';
}

function initAnalysisView() {
  const okBtn = document.getElementById('popup-ok-btn');
  if (okBtn && !okBtn.dataset.bound) {
    okBtn.dataset.bound = 'true';
    okBtn.addEventListener('click', () => {
      document.getElementById('popup-modal').style.display = 'none';
    });
  }
  const openBtn = document.getElementById('open-portfolio-btn');
  if (openBtn && !openBtn.dataset.bound) {
    openBtn.dataset.bound = 'true';
    openBtn.addEventListener('click', async () => {
      const dirPath = await window.api.selectPortfolioFolder();
      if (!dirPath) return;
      const res = await window.api.setPortfolioDir(dirPath);
      if (!res.success) {
        showPopup(res.error);
        await window.api.resetPortfolio();
        loadAnalysis();
      } else {
        loadAnalysis();
      }
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAnalysisView);
} else {
  initAnalysisView();
}

let hasInitializedStartup = false;

async function checkStartupPortfolio() {
  if (hasInitializedStartup) return;
  hasInitializedStartup = true;
  try {
    const lastPath = await window.api.getLastOpenPath();
    if (lastPath) {
      const res = await window.api.setPortfolioDir(lastPath);
      if (!res.success) {
        showPopup(res.error);
        await window.api.resetPortfolio();
      }
    }
  } catch (e) {}
}

export async function loadAnalysis() {
  await checkStartupPortfolio();
  try {
    const stats = await window.api.getPortfolioStats();

    document.getElementById('analysis-summary').innerHTML = `
      <table>
        <tr><td><strong>Portfolio Name:</strong></td><td>${stats.portfolio_name}</td></tr>
        <tr><td><strong>Number of Holdings:</strong></td><td>${stats.holdings.length}</td></tr>
        <tr><td><strong>Total Holdings Value:</strong></td><td>$${stats.total_holdings_value}</td></tr>
        <tr><td><strong>Average Dividend Yield:</strong></td><td>${stats.average_dividend_yield}%</td></tr>
        <tr><td><strong>Expected Total Yearly Dividend:</strong></td><td>$${stats.expected_total_yearly_dividend}</td></tr>
        <tr><td><strong>Expected Monthly Dividend:</strong></td><td>$${stats.expected_monthly_dividend}</td></tr>
        <tr><td><strong>Portfolio Path:</strong></td><td>${stats.portfolio_path}</td></tr>
      </table>
      <div style="display: flex; align-items: center; justify-content: flex-start; margin-top: 15px; padding-top: 12px; border-top: 1px solid #333333;">
        <button id="open-portfolio-btn" class="tab-btn" style="padding: 6px 14px; font-size: 13px; background: #0e639c; color: white; cursor: pointer;">Open</button>
      </div>
    `;
    initAnalysisView();

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
      return;
    }

    if (noDataMsg) noDataMsg.style.display = 'none';

    tbody.innerHTML = stats.holdings.map(h => `
      <tr ${h.db_filtered ? 'data-legend-index="0"' : ''}>
        <td ${h.db_filtered ? 'style="color: #facc15;"' : ''}>${h.symbol}</td>
        <td>${h.company}</td>
        <td>${h.shares}</td>
        <td>$${h.price}</td>
        <td>$${h.holding_value}</td>
        <td>$${h.yearly_dividend}</td>
        <td>${h.yield_1y}%</td>
        <td>${h.updated_at}</td>
      </tr>
    `).join('');

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
    document.querySelectorAll('divi-table').forEach(dt => dt.updateStickyHeader());
  } catch (err) {
    document.getElementById('analysis-summary').innerHTML = `
      <span style="color: red;">Error: ${err.message}</span>
      <div style="display: flex; align-items: center; justify-content: flex-start; margin-top: 15px; padding-top: 12px; border-top: 1px solid #333333;">
        <button id="open-portfolio-btn" class="tab-btn" style="padding: 6px 14px; font-size: 13px; background: #0e639c; color: white; cursor: pointer;">Open</button>
      </div>
    `;
    initAnalysisView();
    document.getElementById('analysis-body').innerHTML = `<tr><td colspan="8" style="color: red;">Failed to load portfolio analysis</td></tr>`;
    const noDataMsg = document.getElementById('pie-no-data-msg');
    if (noDataMsg) noDataMsg.style.display = 'flex';
  }
}
