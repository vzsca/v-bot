export function initAccessibility() {
  const main = document.querySelector('.main');
  const mobileToggle = document.querySelector('#mobileToggle');
  const sidebar = document.querySelector('#sidebar');
  const backdrop = document.querySelector('#modalBackdrop');

  if (main) {
    if (!main.id) main.id = 'main-content';
    main.setAttribute('tabindex', '-1');
  }

  if (!document.querySelector('.skip-link')) {
    const skip = document.createElement('a');
    skip.className = 'skip-link';
    skip.href = '#main-content';
    skip.textContent = 'Skip to main content';
    document.body.prepend(skip);
  }

  document.querySelectorAll('.nav a').forEach(link => {
    if (!link.getAttribute('aria-label')) {
      const clone = link.cloneNode(true);
      clone.querySelectorAll('.icon').forEach(icon => icon.remove());
      link.setAttribute('aria-label', clone.textContent.trim());
    }
  });

  document.querySelectorAll('.btn').forEach(button => {
    button.type = 'button';
  });

  mobileToggle?.setAttribute('aria-controls', 'sidebar');
  mobileToggle?.setAttribute('aria-expanded', 'false');
  sidebar?.setAttribute('aria-label', 'Main navigation');

  if (backdrop) {
    backdrop.setAttribute('aria-hidden', 'true');
    document.querySelector('#modalClose')?.setAttribute('aria-label', 'Close dialog');
  }
}
