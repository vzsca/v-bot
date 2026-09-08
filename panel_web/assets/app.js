const views = [...document.querySelectorAll("[data-view]")];
const links = [...document.querySelectorAll("[data-page]")];
const title = document.querySelector("#pageTitle");
const sidebar = document.querySelector(".sidebar");
const modalBackdrop = document.querySelector("#modalBackdrop");
const modalContent = document.querySelector("#modalContent");
const modalClose = document.querySelector("#modalClose");
const titles = Object.fromEntries(links.map(a => [a.dataset.page, a.textContent.trim()]));

function showPage(name) {
  if (!titles[name]) name = "dashboard";
  views.forEach(v => { v.hidden = v.dataset.view !== name; });
  links.forEach(a => a.classList.toggle("active", a.dataset.page === name));
  if (title) title.textContent = titles[name];
  document.title = `v-bot • ${titles[name]}`;
  history.replaceState(null, "", `#${name}`);
  sidebar?.classList.remove("open");
}

links.forEach(a => a.addEventListener("click", e => {
  e.preventDefault();
  showPage(a.dataset.page);
}));

document.querySelector("#mobileToggle")?.addEventListener("click", () => sidebar?.classList.toggle("open"));

function openModal(html) {
  if (!modalBackdrop || !modalContent) return;
  modalContent.innerHTML = html;
  modalBackdrop.hidden = false;
  document.body.classList.add("modal-open");
}

function closeModal() {
  if (!modalBackdrop || !modalContent) return;
  modalBackdrop.hidden = true;
  modalContent.innerHTML = "";
  document.body.classList.remove("modal-open");
}

modalClose?.addEventListener("click", closeModal);
modalBackdrop?.addEventListener("click", e => {
  if (e.target === modalBackdrop) closeModal();
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape") closeModal();
});

document.querySelectorAll(".server-invite").forEach(btn => btn.addEventListener("click", () => {
  const name = btn.dataset.server;
  const url = btn.dataset.invite;
  openModal(`<div class="modal-icon">↗</div><div class="eyebrow">SERVER INVITE</div><h2>Invite link</h2><p class="modal-description">Invite link for <strong>${name}</strong>.</p><div class="invite-box"><input value="${url}" readonly><button class="btn primary" type="button" id="copyInvite">Copy</button></div><span class="modal-hint">Frontend preview only — no real link is generated here.</span>`);
  document.querySelector("#copyInvite")?.addEventListener("click", () => {
    document.querySelector("#copyInvite").textContent = "Copied ✓";
  });
}));

document.querySelectorAll(".server-manage").forEach(btn => btn.addEventListener("click", () => {
  const name = btn.dataset.server;
  openModal(`<div class="modal-icon">⚙</div><div class="eyebrow">SERVER MANAGEMENT</div><h2>${name}</h2><p class="modal-description">This is the future server management workspace.</p><div class="modal-list"><div class="row"><span>Moderation access</span><span class="badge success">ENABLED</span></div><div class="row"><span>Announcement access</span><span class="badge success">ENABLED</span></div><div class="row"><span>Dangerous commands</span><span class="badge danger">DISABLED</span></div><div class="row"><span>Bot permissions</span><span class="badge">ADMIN</span></div></div><div class="actions modal-actions"><button class="btn primary">Open Server Dashboard</button><button class="btn">Permissions</button></div>`);
}));

document.querySelectorAll(".server-api").forEach(btn => btn.addEventListener("click", () => {
  const name = btn.dataset.server;
  openModal(`<div class="modal-icon">⌁</div><div class="eyebrow">API ACCESS</div><h2>${name}</h2><p class="modal-description">Manage which integrations may access this server.</p><div class="access-list"><div class="access-row"><div><strong>Discord API</strong><span>Core bot access</span></div><label class="switch"><input type="checkbox" checked><span></span></label></div><div class="access-row"><div><strong>Twitch</strong><span>Stream notifications</span></div><label class="switch"><input type="checkbox" checked><span></span></label></div><div class="access-row"><div><strong>YouTube</strong><span>Video notifications</span></div><label class="switch"><input type="checkbox"><span></span></label></div></div><div class="actions modal-actions"><button class="btn primary">Save Access</button><button class="btn">Rotate Access</button></div>`);
}));

document.querySelectorAll(".server-leave").forEach(btn => btn.addEventListener("click", () => {
  const name = btn.dataset.server;
  openModal(`<div class="modal-icon danger-text">!</div><div class="eyebrow">DANGEROUS ACTION</div><h2>Leave ${name}?</h2><p class="modal-description">The bot would leave this server in a connected backend. This button is only a visual mockup right now.</p><div class="confirm-box"><span>Server connection will be removed.</span><span class="badge danger">CONFIRMATION REQUIRED</span></div><div class="actions modal-actions"><button class="btn danger" type="button" id="confirmLeave">Leave Server</button><button class="btn" type="button" id="cancelLeave">Cancel</button></div>`);
  document.querySelector("#confirmLeave")?.addEventListener("click", () => {
    document.querySelector("#confirmLeave").textContent = "Preview only ✓";
  });
  document.querySelector("#cancelLeave")?.addEventListener("click", closeModal);
}));

showPage(location.hash.slice(1) || "dashboard");
