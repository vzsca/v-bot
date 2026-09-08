let backdrop = null;
let content = null;
let closeButton = null;
let lastFocused = null;
let trapHandler = null;

export function initModals() {
  backdrop = document.querySelector('#modalBackdrop');
  content = document.querySelector('#modalContent');
  closeButton = document.querySelector('#modalClose');
  if (!backdrop || !content) return;

  backdrop.setAttribute('aria-hidden', 'true');
  closeButton?.setAttribute('aria-label', 'Close dialog');
  closeButton?.addEventListener('click', closeModal);
  backdrop.addEventListener('click', event => {
    if (event.target === backdrop) closeModal();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !backdrop.hidden) closeModal();
  });
}

export function openModal(html, titleText = 'Dialog', descriptionText = '') {
  if (!backdrop || !content) return;
  lastFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  content.innerHTML = html;
  const dialog = backdrop.querySelector('.modal');
  if (!dialog) return;

  const title = dialog.querySelector('h2');
  const description = dialog.querySelector('.modal-description');
  if (title) {
    title.id = 'modalTitle';
    dialog.setAttribute('aria-labelledby', 'modalTitle');
  } else {
    dialog.setAttribute('aria-label', titleText);
  }
  if (description) {
    description.id = 'modalDescription';
    dialog.setAttribute('aria-describedby', 'modalDescription');
  } else if (descriptionText) {
    dialog.setAttribute('aria-label', `${titleText}. ${descriptionText}`);
  }
  dialog.setAttribute('tabindex', '-1');
  backdrop.hidden = false;
  backdrop.setAttribute('aria-hidden', 'false');
  document.body.classList.add('modal-open');

  const focusables = getFocusable(dialog);
  (focusables[0] || dialog).focus();
  trapHandler = event => {
    if (event.key !== 'Tab') return;
    const elements = getFocusable(dialog);
    if (!elements.length) return;
    const first = elements[0];
    const last = elements[elements.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };
  document.addEventListener('keydown', trapHandler);
}

export function closeModal() {
  if (!backdrop || !content) return;
  backdrop.hidden = true;
  backdrop.setAttribute('aria-hidden', 'true');
  content.innerHTML = '';
  document.body.classList.remove('modal-open');
  if (trapHandler) {
    document.removeEventListener('keydown', trapHandler);
    trapHandler = null;
  }
  lastFocused?.focus?.();
  lastFocused = null;
}

export function getFocusable(root) {
  return [...root.querySelectorAll(
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )].filter(element => element instanceof HTMLElement && !element.hidden);
}
