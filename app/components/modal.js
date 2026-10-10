const MODAL_ID = 'popup-modal';
const TITLE_ID = 'popup-title';
const MESSAGE_ID = 'popup-message';
const OK_ID = 'popup-ok-btn';

let bound = false;

function el(id) {
  return document.getElementById(id);
}

function ensureBound() {
  if (bound) return;
  const ok = el(OK_ID);
  if (ok) {
    ok.addEventListener('click', hide);
    bound = true;
  }
}

export function showMessage(message, title = 'Message') {
  const modal = el(MODAL_ID);
  if (!modal) return;
  const titleEl = el(TITLE_ID);
  if (titleEl) titleEl.textContent = title;
  const msgEl = el(MESSAGE_ID);
  if (msgEl) msgEl.value = message;
  modal.style.display = 'flex';
  ensureBound();
}

export function showError(message, title = 'Error') {
  showMessage(message, title);
}

export function hide() {
  const modal = el(MODAL_ID);
  if (modal) modal.style.display = 'none';
}
