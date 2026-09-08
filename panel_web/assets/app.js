/* Frontend-only panel routing and authentication state. */
(() => {
  'use strict';

  const AUTH_KEY = 'vbot-panel-connected';

  document.addEventListener('DOMContentLoaded', init);

  function isConnected() {
    return sessionStorage.getItem(AUTH_KEY) === 'true';
  }

  function setConnected(value) {
    if (value) sessionStorage.setItem(AUTH_KEY, 'true');
    else sessionStorage.removeItem(AUTH_KEY);
  }

  function init() {
    loadPanelStyles();
    setupConnection();
    setupNavigation();
    enforceRoute();
  }

  function loadPanelStyles() {
    for (const path of ['assets/ui.css', 'assets/polish.css', 'assets/auth.css']) {
      if (document.querySelector(`link[href="${path}"]`)) continue;
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = path;
      document.head.appendChild(link);
    }
  }

  function showConnection() {
    const gate = document.getElementById('authGate');
    const app = document.querySelector('.app');
    if (gate) gate.hidden = false;
    if (app) app.hidden = true;
    document.body.classList.add('auth-required');
    document.title = 'v-bot • Connection';
  }

  function showPanel() {
    const gate = document.getElementById('authGate');
    const app = document.querySelector('.app');
    if (gate) gate.hidden = true;
    if (app) app.hidden = false;
    document.body.classList.remove('auth-required');
  }

  function getPageNames() {
    return new Set([...document.querySelectorAll('[data-page]')].map(link => link.dataset.page));
  }

  function renderPage(requestedPage) {
    if (!isConnected()) {
      showConnection();
      if (location.hash !== '#connexion') {
        history.replaceState(null, '', `${location.pathname}${location.search}#connexion`);
      }
      return;
    }

    showPanel();

    const target = requestedPage === 'connexion' ? 'dashboard' : (requestedPage || 'dashboard');
    const pageNames = getPageNames();
    const page = pageNames.has(target) ? target : 'dashboard';
    const views = document.querySelectorAll('[data-view]');
    const links = document.querySelectorAll('[data-page]');

    views.forEach(view => {
      view.hidden = view.dataset.view !== page;
    });

    links.forEach(link => {
      const active = link.dataset.page === page;
      link.classList.toggle('active', active);
      link.setAttribute('aria-current', active ? 'page' : 'false');
    });

    const activeLink = [...links].find(link => link.dataset.page === page);
    const label = activeLink ? getLinkLabel(activeLink) : 'Dashboard';
    const title = document.getElementById('pageTitle');
    if (title) title.textContent = label;
    document.title = `v-bot • ${label}`;

    const desiredHash = `#${page}`;
    if (location.hash !== desiredHash) {
      history.replaceState(null, '', `${location.pathname}${location.search}${desiredHash}`);
    }
  }

  function enforceRoute() {
    renderPage(location.hash.replace(/^#/, ''));
  }

  function setupConnection() {
    const form = document.getElementById('authForm');
    if (!form) return;

    window.vBotConnect = function (event) {
      event?.preventDefault();
      setConnected(true);
      location.hash = '#dashboard';
      return false;
    };

    form.addEventListener('submit', window.vBotConnect);
  }

  function setupNavigation() {
    const sidebar = document.getElementById('sidebar');
    const mobileToggle = document.getElementById('mobileToggle');

    document.querySelectorAll('[data-page]').forEach(link => {
      link.addEventListener('click', event => {
        if (!isConnected()) {
          event.preventDefault();
          location.hash = '#connexion';
          return;
        }

        sidebar?.classList.remove('open');
        mobileToggle?.setAttribute('aria-expanded', 'false');
        // Keep the native href/hash navigation. hashchange renders that exact page.
      });
    });

    mobileToggle?.addEventListener('click', () => {
      const open = sidebar?.classList.toggle('open') ?? false;
      mobileToggle.setAttribute('aria-expanded', String(open));
    });

    window.addEventListener('hashchange', enforceRoute);
  }

  function getLinkLabel(link) {
    const clone = link.cloneNode(true);
    clone.querySelectorAll('.icon').forEach(icon => icon.remove());
    return clone.textContent.trim();
  }
})();
