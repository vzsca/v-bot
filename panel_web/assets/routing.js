/* Frontend-only authentication and hash routing. */
(() => {
  'use strict';

  const AUTH_KEY = 'vbot-panel-connected';

  function connected() {
    return sessionStorage.getItem(AUTH_KEY) === 'true';
  }

  function setConnected(value) {
    sessionStorage.setItem(AUTH_KEY, value ? 'true' : 'false');
  }

  function pageNames() {
    return [...document.querySelectorAll('[data-page]')].map(link => link.dataset.page);
  }

  function render(page) {
    if (!connected()) {
      showConnection();
      return;
    }

    if (!page || page === 'connexion' || !pageNames().includes(page)) {
      page = 'dashboard';
    }

    document.querySelector('#authGate')?.setAttribute('hidden', '');
    const app = document.querySelector('.app');
    if (app) app.removeAttribute('hidden');
    document.body.classList.remove('auth-required');

    document.querySelectorAll('[data-view]').forEach(view => {
      view.hidden = view.dataset.view !== page;
    });

    document.querySelectorAll('[data-page]').forEach(link => {
      const active = link.dataset.page === page;
      link.classList.toggle('active', active);
      link.setAttribute('aria-current', active ? 'page' : 'false');
    });

    const active = document.querySelector(`[data-page="${CSS.escape(page)}"]`);
    const label = active ? active.textContent.replace(/^[^A-Za-z0-9]+/, '').trim() : 'Dashboard';
    const title = document.querySelector('#pageTitle');
    if (title) title.textContent = label;
    document.title = `v-bot • ${label}`;
  }

  function showConnection() {
    const gate = document.querySelector('#authGate');
    const app = document.querySelector('.app');
    if (gate) gate.removeAttribute('hidden');
    if (app) app.setAttribute('hidden', '');
    document.body.classList.add('auth-required');
    document.title = 'v-bot • Connection';
  }

  function navigate(page) {
    if (!connected()) {
      history.replaceState(null, '', `${location.pathname}${location.search}#connexion`);
      showConnection();
      return;
    }

    history.replaceState(null, '', `${location.pathname}${location.search}#${page}`);
    render(page);
  }

  function init() {
    document.querySelectorAll('[data-page]').forEach(link => {
      link.addEventListener('click', event => {
        event.preventDefault();
        navigate(link.dataset.page || 'dashboard');
      });
    });

    const form = document.querySelector('#authForm');
    if (form) {
      form.addEventListener('submit', event => {
        event.preventDefault();
        setConnected(true);
        navigate('dashboard');
      });
    }

    window.addEventListener('hashchange', () => {
      render(location.hash.slice(1));
    });

    const requested = location.hash.slice(1);
    if (!connected()) {
      history.replaceState(null, '', `${location.pathname}${location.search}#connexion`);
      showConnection();
    } else {
      render(requested || 'dashboard');
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
