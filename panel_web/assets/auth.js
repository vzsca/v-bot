import { openModal, closeModal } from './modals.js';

const AUTH_STATE_KEY = 'vbot-panel-authenticated';

export function initAuth() {
  const gate = document.querySelector('#authGate');
  const shell = document.querySelector('.app');
  const form = document.querySelector('#authForm');
  const idInput = document.querySelector('#panelId');
  const passwordInput = document.querySelector('#panelPassword');
  const submit = document.querySelector('#authSubmit');
  const logout = document.querySelector('[data-action="logout"]');
  const changePassword = document.querySelector('[data-action="change-password"]');

  if (!gate || !shell || !form) return;

  function isAuthenticated() {
    return sessionStorage.getItem(AUTH_STATE_KEY) === 'true';
  }

  function sync() {
    const authenticated = isAuthenticated();
    gate.hidden = authenticated;
    shell.hidden = !authenticated;
    document.body.classList.toggle('auth-required', !authenticated);
    if (!authenticated) document.title = 'v-bot • Login';
  }

  function login() {
    const id = idInput?.value.trim();
    const password = passwordInput?.value;
    if (!id || !password) {
      form.reportValidity();
      return;
    }

    // Frontend-only preview: a future backend will validate the credentials.
    sessionStorage.setItem(AUTH_STATE_KEY, 'true');
    sync();
    window.vBotNavigation?.showPage(location.hash.slice(1) || 'dashboard', { updateHash: false });
    if (submit) submit.textContent = 'Connected ✓';
  }

  function logoutUser() {
    sessionStorage.removeItem(AUTH_STATE_KEY);
    if (location.hash) history.replaceState(null, '', location.pathname + location.search);
    sync();
    form.reset();
    if (submit) submit.textContent = 'Connect';
    idInput?.focus();
  }

  function showChangePassword() {
    openModal(`
      <div class="modal-icon" aria-hidden="true">⌁</div>
      <div class="eyebrow">SECURITY</div>
      <h2>Change password</h2>
      <p class="modal-description">Update the local panel password. Password changes are simulated until a backend is connected.</p>
      <form id="changePasswordForm" class="stacked-form">
        <div class="field">
          <label for="currentPassword">Current password</label>
          <input id="currentPassword" name="currentPassword" type="password" autocomplete="current-password" required>
        </div>
        <div class="field">
          <label for="newPassword">New password</label>
          <input id="newPassword" name="newPassword" type="password" autocomplete="new-password" minlength="8" required>
        </div>
        <div class="field">
          <label for="confirmPassword">Confirm new password</label>
          <input id="confirmPassword" name="confirmPassword" type="password" autocomplete="new-password" minlength="8" required>
        </div>
        <div class="actions modal-actions">
          <button class="btn primary" type="submit">Change password</button>
          <button class="btn" type="button" id="cancelPasswordChange">Cancel</button>
        </div>
      </form>
    `);

    const passwordForm = document.querySelector('#changePasswordForm');
    passwordForm?.addEventListener('submit', event => {
      event.preventDefault();
      const data = new FormData(passwordForm);
      const next = String(data.get('newPassword') || '');
      const confirm = String(data.get('confirmPassword') || '');
      const confirmInput = document.querySelector('#confirmPassword');
      confirmInput?.setCustomValidity('');
      if (next.length < 8 || next !== confirm) {
        confirmInput?.setCustomValidity(next !== confirm ? 'Passwords do not match.' : 'Password must contain at least 8 characters.');
        confirmInput?.reportValidity();
        return;
      }
      closeModal();
      showPreviewNotice('Password updated in preview', 'The password change is ready for backend integration.');
    });
    document.querySelector('#cancelPasswordChange')?.addEventListener('click', closeModal);
  }

  form.addEventListener('submit', event => {
    event.preventDefault();
    login();
  });
  logout?.addEventListener('click', logoutUser);
  changePassword?.addEventListener('click', showChangePassword);

  window.vBotAuth = { isAuthenticated, login, logout: logoutUser, showChangePassword };
  sync();
  if (!isAuthenticated()) idInput?.focus();
}

function showPreviewNotice(title, description) {
  openModal(`
    <div class="modal-icon" aria-hidden="true">✓</div>
    <div class="eyebrow">SECURITY</div>
    <h2>${title}</h2>
    <p class="modal-description">${description}</p>
    <div class="actions modal-actions"><button class="btn primary" id="closePreviewNotice" type="button">Done</button></div>
  `);
  document.querySelector('#closePreviewNotice')?.addEventListener('click', closeModal);
}
