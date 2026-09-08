/* Standalone frontend bootstrap for panel_web. */

(() => {
  'use strict';

  const AUTH_KEY = 'vbot-panel-connected';
  const state = { modal: null, lastFocused: null };

  document.addEventListener('DOMContentLoaded', init);

  function isConnected() {
    return sessionStorage.getItem(AUTH_KEY) === 'true';
  }

  function setConnected(value) {
    if (value) sessionStorage.setItem(AUTH_KEY, 'true');
    else sessionStorage.removeItem(AUTH_KEY);
  }

  function init() {
    injectStylesheet('assets/ui.css');
    injectStylesheet('assets/polish.css');
    injectStylesheet('assets/auth.css');
    initAccessibility();
    initModals();
    initAuthRouting();
    initNavigation();
    initServers();
    initActions();
    enforceAuthRoute();
  }

  function injectStylesheet(path) {
    if (document.querySelector(`link[href="${path}"]`)) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = path;
    document.head.appendChild(link);
  }

  function goToConnection() {
    history.replaceState(null, '', `${location.pathname}${location.search}#connexion`);
    showConnectionPage();
  }

  function goToDashboard() {
    history.replaceState(null, '', `${location.pathname}${location.search}#dashboard`);
    showDashboardPage();
  }

  function showConnectionPage() {
    const gate = document.querySelector('#authGate');
    const shell = document.querySelector('.app');
    if (gate) gate.hidden = false;
    if (shell) shell.hidden = true;
    document.body.classList.add('auth-required');
    document.title = 'v-bot • Connection';
    document.querySelector('#panelId')?.focus();
  }

  function showDashboardPage() {
    const gate = document.querySelector('#authGate');
    const shell = document.querySelector('.app');
    if (gate) gate.hidden = true;
    if (shell) shell.hidden = false;
    document.body.classList.remove('auth-required');
    initNavigationPage('dashboard');
  }

  function enforceAuthRoute() {
    if (!isConnected()) {
      goToConnection();
      return;
    }
    goToDashboard();
  }

  function initAuthRouting() {
    const form = document.querySelector('#authForm');
    if (!form) return;

    window.vBotConnect = function (event) {
      event?.preventDefault();
      setConnected(true);
      goToDashboard();
      return false;
    };

    form.addEventListener('submit', window.vBotConnect);
  }

  function initNavigation() {
    const links = [...document.querySelectorAll('[data-page]')];
    const sidebar = document.querySelector('#sidebar');
    const mobileToggle = document.querySelector('#mobileToggle');

    links.forEach(link => {
      link.setAttribute('aria-label', getLinkLabel(link));
      link.addEventListener('click', event => {
        if (!isConnected()) {
          event.preventDefault();
          goToConnection();
          return;
        }
        sidebar?.classList.remove('open');
        mobileToggle?.setAttribute('aria-expanded', 'false');
      });
    });

    mobileToggle?.setAttribute('aria-controls', 'sidebar');
    mobileToggle?.setAttribute('aria-expanded', 'false');
    mobileToggle?.addEventListener('click', () => {
      const open = sidebar?.classList.toggle('open') ?? false;
      mobileToggle.setAttribute('aria-expanded', String(open));
    });

    window.addEventListener('hashchange', enforceAuthRoute);
    window.vBotNavigation = { showPage: initNavigationPage };
  }

  function initNavigationPage(name) {
    if (!isConnected()) {
      goToConnection();
      return;
    }

    const labels = Object.fromEntries(
      [...document.querySelectorAll('[data-page]')].map(link => [link.dataset.page, getLinkLabel(link)])
    );
    const page = Object.prototype.hasOwnProperty.call(labels, name) ? name : 'dashboard';
    const views = [...document.querySelectorAll('[data-view]')];
    const links = [...document.querySelectorAll('[data-page]')];
    const title = document.querySelector('#pageTitle');

    views.forEach(view => { view.hidden = view.dataset.view !== page; });
    links.forEach(link => {
      const active = link.dataset.page === page;
      link.classList.toggle('active', active);
      link.setAttribute('aria-current', active ? 'page' : 'false');
    });

    if (title) title.textContent = labels[page] || 'Dashboard';
    document.title = `v-bot • ${labels[page] || 'Dashboard'}`;
    if (location.hash.slice(1) !== page) {
      history.replaceState(null, '', `${location.pathname}${location.search}#${page}`);
    }
  }

  function initAccessibility() {
    const main = document.querySelector('.main');
    const sidebar = document.querySelector('#sidebar');
    const mobileToggle = document.querySelector('#mobileToggle');

    if (main) {
      main.id ||= 'main-content';
      main.setAttribute('tabindex', '-1');
    }

    let skip = document.querySelector('.skip-link');
    if (!skip) {
      skip = document.createElement('a');
      skip.className = 'skip-link';
      skip.href = '#main-content';
      skip.textContent = 'Skip to main content';
      document.body.prepend(skip);
    }

    sidebar?.setAttribute('aria-label', 'Main navigation');
    mobileToggle?.setAttribute('aria-controls', 'sidebar');

    document.querySelectorAll('[data-view]').forEach((view, index) => {
      const heading = view.querySelector('h1, h2');
      if (!heading) return;
      heading.id ||= `page-heading-${index}`;
      view.setAttribute('role', 'region');
      view.setAttribute('aria-labelledby', heading.id);
    });
  }

  function initModals() {
    state.modal = document.querySelector('#modalBackdrop');
    if (!state.modal) return;
    state.modal.setAttribute('aria-hidden', 'true');
    document.querySelector('#modalClose')?.addEventListener('click', closeModal);
    state.modal.addEventListener('click', event => {
      if (event.target === state.modal) closeModal();
    });
    document.addEventListener('keydown', event => {
      if (!state.modal.hidden && event.key === 'Escape') closeModal();
      if (!state.modal.hidden && event.key === 'Tab') trapModalFocus(event);
    });
  }

  function openModal(html, title = 'Dialog') {
    const backdrop = state.modal;
    const container = document.querySelector('#modalContent');
    if (!backdrop || !container || !isConnected()) return;
    state.lastFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    container.innerHTML = html;
    const dialog = backdrop.querySelector('.modal');
    if (!dialog) return;
    const heading = dialog.querySelector('h2, h1');
    const description = dialog.querySelector('.modal-description');
    if (heading) {
      heading.id = 'modalTitle';
      dialog.setAttribute('aria-labelledby', 'modalTitle');
    } else dialog.setAttribute('aria-label', title);
    if (description) {
      description.id = 'modalDescription';
      dialog.setAttribute('aria-describedby', 'modalDescription');
    }
    dialog.setAttribute('tabindex', '-1');
    backdrop.hidden = false;
    backdrop.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    (getFocusable(dialog)[0] || dialog).focus();
  }

  function closeModal() {
    const backdrop = state.modal;
    const container = document.querySelector('#modalContent');
    if (!backdrop || !container) return;
    backdrop.hidden = true;
    backdrop.setAttribute('aria-hidden', 'true');
    container.innerHTML = '';
    document.body.classList.remove('modal-open');
    state.lastFocused?.focus?.();
    state.lastFocused = null;
  }

  function getFocusable(root) {
    return [...root.querySelectorAll('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]
      .filter(el => el instanceof HTMLElement && !el.hidden);
  }

  function trapModalFocus(event) {
    const dialog = state.modal?.querySelector('.modal');
    if (!dialog) return;
    const focusables = getFocusable(dialog);
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

  function initServers() {
    // Existing server interactions remain unchanged in spirit and are frontend-only.
    document.querySelectorAll('.server-invite').forEach(button => button.addEventListener('click', () => {
      const name = button.dataset.server || 'Server';
      const url = button.dataset.invite || 'https://discord.gg/example';
      openModal(`<div class="modal-icon" aria-hidden="true">↗</div><div class="eyebrow">SERVER INVITE</div><h2>${escapeHtml(name)}</h2><p class="modal-description">Copy or open the server invite link.</p><div class="invite-box"><input id="inviteUrl" value="${escapeAttribute(url)}" readonly><button class="btn primary" id="copyInvite" type="button">Copy</button></div>`);
      document.querySelector('#copyInvite')?.addEventListener('click', async event => {
        try { await navigator.clipboard?.writeText(url); } catch (_) {}
        event.currentTarget.textContent = 'Copied ✓';
      });
    }));

    document.querySelectorAll('.server-manage').forEach(button => button.addEventListener('click', () => {
      openModal(`<div class="modal-icon" aria-hidden="true">⚙</div><div class="eyebrow">SERVER MANAGEMENT</div><h2>${escapeHtml(button.dataset.server || 'Server')}</h2><p class="modal-description">Manage server settings, permissions and server-specific features.</p><div class="modal-list">${statusRow('Moderation','ENABLED','success')}${statusRow('Announcements','ENABLED','success')}${statusRow('Dangerous commands','DISABLED','danger')}${statusRow('Bot permission level','ADMIN','')}</div>`);
    }));

    document.querySelectorAll('.server-api').forEach(button => button.addEventListener('click', () => {
      openModal(`<div class="modal-icon" aria-hidden="true">⌁</div><div class="eyebrow">API ACCESS</div><h2>${escapeHtml(button.dataset.server || 'Server')}</h2><p class="modal-description">Choose which integrations are allowed for this server.</p><div class="access-list">${accessRow('Discord API','Core bot access',true)}${accessRow('Twitch','Stream notifications',true)}${accessRow('YouTube','Video notifications',false)}</div>`);
    }));

    document.querySelectorAll('.server-leave').forEach(button => button.addEventListener('click', () => {
      openModal(`<div class="modal-icon danger-text" aria-hidden="true">!</div><div class="eyebrow">DANGEROUS ACTION</div><h2>Leave ${escapeHtml(button.dataset.server || 'Server')}?</h2><p class="modal-description">This action is only a frontend preview.</p><div class="actions modal-actions"><button class="btn danger" type="button">Leave Server</button><button class="btn" id="cancelLeave" type="button">Cancel</button></div>`);
      document.querySelector('#cancelLeave')?.addEventListener('click', closeModal);
    }));
  }

  function initActions() {
    document.querySelectorAll('.btn[data-action]').forEach(button => {
      button.addEventListener('click', () => runAction(button.dataset.action));
    });
  }

  function runAction(action) {
    if (!isConnected()) return goToConnection();
    switch (action) {
      case 'open-control': initNavigationPage('control'); break;
      case 'open-logs': initNavigationPage('logs'); break;
      case 'open-servers': initNavigationPage('servers'); break;
      case 'start': actionModal('BOT CONTROL', 'Start bot'); break;
      case 'stop': actionModal('BOT CONTROL', 'Stop bot'); break;
      case 'restart': actionModal('BOT CONTROL', 'Restart bot'); break;
      case 'refresh': actionModal('SYSTEM', 'Refresh'); break;
      case 'clear-logs': actionModal('LOG MANAGEMENT', 'Clear logs'); break;
      case 'add-owner': actionModal('OWNER MANAGEMENT', 'Add Secondary Owner'); break;
      case 'remove-owner': actionModal('OWNER MANAGEMENT', 'Remove secondary owner'); break;
      case 'manage-owners': actionModal('OWNER MANAGEMENT', 'Manage owners'); break;
      case 'save-changes': actionModal('CONFIGURATION', 'Save changes'); break;
      case 'generate-code': actionModal('SECURITY', 'Generate security code'); break;
      case 'check-updates': actionModal('UPDATES', 'Check for updates'); break;
      case 'search-servers': actionModal('SERVERS', 'Search servers'); break;
      default: break;
    }
  }

  function actionModal(eyebrow, title) {
    openModal(`<div class="modal-icon" aria-hidden="true">✓</div><div class="eyebrow">${eyebrow}</div><h2>${title}</h2><p class="modal-description">Frontend preview only.</p><div class="actions modal-actions"><button class="btn primary" id="genericConfirm" type="button">Confirm</button><button class="btn" id="genericCancel" type="button">Cancel</button></div>`);
    document.querySelector('#genericConfirm')?.addEventListener('click', event => { event.currentTarget.textContent = 'Preview only ✓'; });
    document.querySelector('#genericCancel')?.addEventListener('click', closeModal);
  }

  function getLinkLabel(link) {
    const clone = link.cloneNode(true);
    clone.querySelectorAll('.icon').forEach(icon => icon.remove());
    return clone.textContent.trim();
  }

  function statusRow(label, value, kind) {
    const badge = kind ? `<span class="badge ${kind}">${value}</span>` : `<span class="badge">${value}</span>`;
    return `<div class="row"><span>${label}</span>${badge}</div>`;
  }

  function accessRow(label, description, checked) {
    return `<div class="access-row"><div><strong>${label}</strong><span>${description}</span></div><label class="switch"><input type="checkbox" ${checked ? 'checked' : ''} aria-label="Enable ${label}"><span aria-hidden="true"></span></label></div>`;
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]);
  }

  function escapeAttribute(value) { return escapeHtml(value); }
})();
