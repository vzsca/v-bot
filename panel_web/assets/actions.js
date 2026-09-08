import { openModal, closeModal } from './modals.js';

export function initActions() {
  document.querySelectorAll('.btn').forEach(button => {
    if (button.matches('.server-invite,.server-manage,.server-api,.server-leave')) return;
    button.type = 'button';
    const action = button.dataset.action || inferAction(button);
    if (!action) return;
    button.dataset.action = action;
    button.addEventListener('click', () => runAction(action, button));
  });
}

function inferAction(button) {
  const label = button.textContent.trim().replace(/^[^A-Za-z]+/, '').toLowerCase();
  const map = new Map([
    ['open bot control', 'open-control'], ['open logs', 'open-logs'], ['view logs', 'open-logs'], ['manage servers', 'open-servers'],
    ['start bot', 'start'], ['start', 'start'], ['stop bot', 'stop'], ['stop', 'stop'], ['restart', 'restart'],
    ['refresh', 'refresh'], ['search', 'search-servers'], ['clear', 'clear-logs'],
    ['add owner', 'add-owner'], ['add secondary owner', 'add-owner'], ['manage owners', 'manage-owners'], ['change owner', 'change-owner'], ['remove', 'remove-owner'],
    ['save changes', 'save-changes'], ['edit', 'edit-integration'], ['generate code', 'generate-code'],
    ['check for updates', 'check-updates'],
  ]);
  return map.get(label) || null;
}

function runAction(action, button) {
  switch (action) {
    case 'open-control': window.vBotNavigation?.showPage('control'); break;
    case 'open-logs': window.vBotNavigation?.showPage('logs'); break;
    case 'open-servers': window.vBotNavigation?.showPage('servers'); break;
    case 'start': actionModal('BOT CONTROL', 'Start bot', 'The button is ready for backend integration. No process is started in this frontend-only version.', 'success'); break;
    case 'stop': actionModal('BOT CONTROL', 'Stop bot', 'The button is ready for backend integration. No process is stopped in this frontend-only version.', 'danger'); break;
    case 'restart': actionModal('BOT CONTROL', 'Restart bot', 'Restart behavior is simulated only. Nothing is executed.', 'primary'); break;
    case 'refresh': actionModal('SYSTEM', 'Refresh', 'Fresh data can be requested here once a backend is connected.', 'primary'); break;
    case 'search-servers':
      openModal(`
        <div class="modal-icon" aria-hidden="true">⌕</div><div class="eyebrow">SERVERS</div>
        <h2>Search servers</h2><p class="modal-description">The search interface is ready for a backend query.</p>
        <div class="field"><label for="serverSearch">Server name or ID</label><input id="serverSearch" placeholder="Gaming Hub"></div>
        <div class="actions modal-actions"><button class="btn primary" id="confirmSearch" type="button">Search</button><button class="btn" id="cancelSearch" type="button">Cancel</button></div>
      `);
      document.querySelector('#confirmSearch')?.addEventListener('click', event => { event.currentTarget.textContent = 'Preview only ✓'; });
      document.querySelector('#cancelSearch')?.addEventListener('click', closeModal);
      break;
    case 'clear-logs': actionModal('LOG MANAGEMENT', 'Clear logs', 'Log deletion is intentionally not executed in this frontend-only version.', 'danger'); break;
    case 'add-owner':
      openModal(`
        <div class="modal-icon" aria-hidden="true">+</div><div class="eyebrow">OWNER MANAGEMENT</div>
        <h2>Add Secondary Owner</h2><p class="modal-description">Add a Discord user ID as a secondary owner.</p>
        <div class="field"><label for="secondaryOwnerId">Discord User ID</label><input id="secondaryOwnerId" inputmode="numeric" placeholder="123456789012345678"></div>
        <div class="actions modal-actions"><button class="btn primary" id="confirmAddOwner" type="button">Add Owner</button><button class="btn" id="cancelAddOwner" type="button">Cancel</button></div>
      `);
      document.querySelector('#confirmAddOwner')?.addEventListener('click', event => { event.currentTarget.textContent = 'Added in preview ✓'; });
      document.querySelector('#cancelAddOwner')?.addEventListener('click', closeModal);
      break;
    case 'remove-owner': actionModal('OWNER MANAGEMENT', 'Remove secondary owner', 'This owner would be removed once a backend is connected. No configuration is changed in this preview.', 'danger'); break;
    case 'manage-owners': actionModal('OWNER MANAGEMENT', 'Manage owners', 'The owner-management workflow is prepared for future backend integration.', 'primary'); break;
    case 'change-owner': actionModal('OWNER MANAGEMENT', 'Change owner', 'Principal-owner changes require backend authorization and are not executed here.', 'danger'); break;
    case 'save-changes': actionModal('CONFIGURATION', 'Save changes', 'The form flow is simulated. No file or bot configuration is modified.', 'primary'); break;
    case 'edit-integration': actionModal('INTEGRATIONS', 'Edit integration', 'Integration editing is currently a frontend-only workflow.', 'primary'); break;
    case 'generate-code': actionModal('SECURITY', 'Generate security code', 'The real security-code service is not called by this frontend.', 'primary'); break;
    case 'check-updates': actionModal('UPDATES', 'Check for updates', 'The future updater can query GitHub releases. No network request is made here.', 'primary'); break;
    default: break;
  }
}

function actionModal(eyebrow, title, description, kind) {
  const confirmClass = kind === 'danger' ? 'danger' : kind === 'success' ? 'success' : 'primary';
  openModal(`
    <div class="modal-icon ${kind === 'danger' ? 'danger-text' : ''}" aria-hidden="true">${kind === 'danger' ? '!' : '✓'}</div>
    <div class="eyebrow">${eyebrow}</div><h2>${title}</h2><p class="modal-description">${description}</p>
    <div class="actions modal-actions"><button class="btn ${confirmClass}" id="genericConfirm" type="button">Confirm</button><button class="btn" id="genericCancel" type="button">Cancel</button></div>
  `);
  document.querySelector('#genericConfirm')?.addEventListener('click', event => { event.currentTarget.textContent = 'Preview only ✓'; });
  document.querySelector('#genericCancel')?.addEventListener('click', closeModal);
}
