export function initNavigation() {
  const views = [...document.querySelectorAll('[data-view]')];
  const links = [...document.querySelectorAll('[data-page]')];
  const title = document.querySelector('#pageTitle');
  const sidebar = document.querySelector('#sidebar');
  const titles = Object.fromEntries(links.map(link => [link.dataset.page, link.textContent.trim()]));

  function showPage(name) {
    if (!titles[name]) name = 'dashboard';
    views.forEach(view => { view.hidden = view.dataset.view !== name; });
    links.forEach(link => {
      const active = link.dataset.page === name;
      link.classList.toggle('active', active);
      link.setAttribute('aria-current', active ? 'page' : 'false');
    });
    if (title) title.textContent = titles[name];
    document.title = `v-bot • ${titles[name]}`;
    history.replaceState(null, '', `#${name}`);
    sidebar?.classList.remove('open');
  }

  links.forEach(link => {
    link.setAttribute('aria-current', link.classList.contains('active') ? 'page' : 'false');
    link.addEventListener('click', event => {
      event.preventDefault();
      showPage(link.dataset.page);
    });
  });

  document.querySelector('#mobileToggle')?.addEventListener('click', () => {
    sidebar?.classList.toggle('open');
  });

  window.vBotNavigation = { showPage };
  showPage(location.hash.slice(1) || 'dashboard');
}
