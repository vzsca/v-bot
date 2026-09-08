export function initNavigation() {
  const views = [...document.querySelectorAll('[data-view]')];
  const links = [...document.querySelectorAll('[data-page]')];
  const title = document.querySelector('#pageTitle');
  const sidebar = document.querySelector('#sidebar');
  const mobileToggle = document.querySelector('#mobileToggle');

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
    link.addEventListener('click', closeMobileSidebar);
  });

  window.addEventListener('hashchange', () => {
    if (window.vBotAuth?.isAuthenticated?.() === false) return;
    showPage(location.hash.slice(1), { updateHash: false });
  });

  mobileToggle?.setAttribute('aria-controls', 'sidebar');
  mobileToggle?.setAttribute('aria-expanded', 'false');
  mobileToggle?.addEventListener('click', () => {
    const isOpen = sidebar?.classList.toggle('open') ?? false;
    mobileToggle.setAttribute('aria-expanded', String(isOpen));
  });

  window.vBotNavigation = { showPage };
  if (window.vBotAuth?.isAuthenticated?.() !== false) {
    showPage(location.hash.slice(1) || 'dashboard', { updateHash: false });
  }
}
