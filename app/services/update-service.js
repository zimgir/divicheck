const path = require('path');
const fs = require('fs');
const fsPromises = require('fs').promises;
const { spawn } = require('child_process');
const { BrowserWindow } = require('electron');
const { getPortfolioSymbols, writeLastUpdateSnapshot } = require('./portfolio-service');

const POLL_MS = 500;

let task = null;

function rootDir() {
  return path.resolve(__dirname, '..', '..');
}

function appPaths() {
  const root = rootDir();
  return {
    root,
    symbols: path.join(root, '.app', 'symbols_portfolio.txt'),
    progress: path.join(root, '.app', 'update-progress.json'),
    db: path.join(root, '.db', 'divicheck.db'),
    cli: path.join(root, 'db', 'db_cli.py')
  };
}

function pythonPath() {
  if (process.env.DIVICHECK_PYTHON) return process.env.DIVICHECK_PYTHON;
  const venv = path.join(rootDir(), '.venv', 'bin', 'python');
  return fs.existsSync(venv) ? venv : 'python3';
}

function broadcast(channel, payload) {
  if (!BrowserWindow) return;
  for (const win of BrowserWindow.getAllWindows()) {
    win.webContents.send(channel, payload);
  }
}

function readProgress(progressPath) {
  try {
    const raw = fs.readFileSync(progressPath, 'utf8');
    const data = JSON.parse(raw);
    return {
      percent: typeof data.percent === 'number' ? data.percent : 0,
      cur: data.cur,
      total: data.total,
      msg: data.msg || ''
    };
  } catch (e) {
    return null;
  }
}

function getState() {
  if (!task) {
    return { running: false, title: '', percent: 0, cur: null, total: null, msg: '', exitCode: null, error: null };
  }
  return {
    running: task.running,
    title: task.title,
    percent: task.progress.percent,
    cur: task.progress.cur,
    total: task.progress.total,
    msg: task.progress.msg,
    exitCode: task.exitCode,
    error: task.error
  };
}

async function start({ title = 'Portfolio update' } = {}) {
  if (task && task.running) {
    return { success: false, error: 'A database task is already running.' };
  }

  const paths = appPaths();

  const snap = await writeLastUpdateSnapshot();
  if (!snap.success) return snap;

  const symbols = await getPortfolioSymbols();
  if (!symbols || symbols.length === 0) {
    return { success: false, error: 'No portfolio is open.' };
  }

  try {
    await fsPromises.mkdir(path.dirname(paths.symbols), { recursive: true });
    await fsPromises.writeFile(paths.symbols, symbols.join('\n') + '\n', 'utf8');
    await fsPromises.rm(paths.progress, { force: true });
  } catch (e) {
    return { success: false, error: `Failed to prepare update: ${e.message}` };
  }

  const args = [
    paths.cli,
    '--symbols', paths.symbols,
    '--db', paths.db,
    '--progress', paths.progress,
    'update'
  ];

  const child = spawn(pythonPath(), args, { cwd: paths.root });
  task = {
    running: true,
    title,
    child,
    progress: { percent: 0, cur: null, total: null, msg: '' },
    output: '',
    exitCode: null,
    error: null,
    stopped: false,
    timer: null,
    killTimer: null
  };

  const appendOutput = (buf) => {
    task.output = (task.output + buf.toString()).slice(-4000);
  };
  child.stdout.on('data', appendOutput);
  child.stderr.on('data', appendOutput);

  task.timer = setInterval(() => {
    const p = readProgress(paths.progress);
    if (p) {
      task.progress = p;
      broadcast('db-task-update', getState());
    }
  }, POLL_MS);

  child.on('error', (err) => {
    task.error = err.message;
    finish(null);
  });

  child.on('exit', (code) => {
    finish(code);
  });

  broadcast('db-task-update', getState());
  return { success: true };
}

function finish(code) {
  if (!task) return;
  if (task.timer) clearInterval(task.timer);
  if (task.killTimer) clearTimeout(task.killTimer);
  const finalProgress = readProgress(appPaths().progress);
  if (finalProgress) task.progress = finalProgress;
  task.running = false;
  task.exitCode = code;
  if (code !== 0 && !task.stopped && !task.error) {
    const tail = task.output.trim().split('\n').filter(Boolean).slice(-1)[0] || '';
    task.error = `Exited with code ${code}${tail ? ': ' + tail : ''}`;
  }
  broadcast('db-task-update', getState());
  broadcast('db-task-finished', getState());
}

function stop() {
  if (!task || !task.running) return { success: false, error: 'No task running.' };
  task.stopped = true;
  const child = task.child;
  child.kill('SIGTERM');
  task.killTimer = setTimeout(() => {
    if (task && task.running) child.kill('SIGKILL');
  }, 5000);
  return { success: true };
}

module.exports = { start, stop, getState };
