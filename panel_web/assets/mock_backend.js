/* Frontend-only mock backend: UI actions and modal flows without bot/API access. */
(() => {
  const backdrop = document.querySelector('#modalBackdrop');
  const content = document.querySelector('#modalContent');
  const closeButton = document.querySelector('#modalClose');
  if (!backdrop || !content) return;

  const close = () => { backdrop.hidden = true; content.innerHTML = ''; document.body.classList.remove('modal-open'); };
  const open = (html) => { content.innerHTML = html; backdrop.hidden = false; document.body.classList.add('modal-open'); };
  closeButton?.addEventListener('click', close);
  backdrop.addEventListener('click', e => { if (e.target === backdrop) close(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });

  const popup = (eyebrow, title, text, buttons = '') => open(`<div class="modal-icon">✓</div><div class="eyebrow">${eyebrow}</div><h2>${title}</h2><p class="modal-description">${text}</p>${buttons ? `<div class="actions modal-actions">${buttons}</div>` : ''}`);
  const done = (selector, label = 'Preview only ✓') => document.querySelector(selector) && (document.querySelector(selector).textContent = label);

  document.querySelectorAll('.server-invite').forEach(btn => btn.addEventListener('click', () => {
    const name = btn.dataset.server || 'Server'; const url = btn.dataset.invite || 'https://discord.gg/example';
    open(`<div class="modal-icon">↗</div><div class="eyebrow">SERVER INVITE</div><h2>Invite ${name}</h2><p class="modal-description">Copy or open the server invite link.</p><div class="invite-box"><input value="${url}" readonly><button class="btn primary" id="mockCopyInvite">Copy</button></div><span class="modal-hint">Mock UI — no invite is generated or fetched.</span>`);
    document.querySelector('#mockCopyInvite')?.addEventListener('click', async () => { try { await navigator.clipboard.writeText(url); } catch (_) {} done('#mockCopyInvite', 'Copied ✓'); });
  }));

  document.querySelectorAll('.server-manage').forEach(btn => btn.addEventListener('click', () => {
    const name = btn.dataset.server || 'Server';
    open(`<div class="modal-icon">⚙</div><div class="eyebrow">SERVER MANAGEMENT</div><h2>${name}</h2><p class="modal-description">Manage settings, permissions and server-specific features.</p><div class="modal-list"><div class="row"><span>Moderation</span><span class="badge success">ENABLED</span></div><div class="row"><span>Announcements</span><span class="badge success">ENABLED</span></div><div class="row"><span>Dangerous commands</span><span class="badge danger">DISABLED</span></div><div class="row"><span>Bot permission level</span><span class="badge">ADMIN</span></div></div><div class="actions modal-actions"><button class="btn primary" id="mockServerSettings">Server Settings</button><button class="btn" id="mockServerPermissions">Permissions</button></div>`);
    document.querySelector('#mockServerSettings')?.addEventListener('click', () => done('#mockServerSettings', 'Ready ✓'));
    document.querySelector('#mockServerPermissions')?.addEventListener('click', () => done('#mockServerPermissions', 'Ready ✓'));
  }));

  document.querySelectorAll('.server-api').forEach(btn => btn.addEventListener('click', () => {
    const name = btn.dataset.server || 'Server';
    open(`<div class="modal-icon">⌁</div><div class="eyebrow">API ACCESS</div><h2>${name}</h2><p class="modal-description">Choose which integrations are allowed for this server.</p><div class="access-list"><div class="access-row"><div><strong>Discord API</strong><span>Core bot access</span></div><label class="switch"><input type="checkbox" checked><span></span></label></div><div class="access-row"><div><strong>Twitch</strong><span>Stream notifications</span></div><label class="switch"><input type="checkbox" checked><span></span></label></div><div class="access-row"><div><strong>YouTube</strong><span>Video notifications</span></div><label class="switch"><input type="checkbox"><span></span></label></div></div><div class="actions modal-actions"><button class="btn primary" id="mockSaveAccess">Save Access</button><button class="btn" id="mockRotateAccess">Rotate Access</button></div>`);
    document.querySelector('#mockSaveAccess')?.addEventListener('click', () => done('#mockSaveAccess', 'Saved in preview ✓'));
    document.querySelector('#mockRotateAccess')?.addEventListener('click', () => done('#mockRotateAccess', 'Rotation preview ✓'));
  }));

  document.querySelectorAll('.server-leave').forEach(btn => btn.addEventListener('click', () => {
    const name = btn.dataset.server || 'Server';
    open(`<div class="modal-icon danger-text">!</div><div class="eyebrow">DANGEROUS ACTION</div><h2>Leave ${name}?</h2><p class="modal-description">This would make the bot leave the selected server once a real backend is connected.</p><div class="confirm-box"><span>This action cannot be undone from the server.</span><span class="badge danger">CONFIRMATION REQUIRED</span></div><div class="actions modal-actions"><button class="btn danger" id="mockConfirmLeave">Leave Server</button><button class="btn" id="mockCancelLeave">Cancel</button></div>`);
    document.querySelector('#mockConfirmLeave')?.addEventListener('click', () => done('#mockConfirmLeave'));
    document.querySelector('#mockCancelLeave')?.addEventListener('click', close);
  }));

  document.querySelectorAll('.btn').forEach(btn => {
    if (btn.matches('.server-invite,.server-manage,.server-api,.server-leave')) return;
    btn.addEventListener('click', () => {
      const label = btn.textContent.trim().replace(/^[^A-Za-z]+/, ''); const lower = label.toLowerCase();
      if (lower === 'start bot' || lower === 'start') popup('BOT CONTROL', 'Start bot', 'The action flow is ready, but no local process is started in this frontend-only version.', '<button class="btn success" id="mockAction">Confirm start</button><button class="btn" id="mockCancel">Cancel</button>');
      else if (lower === 'stop bot' || lower === 'stop') popup('BOT CONTROL', 'Stop bot', 'The action flow is ready, but no local process is stopped in this frontend-only version.', '<button class="btn danger" id="mockAction">Confirm stop</button><button class="btn" id="mockCancel">Cancel</button>');
      else if (lower === 'restart') popup('BOT CONTROL', 'Restart bot', 'Restart confirmation is simulated only. Nothing is executed.', '<button class="btn primary" id="mockAction">Confirm restart</button><button class="btn" id="mockCancel">Cancel</button>');
      else if (lower.includes('open logs') || lower === 'view logs') location.hash = '#logs';
      else if (lower === 'open bot control') location.hash = '#control';
      else if (lower === 'refresh') popup('SYSTEM', 'Refresh', 'The UI can later request fresh data from the backend. No data source is connected yet.', '<button class="btn primary" id="mockAction">Refresh</button>');
      else if (lower === 'search') popup('SERVERS', 'Search servers', 'This search field is ready for a backend query.', '<div class="field"><label>Server name or ID</label><input placeholder="Gaming Hub"></div><button class="btn primary" id="mockAction">Search</button>');
      else if (lower === 'clear') popup('LOG MANAGEMENT', 'Clear logs', 'Clearing logs is not executed in this mock frontend.', '<button class="btn danger" id="mockAction">Confirm clear</button><button class="btn" id="mockCancel">Cancel</button>');
      else if (lower === 'save changes' || lower === 'save access') popup('CONFIGURATION', 'Save changes', 'The form flow is simulated. No file or bot configuration is modified.', '<button class="btn primary" id="mockAction">Save</button>');
      else if (lower === 'add owner' || lower === 'manage owners' || lower === 'change owner') popup('OWNER MANAGEMENT', label, 'Owner-management UI is prepared for the future backend.', '<button class="btn primary" id="mockAction">Continue</button>');
      else if (lower === 'edit') popup('INTEGRATIONS', 'Edit integration', 'Integration editing is currently a frontend-only form flow.', '<button class="btn primary" id="mockAction">Continue</button>');
      else if (lower === 'generate code') popup('SECURITY', 'Generate security code', 'Only the UI flow is implemented here; the real code generator is not called.', '<button class="btn primary" id="mockAction">Generate</button>');
      else if (lower === 'check for updates') popup('UPDATES', 'Check for updates', 'The future updater can query GitHub releases. This preview does not make network requests.', '<button class="btn primary" id="mockAction">Check</button>');
      else if (lower === 'copy') done(`#${btn.id}`);
      document.querySelector('#mockAction')?.addEventListener('click', () => done('#mockAction'));
      document.querySelector('#mockCancel')?.addEventListener('click', close);
    });
  });
})();
