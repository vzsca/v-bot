export function initAuth() {
  const gate = document.querySelector('#authGate');
  const shell = document.querySelector('.app');
  const form = document.querySelector('#authForm');
  const idInput = document.querySelector('#panelId');

  if (!gate || !shell || !form) return;

  function getRequestedPage() {
    return location.hash.slice(1) || 'dashboard';
  }

  function showPanel() {
    gate.hidden = true;
    shell.hidden = false;
    document.body.classList.remove('auth-required');

    const requestedPage = getRequestedPage();
    window.vBotNavigation?.showPage(requestedPage, { updateHash: false });
    window.vBotAccessibility?.updateSkipTarget();
    document.querySelector('#main-content')?.focus({ preventScroll: false });
  }

  form.addEventListener('submit', event => {
    event.preventDefault();

    // UI-only authentication screen for now.
    // The real ID/password validation will be implemented with the backend later.
    showPanel();
  });

  document.title = 'v-bot • Login';
  idInput?.focus();
}
