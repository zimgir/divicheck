import './components/divi-table.js';
import { initTaskBar } from './components/task-bar.js';
import { showError } from './components/modal.js';
import { loadAnalysis } from './views/analysis-view.js';
import { loadData } from './views/search-view.js';

window.switchView = function(viewName) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.view-content').forEach(view => view.classList.remove('active'));

  if (viewName === 'analysis') {
    document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
    document.getElementById('view-analysis').classList.add('active');
    loadAnalysis();
  } else if (viewName === 'search') {
    document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
    document.getElementById('view-search').classList.add('active');
    loadData();
  }
};

window.addEventListener('resize', () => {
  document.querySelectorAll('divi-table').forEach(dt => dt.updateStickyHeader());
});

async function updateDbBanner() {
  try {
    const stats = await window.api.getStats();
    const banner = document.getElementById('db-missing-banner');
    if (banner) {
      banner.style.display = stats.db_available === false ? 'block' : 'none';
    }
  } catch (e) {
    const banner = document.getElementById('db-missing-banner');
    if (banner) banner.style.display = 'none';
  }
}

window.updateDbBanner = updateDbBanner;

window.onload = async () => {
  while (!window.api || !window.api.getPortfolioStats) {
    await new Promise(r => setTimeout(r, 50));
  }
  await initTaskBar();
  window.api.onDbTaskFinished((state) => {
    if (state.error) showError(state.error, 'Update failed');
  });
  await updateDbBanner();
  loadAnalysis();
};
