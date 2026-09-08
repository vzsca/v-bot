const AUTH_HASH_KEY = 'vbot-panel-auth';

export function initNavigation() {
  const views = [...document.querySelectorAll('[data-view]')];
  const links = [...document.querySelectorAll('[data-page]')];
  const title = document.querySelector('#pageTitle');
  const sidebar = document.querySelector('#sidebar');
  const mobileToggle = document.querySelector('#mobileToggle');
  const authGate = document.querySelector('#authGate');
  const appShell = document.querySelector('.app');
  const logoutButton = document.querySelector('[data-action="logout"]');
  const changePasswordButton = document.querySelector('[data-action="change-password"]');
  const authForm = document.querySelector('#authForm');

  const pageLabels = Object.fromEntries(links.map(link => [link.dataset.page, getLinkLabel(link)]));

  function getLinkLabel(link) {
    const label = link.getAttribute('aria-label');
    if (label) return label;
    const clone = link.cloneNode(true);
    clone.querySelectorAll('.icon').forEach(icon => icon.remove());
    return clone.textContent.trim();
  }

  function normalizePage(name) {
    return Object.prototype.hasOwnProperty.call(pageLabels, name) ? name : 'dashboard';
  }

  function isAuthenticated() {
    return sessionStorage.getItem(AUTH_HASH_KEY) === 'authenticated';
  }

  function setAuthenticated(value) {
    if (value) sessionStorage.setItem(AUTH_HASH_KEY, 'authenticated');
    else sessionStorage.removeItem(AUTH_HASH_KEY);
    syncAuthView();
  }

  function syncAuthView() {
    const authenticated = isAuthenticated();
    authGate?.toggleAttribute('hidden', authenticated);
    appShell?.toggleAttribute('hidden', !authenticated);
    document.body.classList.toggle('auth-required', !authenticated);
  }

  function showPage(name, { updateHash = true } = {}) {
    const page = normalizePage(name);
    views.forEach(view => { view.hidden = view.dataset.view !== page; });
    links.forEach(link => {
      const active = link.dataset.page === page;
      link.classList.toggle('active', active);
      link.setAttribute('aria-current', active ? 'page' : 'false');
    });
    if (title) title.textContent = pageLabels[page];
    document.title = `v-bot • ${pageLabels[page]}`;
    if (updateHash && location.hash !== `#${page}`) location.hash = page;
    closeMobileSidebar();
  }

  function closeMobileSidebar() {
    sidebar?.classList.remove('open');
    mobileToggle?.setAttribute('aria-expanded', 'false');
  }

  links.forEach(link => {
    link.setAttribute('aria-label', pageLabels[link.dataset.page]);
    link.addEventListener('click', () => closeMobileSidebar());
  });

  window.addEventListener('hashchange', () => showPage(location.hash.slice(1), { updateHash: false }));

  mobileToggle?.setAttribute('aria-controls', 'sidebar');
  mobileToggle?.setAttribute('aria-expanded', 'false');
  mobileToggle?.addEventListener('click', () => {
    const isOpen = sidebar?.classList.toggle('open') ?? false;
    mobileToggle.setAttribute('aria-expanded', String(isOpen));
  });

  authForm?.addEventListener('submit', event => {
    event.preventDefault();
    const submit = authForm.querySelector('button[type="submit"]');
    const id = new FormData(authForm).get('panel-id');
    const password = new FormData(authForm).get('panel-password');
    if (!id || !password) return;
    setAuthenticated(true);
    showPage(location.hash.slice(1) || 'dashboard', { updateHash: false });
    if (submit) submit.textContent = 'Connected ✓';
  });

  logoutButton?.addEventListener('click', () => {
    setAuthenticated(false);
    if (location.hash) history.replaceState(null, '', location.pathname + location.search);
    authForm?.querySelector('input[name="panel-id"]')?.focus();
  });

  changePasswordButton?.addEventListener('click', () => {
    window.dispatchEvent(new CustomEvent('vbot:change-password'));
  });

  window.vBotNavigation = { showPage, setAuthenticated, isAuthenticated, logout: () => setAuthenticated(false) };
  syncAuthView();
  if (isAuthenticated()) showPage(location.hash.slice(1) || 'dashboard', { updateHash: false });
}
