export async function loadAnalysis() {
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
    `;

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
    if (!stats.holdings || stats.holdings.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8">No holdings found! check .app/portfolio.json</td></tr>';
      return;
    }

    tbody.innerHTML = stats.holdings.map(h => `
      <tr>
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
    if (window.sectorChartInstance) {
      window.sectorChartInstance.destroy();
    }

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
            position: 'right',
            labels: {
              color: '#cccccc',
              boxWidth: 12,
              font: {
                size: 13
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
    document.getElementById('analysis-summary').innerHTML = `<span style="color: red;">Error: ${err.message}</span>`;
    document.getElementById('analysis-body').innerHTML = `<tr><td colspan="8" style="color: red;">Failed to load portfolio analysis</td></tr>`;
  }
}
