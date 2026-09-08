/* Standalone frontend bootstrap for panel_web.
   No ES module imports are used here so the preview also works from file://. */

(() => {
  'use strict';

  const state = {
    modal: null,
    lastFocused: null,
    previousHash: '',
  };

  const pageLabels = () => Object.fromEntries(
    [...document.querySelectorAll('[data-page]')].map(link => [link.dataset.page, getLinkLabel(link)])
  );

  document.addEventListener('DOMContentLoaded', init);

  function init() {
    injectStylesheet('assets/ui.css');
    injectStylesheet('assets/polish.css');
    injectStylesheet('assets/auth.css');

    initAccessibility();
    initModals();
    initAuth();
    initNavigation();
    initServers();
    initActions();
  }

  function injectStylesheet(path) {
    if (document.querySelector(`link[href="${path}"]`)) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = path;
    document.head.appendChild(link);
  }

  function initAuth() {
    const gate = document.querySelector('#authGate');
    const shell = document.querySelector('.app');
    const form = document.querySelector('#authForm');
    const idInput = document.querySelector('#panelId');
    const passwordInput = document.querySelector('#panelPassword');

    if (!gate || !shell || !form) return;

    form.addEventListener('submit', event => {
      event.preventDefault();
      const target = location.hash.slice(1);
      gate.hidden = true;
      shell.hidden = false;
      document.body.classList.remove('auth-required');
      initNavigationPage(target || 'dashboard');
    });

    document.title = 'v-bot • Login';
    idInput?.focus();
    void passwordInput;
  }

  function initNavigation() {
    const links = [...document.querySelectorAll('[data-page]')];
    const sidebar = document.querySelector('#sidebar');
    const mobileToggle = document.querySelector('#mobileToggle');
    const pageTitle = document.querySelector('#pageTitle');

    links.forEach(link => {
      link.setAttribute('aria-label', getLinkLabel(link));
      link.addEventListener('click', () => {
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

    window.addEventListener('hashchange', () => {
      initNavigationPage(location.hash.slice(1));
    });

    window.vBotNavigation = { showPage: initNavigationPage };
    initNavigationPage(location.hash.slice(1) || 'dashboard');

    function setTitle(page) {
      if (pageTitle) pageTitle.textContent = pageLabels()[page] || 'Dashboard';
      document.title = `v-bot • ${pageLabels()[page] || 'Dashboard'}`;
    }

    function updateActive(page) {
      links.forEach(link => {
        const active = link.dataset.page === page;
        link.classList.toggle('active', active);
        link.setAttribute('aria-current', active ? 'page' : 'false');
      });
    }

    void setTitle;
    void updateActive;
  }

  function initNavigationPage(name) {
    const labels = pageLabels();
    const page = Object.prototype.hasOwnProperty.call(labels, name) ? name : 'dashboard';
    const views = [...document.querySelectorAll('[data-view]')];
    const links = [...document.querySelectorAll('[data-page]')];
    const title = document.querySelector('#pageTitle');

    views.forEach(view => {
      view.hidden = view.dataset.view !== page;
    });

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

    skip.addEventListener('click', event => {
      const target = document.querySelector('#main-content');
      if (!target) return;
      event.preventDefault();
      target.focus({ preventScroll: true });
      target.scrollIntoView({ block: 'start' });
    });

    sidebar?.setAttribute('aria-label', 'Main navigation');
    mobileToggle?.setAttribute('aria-controls', 'sidebar');

    document.querySelectorAll('[data-view]').forEach((view, index) => {
      const heading = view.querySelector('h1, h2');
      if (!heading) return;
      heading.id ||= `page-heading-${index}`;
      view.setAttribute('role', 'region');
      view.setAttribute('aria-labelledby', heading.id);
    });

    document.querySelectorAll('.btn').forEach(button => {
      button.type = 'button';
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
    if (!backdrop || !container) return;

    state.lastFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    container.innerHTML = html;

    const dialog = backdrop.querySelector('.modal');
    if (!dialog) return;

    const heading = dialog.querySelector('h2, h1');
    const description = dialog.querySelector('.modal-description');
    if (heading) {
      heading.id = 'modalTitle';
      dialog.setAttribute('aria-labelledby', 'modalTitle');
    } else {
      dialog.setAttribute('aria-label', title);
    }
    if (description) {
      description.id = 'modalDescription';
      dialog.setAttribute('aria-describedby', 'modalDescription');
    }

    dialog.setAttribute('tabindex', '-1');
    backdrop.hidden = false;
    backdrop.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');

    const focusables = getFocusable(dialog);
    (focusables[0] || dialog).focus();
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
    document.querySelectorAll('.server-invite').forEach(button => button.addEventListener('click', () => {
      const name = button.dataset.server || 'Server';
      const url = button.dataset.invite || 'https://discord.gg/example';
      openModal(`
        <div class="modal-icon" aria-hidden="true">↗</div>
        <div class="eyebrow">SERVER INVITE</div>
        <h2>Invite ${escapeHtml(name)}</h2>
        <p class="modal-description">Copy or open the server invite link.</p>
        <div class="invite-box"><input id="inviteUrl" value="${escapeAttribute(url)}" readonly aria-label="Server invite link"><button class="btn primary" id="copyInvite" type="button">Copy</button></div>
        <span class="modal-hint">Frontend preview only — no invite is generated or fetched.</span>
      `);
      document.querySelector('#copyInvite')?.addEventListener('click', async event => {
        try { await navigator.clipboard?.writeText(url); } catch (_) { /* file:// may not expose clipboard */ }
        event.currentTarget.textContent = 'Copied ✓';
      });
    }));

    document.querySelectorAll('.server-manage').forEach(button => button.addEventListener('click', () => {
      const name = button.dataset.server || 'Server';
      openModal(`
        <div class="modal-icon" aria-hidden="true">⚙</div>
        <div class="eyebrow">SERVER MANAGEMENT</div>
        <h2>${escapeHtml(name)}</h2>
        <p class="modal-description">Manage server settings, permissions and server-specific features.</p>
        <div class="modal-list">
          ${statusRow('Moderation', 'ENABLED', 'success')}
          ${statusRow('Announcements', 'ENABLED', 'success')}
          ${statusRow('Dangerous commands', 'DISABLED', 'danger')}
          ${statusRow('Bot permission level', 'ADMIN', '')}
        </div>
        <div class="actions modal-actions"><button class="btn primary" type="button" data-preview-action="server-settings">Server Settings</button><button class="btn" type="button" data-preview-action="permissions">Permissions</button></div>
      `);
      bindPreviewActions();
    }));

    document.querySelectorAll('.server-api').forEach(button => button.addEventListener('click', () => {
      const name = button.dataset.server || 'Server';
      openModal(`
        <div class="modal-icon" aria-hidden="true">⌁</div>
        <div class="eyebrow">API ACCESS</div>
        <h2>${escapeHtml(name)}</h2>
        <p class="modal-description">Choose which integrations are allowed for this server.</p>
        <div class="access-list">${accessRow('Discord API', 'Core bot access', true)}${accessRow('Twitch', 'Stream notifications', true)}${accessRow('YouTube', 'Video notifications', false)}</div>
        <div class="actions modal-actions"><button class="btn primary" id="saveApiPreview" type="button">Save Access</button><button class="btn" id="rotateApiPreview" type="button">Rotate Access</button></div>
      `);
      document.querySelector('#saveApiPreview')?.addEventListener('click', event => { event.currentTarget.textContent = 'Saved in preview ✓'; });
      document.querySelector('#rotateApiPreview')?.addEventListener('click', event => { event.currentTarget.textContent = 'Rotation preview ✓'; });
    }));

    document.querySelectorAll('.server-leave').forEach(button => button.addEventListener('click', () => {
      const name = button.dataset.server || 'Server';
      openModal(`
        <div class="modal-icon danger-text" aria-hidden="true">!</div>
        <div class="eyebrow">DANGEROUS ACTION</div>
        <h2>Leave ${escapeHtml(name)}?</h2>
        <p class="modal-description">This would make the bot leave the selected server once a real backend is connected.</p>
        <div class="confirm-box"><span>This action cannot be undone from the server.</span><span class="badge danger">CONFIRMATION REQUIRED</span></div>
        <div class="actions modal-actions"><button class="btn danger" id="confirmLeave" type="button">Leave Server</button><button class="btn" id="cancelLeave" type="button">Cancel</button></div>
      `);
      document.querySelector('#confirmLeave')?.addEventListener('click', event => { event.currentTarget.textContent = 'Preview only ✓'; });
      document.querySelector('#cancelLeave')?.addEventListener('click', closeModal);
    }));
  }

  function initActions() {
    document.querySelectorAll('.btn[data-action]').forEach(button => {
      button.addEventListener('click', () => runAction(button.dataset.action, button));
    });
  }

  function runAction(action, button) {
    switch (action) {
      case 'open-control': initNavigationPage('control'); break;
      case 'open-logs': initNavigationPage('logs'); break;
      case 'open-servers': initNavigationPage('servers'); break;
      case 'start': actionModal('BOT CONTROL', 'Start bot', 'The button is ready for backend integration. No process is started in this frontend-only version.', 'success'); break;
      case 'stop': actionModal('BOT CONTROL', 'Stop bot', 'The button is ready for backend integration. No process is stopped in this frontend-only version.', 'danger'); break;
      case 'restart': actionModal('BOT CONTROL', 'Restart bot', 'Restart behavior is simulated only. Nothing is executed.', 'primary'); break;
      case 'refresh': actionModal('SYSTEM', 'Refresh', 'Fresh data can be requested here once a backend is connected.', 'primary'); break;
      case 'clear-logs': actionModal('LOG MANAGEMENT', 'Clear logs', 'Log deletion is intentionally not executed in this frontend-only version.', 'danger'); break;
      case 'add-owner':
        openModal(`<div class="modal-icon" aria-hidden="true">+</div><div class="eyebrow">OWNER MANAGEMENT</div><h2>Add Secondary Owner</h2><p class="modal-description">Add a Discord user ID as a secondary owner.</p><div class="field"><label for="secondaryOwnerId">Discord User ID</label><input id="secondaryOwnerId" inputmode="numeric" placeholder="123456789012345678"></div><div class="actions modal-actions"><button class="btn primary" id="confirmAddOwner" type="button">Add Owner</button><button class="btn" id="cancelAddOwner" type="button">Cancel</button></div>`);
        document.querySelector('#confirmAddOwner')?.addEventListener('click', event => { event.currentTarget.textContent = 'Added in preview ✓'; });
        document.querySelector('#cancelAddOwner')?.addEventListener('click', closeModal);
        break;
      case 'remove-owner': actionModal('OWNER MANAGEMENT', 'Remove secondary owner', 'This owner would be removed once a backend is connected. No configuration is changed in this preview.', 'danger'); break;
      case 'manage-owners': actionModal('OWNER MANAGEMENT', 'Manage owners', 'The owner-management workflow is prepared for future backend integration.', 'primary'); break;
      case 'save-changes': actionModal('CONFIGURATION', 'Save changes', 'The form flow is simulated. No file or bot configuration is modified.', 'primary'); break;
      case 'generate-code': actionModal('SECURITY', 'Generate security code', 'The real security-code service is not called by this frontend.', 'primary'); break;
      case 'check-updates': actionModal('UPDATES', 'Check for updates', 'The future updater can query GitHub releases. No network request is made here.', 'primary'); break;
      case 'search-servers':
        openModal(`<div class="modal-icon" aria-hidden="true">⌕</div><div class="eyebrow">SERVERS</div><h2>Search servers</h2><p class="modal-description">The search interface is ready for a backend query.</p><div class="field"><label for="serverSearch">Server name or ID</label><input id="serverSearch" placeholder="Gaming Hub"></div><div class="actions modal-actions"><button class="btn primary" id="confirmSearch" type="button">Search</button><button class="btn" id="cancelSearch" type="button">Cancel</button></div>`);
        document.querySelector('#confirmSearch')?.addEventListener('click', event => { event.currentTarget.textContent = 'Preview only ✓'; });
        document.querySelector('#cancelSearch')?.addEventListener('click', closeModal);
        break;
      default:
        void button;
        break;
    }
  }

  function actionModal(eyebrow, title, description, kind) {
    const confirmClass = kind === 'danger' ? 'danger' : kind === 'success' ? 'success' : 'primary';
    openModal(`<div class="modal-icon ${kind === 'danger' ? 'danger-text' : ''}" aria-hidden="true">${kind === 'danger' ? '!' : '✓'}</div><div class="eyebrow">${eyebrow}</div><h2>${title}</h2><p class="modal-description">${description}</p><div class="actions modal-actions"><button class="btn ${confirmClass}" id="genericConfirm" type="button">Confirm</button><button class="btn" id="genericCancel" type="button">Cancel</button></div>`);
    document.querySelector('#genericConfirm')?.addEventListener('click', event => { event.currentTarget.textContent = 'Preview only ✓'; });
    document.querySelector('#genericCancel')?.addEventListener('click', closeModal);
  }

  function bindPreviewActions() {
    document.querySelectorAll('[data-preview-action]').forEach(button => button.addEventListener('click', event => {
      event.currentTarget.textContent = 'Ready ✓';
    }));
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

  function escapeAttribute(value) {
    return escapeHtml(value);
  }
})();
