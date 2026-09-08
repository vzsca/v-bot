import { openModal, closeModal } from './modals.js';

export function initServers() {
  bind('.server-invite', button => {
    const name = button.dataset.server || 'Server';
    const url = button.dataset.invite || 'https://discord.gg/example';
    openModal(`
      <div class="modal-icon" aria-hidden="true">↗</div>
      <div class="eyebrow">SERVER INVITE</div>
      <h2>Invite ${escapeHtml(name)}</h2>
      <p class="modal-description">Copy or open the server invite link.</p>
      <div class="invite-box">
        <input id="inviteUrl" value="${escapeAttribute(url)}" readonly aria-label="Server invite link">
        <button class="btn primary" id="copyInvite" type="button">Copy</button>
      </div>
      <span class="modal-hint">Frontend preview only — no invite is generated or fetched.</span>
    `);
    document.querySelector('#copyInvite')?.addEventListener('click', async event => {
      try { await navigator.clipboard.writeText(url); } catch (_) { /* Clipboard may be unavailable on file:// */ }
      event.currentTarget.textContent = 'Copied ✓';
    });
  });

  bind('.server-manage', button => {
    const name = button.dataset.server || 'Server';
    openModal(`
      <div class="modal-icon" aria-hidden="true">⚙</div>
      <div class="eyebrow">SERVER MANAGEMENT</div>
      <h2>${escapeHtml(name)}</h2>
      <p class="modal-description">Manage server settings, permissions and server-specific features.</p>
      <div class="modal-list">
        ${statusRow('Moderation', 'ENABLED', 'success')}
        ${statusRow('Announcements', 'ENABLED', 'success')}
        ${statusRow('Dangerous commands', 'DISABLED', 'danger')}
        ${statusRow('Bot permission level', 'ADMIN', '')}
      </div>
      <div class="actions modal-actions">
        <button class="btn primary" type="button" data-preview-action="server-settings">Server Settings</button>
        <button class="btn" type="button" data-preview-action="permissions">Permissions</button>
      </div>
    `);
    bindPreviewActions();
  });

  bind('.server-api', button => {
    const name = button.dataset.server || 'Server';
    openModal(`
      <div class="modal-icon" aria-hidden="true">⌁</div>
      <div class="eyebrow">API ACCESS</div>
      <h2>${escapeHtml(name)}</h2>
      <p class="modal-description">Choose which integrations are allowed for this server.</p>
      <div class="access-list">
        ${accessRow('Discord API', 'Core bot access', true)}
        ${accessRow('Twitch', 'Stream notifications', true)}
        ${accessRow('YouTube', 'Video notifications', false)}
      </div>
      <div class="actions modal-actions">
        <button class="btn primary" id="saveApiPreview" type="button">Save Access</button>
        <button class="btn" id="rotateApiPreview" type="button">Rotate Access</button>
      </div>
    `);
    document.querySelector('#saveApiPreview')?.addEventListener('click', event => { event.currentTarget.textContent = 'Saved in preview ✓'; });
    document.querySelector('#rotateApiPreview')?.addEventListener('click', event => { event.currentTarget.textContent = 'Rotation preview ✓'; });
  });

  bind('.server-leave', button => {
    const name = button.dataset.server || 'Server';
    openModal(`
      <div class="modal-icon danger-text" aria-hidden="true">!</div>
      <div class="eyebrow">DANGEROUS ACTION</div>
      <h2>Leave ${escapeHtml(name)}?</h2>
      <p class="modal-description">This would make the bot leave the selected server once a real backend is connected.</p>
      <div class="confirm-box"><span>This action cannot be undone from the server.</span><span class="badge danger">CONFIRMATION REQUIRED</span></div>
      <div class="actions modal-actions">
        <button class="btn danger" id="confirmLeave" type="button">Leave Server</button>
        <button class="btn" id="cancelLeave" type="button">Cancel</button>
      </div>
    `);
    document.querySelector('#confirmLeave')?.addEventListener('click', event => { event.currentTarget.textContent = 'Preview only ✓'; });
    document.querySelector('#cancelLeave')?.addEventListener('click', closeModal);
  });
}

function bind(selector, handler) {
  document.querySelectorAll(selector).forEach(button => button.addEventListener('click', () => handler(button)));
}

function bindPreviewActions() {
  document.querySelectorAll('[data-preview-action]').forEach(button => button.addEventListener('click', event => {
    event.currentTarget.textContent = 'Ready ✓';
  }));
}

function statusRow(label, value, kind) {
  const badge = kind ? `<span class="badge ${kind}">${value}</span>` : `<span class="badge">${value}</span>`;
  return `<div class="row"><span>${label}</span>${badge}</div>`;
}

function accessRow(label, description, checked) {
  return `<div class="access-row"><div><strong>${label}</strong><span>${description}</span></div><label class="switch"><input type="checkbox" ${checked ? 'checked' : ''} aria-label="Enable ${label}"><span aria-hidden="true"></span></label></div>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]);
}

function escapeAttribute(value) {
  return escapeHtml(value);
}
