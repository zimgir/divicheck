export async function initTaskBar() {
  const bar = document.getElementById('db-task-bar');
  const titleEl = document.getElementById('db-task-title');
  const fillEl = document.getElementById('db-task-fill');
  const textEl = document.getElementById('db-task-text');
  const stopBtn = document.getElementById('db-task-stop-btn');

  stopBtn.addEventListener('click', () => window.api.stopPortfolioUpdate());

  const show = (state) => {
    if (!state.running) {
      bar.classList.add('hidden');
      return;
    }
    bar.classList.remove('hidden');
    titleEl.textContent = state.title || 'Portfolio update';
    fillEl.style.width = `${state.percent || 0}%`;
    const parts = [];
    if (state.msg) parts.push(state.msg);
    if (state.cur != null && state.total != null) parts.push(`${state.cur} / ${state.total}`);
    parts.push(`${state.percent || 0}%`);
    textEl.textContent = parts.join(' - ');
  };

  const initial = await window.api.getDbTaskState();
  show(initial);

  window.api.onDbTaskUpdate((state) => show(state));
  window.api.onDbTaskFinished(async (state) => {
    show(state);
    await refreshActiveView();
  });
}

async function refreshActiveView() {
  const active = document.querySelector('.view-content.active');
  if (!active) return;
  if (active.id === 'view-analysis') {
    const { loadAnalysis } = await import('../views/analysis-view.js');
    await loadAnalysis();
  } else if (active.id === 'view-search') {
    const { loadData } = await import('../views/search-view.js');
    await loadData();
  }
}
