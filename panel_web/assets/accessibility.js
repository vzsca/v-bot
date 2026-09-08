export function initAccessibility() {
  const main = document.querySelector('.main');
  if (main && !main.id) main.id = 'main-content';

  if (!document.querySelector('.skip-link')) {
    const skip = document.createElement('a');
    skip.className = 'skip-link';
    skip.href = '#main-content';
    skip.textContent = 'Skip to main content';
    document.body.prepend(skip);
  }

  document.querySelectorAll('.nav a').forEach(link => {
    if (!link.getAttribute('aria-label')) link.setAttribute('aria-label', link.textContent.trim());
  });

  document.querySelectorAll('.btn').forEach(button => {
    button.type = 'button';
  });

  const backdrop = document.querySelector('#modalBackdrop');
  if (backdrop) {
    backdrop.setAttribute('aria-hidden', 'true');
    document.querySelector('#modalClose')?.setAttribute('aria-label', 'Close dialog');
  }
}
