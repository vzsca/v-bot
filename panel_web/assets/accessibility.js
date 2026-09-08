export function initAccessibility() {
  const main = document.querySelector('.main');
  const mobileToggle = document.querySelector('#mobileToggle');
  const sidebar = document.querySelector('#sidebar');
  const backdrop = document.querySelector('#modalBackdrop');

  if (main) {
    if (!main.id) main.id = 'main-content';
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
  }, { once: true });

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
}
