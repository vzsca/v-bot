/* v-bot panel frontend — single routing/auth controller. */
(() => {
  'use strict';

  const AUTH_KEY = 'vbot-panel-connected';
  const DEFAULT_PAGE = 'dashboard';

  const state = {
    modal: null,
    lastFocused: null,
  };

  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];

  function isConnected() {
    return sessionStorage.getItem(AUTH_KEY) === 'true';
  }

  function setConnected(value) {
    if (value) sessionStorage.setItem(AUTH_KEY, 'true');
    else sessionStorage.removeItem(AUTH_KEY);
  }

  function currentPage() {
    return window.location.hash.replace(/^#/, '') || DEFAULT_PAGE;
  }

  function pageExists(page) {
    return $$('[data-view]').some(view => view.dataset.view === page);
  }

  function setHash(page) {
    const hash = `#${page}`;
    if (window.location.hash !== hash) window.location.hash = hash;
  }

  function pageLabel(page) {
    const link = $$('[data-page]').find(item => item.dataset.page === page);
    if (!link) return 'Dashboard';
    return link.textContent.trim();
  }

  function renderConnection() {
    const auth = $('#authPage');
    const app = $('#app');
    if (auth) auth.hidden = false;
    if (app) app.hidden = true;
    document.title = 'v-bot • Connection';
    document.body.classList.add('auth-required');
    $('#panelId')?.focus({ preventScroll: true });
  }

  function renderPanel(page) {
    const auth = $('#authPage');
    const app = $('#app');
    if (auth) auth.hidden = true;
    if (app) app.hidden = false;
    document.body.classList.remove('auth-required');

    const target = pageExists(page) ? page : DEFAULT_PAGE;

    $$('[data-view]').forEach(view => {
      view.hidden = view.dataset.view !== target;
    });

    $$('[data-page]').forEach(link => {
      const active = link.dataset.page === target;
      link.classList.toggle('active', active);
      link.setAttribute('aria-current', active ? 'page' : 'false');
    });

    const label = pageLabel(target);
    const title = $('#pageTitle');
    if (title) title.textContent = label;
    document.title = `v-bot • ${label}`;

    if (currentPage() !== target) {
      window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}#${target}`);
    }
  }

  function route() {
    const requested = currentPage();

    if (!isConnected()) {
      if (requested !== 'connexion') setHash('connexion');
      renderConnection();
      return;
    }

    if (requested === 'connexion') {
      setHash(DEFAULT_PAGE);
      renderPanel(DEFAULT_PAGE);
      return;
    }

    renderPanel(requested);
  }

  function connect(event) {
    event?.preventDefault?.();
    setConnected(true);
    setHash(DEFAULT_PAGE);
    return false;
  }

  function navigateFromClick(event) {
    const link = event.target.closest?.('[data-page]');
    if (!link) return;

    event.preventDefault();
    event.stopImmediatePropagation();

    if (!isConnected()) {
      setHash('connexion');
      renderConnection();
      return;
    }

    setHash(link.dataset.page || DEFAULT_PAGE);
  }

  function initNavigation() {
    document.addEventListener('click', navigateFromClick, true);

    window.addEventListener('hashchange', route);

    const mobileToggle = $('#mobileToggle');
    const sidebar = $('#sidebar');
    mobileToggle?.addEventListener('click', () => {
      const open = sidebar?.classList.toggle('open') ?? false;
      mobileToggle.setAttribute('aria-expanded', String(open));
    });

    $$('[data-action]').forEach(button => {
      button.addEventListener('click', () => handleAction(button.dataset.action));
    });
  }

  function handleAction(action) {
    switch (action) {
      case 'open-control': setHash('control'); break;
      case 'open-servers': setHash('servers'); break;
      case 'open-logs': setHash('logs'); break;
      default: showPreview(action);
    }
  }

  function showPreview(action) {
    if (!isConnected()) {
      setHash('connexion');
      return;
    }

    const titles = {
      start: 'Start Bot',
      stop: 'Stop Bot',
      restart: 'Restart Bot',
      refresh: 'Refresh',
      'clear-logs': 'Clear Logs',
      'search-servers': 'Search Servers',
      'add-owner': 'Add Owner',
      'remove-owner': 'Remove Owner',
      'save-changes': 'Save Changes',
      'check-updates': 'Check for Updates',
    };

    openModal(
      `<div class="modal-icon">✓</div><div class="eyebrow">FRONTEND PREVIEW</div><h2>${escapeHtml(titles[action] || 'Action')}</h2><p class="modal-description">This action is not connected to the v-bot backend yet.</p><div class="actions modal-actions"><button class="btn primary" id="previewDone" type="button">Done</button></div>`,
    );
    $('#previewDone')?.addEventListener('click', closeModal);
  }

  function initAuth() {
    const form = $('#authForm');
    if (!form) return;

    window.vBotConnect = connect;
    form.addEventListener('submit', connect);
  }

  function initModalSystem() {
    state.modal = $('#modalBackdrop');
    if (!state.modal) return;

    $('#modalClose')?.addEventListener('click', closeModal);
    state.modal.addEventListener('click', event => {
      if (event.target === state.modal) closeModal();
    });

    document.addEventListener('keydown', event => {
      if (!state.modal || state.modal.hidden) return;
      if (event.key === 'Escape') closeModal();
      if (event.key === 'Tab') trapFocus(event);
    });

    $$('.server-manage').forEach(button => {
      button.addEventListener('click', () => {
        openModal(`<div class="modal-icon">⚙</div><div class="eyebrow">SERVER MANAGEMENT</div><h2>${escapeHtml(button.dataset.server || 'Server')}</h2><p class="modal-description">Server configuration preview.</p><div class="list"><div class="row"><span>Moderation</span><span class="badge success">ENABLED</span></div><div class="row"><span>Announcements</span><span class="badge success">ENABLED</span></div><div class="row"><span>Dangerous commands</span><span class="badge danger">DISABLED</span></div></div>`);
      });
    });

    $$('.server-invite').forEach(button => {
      button.addEventListener('click', () => {
        const server = button.dataset.server || 'Server';
        openModal(`<div class="modal-icon">↗</div><div class="eyebrow">SERVER INVITE</div><h2>${escapeHtml(server)}</h2><p class="modal-description">Invite generation is not connected yet.</p><div class="notice">Frontend preview only.</div>`);
      });
    });

    $$('.server-api').forEach(button => {
      button.addEventListener('click', () => {
        openModal(`<div class="modal-icon">⌁</div><div class="eyebrow">API ACCESS</div><h2>${escapeHtml(button.dataset.server || 'Server')}</h2><p class="modal-description">API access controls will be available after backend integration.</p>`);
      });
    });

    $$('.server-leave').forEach(button => {
      button.addEventListener('click', () => {
        openModal(`<div class="modal-icon danger-text">!</div><div class="eyebrow">DANGEROUS ACTION</div><h2>Leave ${escapeHtml(button.dataset.server || 'Server')}?</h2><p class="modal-description">This is only a frontend preview.</p><div class="actions modal-actions"><button class="btn danger" id="cancelLeave" type="button">Cancel</button></div>`);
        $('#cancelLeave')?.addEventListener('click', closeModal);
      });
    });
  }

  function openModal(html) {
    if (!state.modal || !isConnected()) return;
    const content = $('#modalContent');
    if (!content) return;

    state.lastFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    content.innerHTML = html;
    state.modal.hidden = false;
    document.body.classList.add('modal-open');

    const first = getFocusable(state.modal)[0];
    (first || $('#modalClose'))?.focus();
  }

  function closeModal() {
    if (!state.modal) return;
    state.modal.hidden = true;
    $('#modalContent').innerHTML = '';
    document.body.classList.remove('modal-open');
    state.lastFocused?.focus?.({ preventScroll: true });
    state.lastFocused = null;
  }

  function getFocusable(root) {
    return [...root.querySelectorAll('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href]')];
  }

  function trapFocus(event) {
    const focusables = getFocusable(state.modal);
    if (!focusables.length) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]);
  }

  function init() {
    initAuth();
    initNavigation();
    initModalSystem();
    route();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
