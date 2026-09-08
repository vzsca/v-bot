export function initAccessibility() {
  const main = document.querySelector('.main');
  const authGate = document.querySelector('#authGate');
  const mobileToggle = document.querySelector('#mobileToggle');
  const sidebar = document.querySelector('#sidebar');
  const backdrop = document.querySelector('#modalBackdrop');

  if (main) {
    if (!main.id) main.id = 'main-content';
    main.setAttribute('tabindex', '-1');
  }

  if (authGate) {
    authGate.setAttribute('tabindex', '-1');
  }

  let skip = document.querySelector('.skip-link');
  if (!skip) {
    skip = document.createElement('a');
    skip.className = 'skip-link';
    skip.textContent = 'Skip to main content';
    document.body.prepend(skip);
  }

  function updateSkipTarget() {
    const authenticated = document.querySelector('.app') && !document.querySelector('.app').hidden;
    const target = authenticated ? main : authGate;
    if (target) skip.href = `#${target.id || (authenticated ? 'main-content' : 'authGate')}`;
  }

  function handleSkip(event) {
    const href = skip.getAttribute('href');
    const target = href ? document.querySelector(href) : null;
    if (!target || target.hidden) return;
    event.preventDefault();
    target.focus({ preventScroll: true });
    target.scrollIntoView({ block: 'start' });
  }

  skip.addEventListener('click', handleSkip);
  updateSkipTarget();

  document.querySelectorAll('.nav a').forEach(link => {
    if (!link.getAttribute('aria-label')) {
      const clone = link.cloneNode(true);
      clone.querySelectorAll('.icon').forEach(icon => icon.remove());
      const label = clone.textContent.trim();
      if (label) link.setAttribute('aria-label', label);
    }
  });

  document.querySelectorAll('.btn').forEach(button => {
    button.type = 'button';
  });

  mobileToggle?.setAttribute('aria-controls', 'sidebar');
  mobileToggle?.setAttribute('aria-expanded', 'false');
  mobileToggle?.setAttribute('aria-label', 'Open navigation menu');
  sidebar?.setAttribute('aria-label', 'Main navigation');

  document.querySelectorAll('.content[data-view]').forEach((view, index) => {
    const heading = view.querySelector('h1, h2');
    if (!heading) return;
    if (!heading.id) heading.id = `page-heading-${index}`;
    view.setAttribute('role', 'region');
    view.setAttribute('aria-labelledby', heading.id);
  });

  if (backdrop) {
    backdrop.setAttribute('aria-hidden', 'true');
    document.querySelector('#modalClose')?.setAttribute('aria-label', 'Close dialog');
  }

  window.vBotAccessibility = { updateSkipTarget };
}
