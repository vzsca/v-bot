/* v-bot frontend route controller. */
(() => {
  'use strict';

  const AUTH_KEY = 'vbot-panel-connected';

  const isConnected = () => sessionStorage.getItem(AUTH_KEY) === 'true';
  const setConnected = value => sessionStorage.setItem(AUTH_KEY, value ? 'true' : 'false');
  const currentHash = () => window.location.hash.replace(/^#/, '');

  function pageExists(page) {
    return [...document.querySelectorAll('[data-page]')].some(link => link.dataset.page === page);
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

  function render(page) {
    if (!isConnected()) {
      if (currentHash() !== 'connexion') {
        history.replaceState(null, '', `${location.pathname}${location.search}#connexion`);
      }
      showConnection();
      return;
    }

    showPanel();
    const target = page && page !== 'connexion' && pageExists(page) ? page : 'dashboard';

    document.querySelectorAll('[data-view]').forEach(view => {
      view.hidden = view.dataset.view !== target;
    });

    document.querySelectorAll('[data-page]').forEach(link => {
      const active = link.dataset.page === target;
      link.classList.toggle('active', active);
      link.setAttribute('aria-current', active ? 'page' : 'false');
    });

    const activeLink = [...document.querySelectorAll('[data-page]')].find(link => link.dataset.page === target);
    const label = activeLink ? activeLink.textContent.replace(/[^A-Za-zÀ-ÿ0-9 ]/g, '').trim() : 'Dashboard';
    const title = document.getElementById('pageTitle');
    if (title) title.textContent = label;
    document.title = `v-bot • ${label}`;
  }

  function navigate(page) {
    if (!isConnected()) {
      history.replaceState(null, '', `${location.pathname}${location.search}#connexion`);
      showConnection();
      return;
    }
    history.replaceState(null, '', `${location.pathname}${location.search}#${page}`);
    render(page);
  }

  function connect(event) {
    event?.preventDefault?.();
    setConnected(true);
    navigate('dashboard');
    return false;
  }

  function init() {
    window.vBotConnect = connect;
    document.getElementById('authForm')?.addEventListener('submit', connect);

    /* Intercept navigation before any other click handler or native hash navigation. */
    document.addEventListener('click', event => {
      const link = event.target.closest?.('[data-page]');
      if (!link) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      navigate(link.dataset.page || 'dashboard');
    }, true);

    window.addEventListener('hashchange', () => render(currentHash()));

    const requested = currentHash();
    if (isConnected()) {
      render(requested || 'dashboard');
    } else {
      history.replaceState(null, '', `${location.pathname}${location.search}#connexion`);
      showConnection();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
