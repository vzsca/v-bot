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
links.forEach(a => a.addEventListener("click", e => { e.preventDefault(); showPage(a.dataset.page); }));
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
modalBackdrop?.addEventListener("click", e => { if (e.target === modalBackdrop) closeModal(); });
document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

document.querySelectorAll(".server-invite").forEach(btn => btn.addEventListener("click", () => {
  const name = btn.dataset.server; const url = btn.dataset.invite;
  openModal(`<div class="modal-icon">↗</div><div class="eyebrow">SERVER INVITE</div><h2>Invite link</h2><p class="modal-description">Invite link for <strong>${name}</strong>.</p><div class="invite-box"><input value="${url}" readonly><button class="btn primary" type="button" id="copyInvite">Copy</button></div><span class="modal-hint">Frontend preview only — no real link is generated here.</span>`);
  document.querySelector("#copyInvite")?.addEventListener("click", async () => { try { await navigator.clipboard.writeText(url); } catch (_) {} document.querySelector("#copyInvite").textContent = "Copied ✓"; });
}));

document.querySelectorAll(".server-manage").forEach(btn => btn.addEventListener("click", () => {
  const name = btn.dataset.server;
  openModal(`<div class="modal-icon">⚙</div><div class="eyebrow">SERVER MANAGEMENT</div><h2>${name}</h2><p class="modal-description">This is the future server management workspace.</p><div class="modal-list"><div class="row"><span>Moderation access</span><span class="badge success">ENABLED</span></div><div class="row"><span>Announcement access</span><span class="badge success">ENABLED</span></div><div class="row"><span>Dangerous commands</span><span class="badge danger">DISABLED</span></div><div class="row"><span>Bot permissions</span><span class="badge">ADMIN</span></div></div><div class="actions modal-actions"><button class="btn primary" type="button" id="serverDashboardPreview">Open Server Dashboard</button><button class="btn" type="button" id="serverPermissionsPreview">Permissions</button></div>`);
  document.querySelector("#serverDashboardPreview")?.addEventListener("click", () => { document.querySelector("#serverDashboardPreview").textContent = "Ready ✓"; });
  document.querySelector("#serverPermissionsPreview")?.addEventListener("click", () => { document.querySelector("#serverPermissionsPreview").textContent = "Ready ✓"; });
}));

document.querySelectorAll(".server-api").forEach(btn => btn.addEventListener("click", () => {
  const name = btn.dataset.server;
  openModal(`<div class="modal-icon">⌁</div><div class="eyebrow">API ACCESS</div><h2>${name}</h2><p class="modal-description">Manage which integrations may access this server.</p><div class="access-list"><div class="access-row"><div><strong>Discord API</strong><span>Core bot access</span></div><label class="switch"><input type="checkbox" checked><span></span></label></div><div class="access-row"><div><strong>Twitch</strong><span>Stream notifications</span></div><label class="switch"><input type="checkbox" checked><span></span></label></div><div class="access-row"><div><strong>YouTube</strong><span>Video notifications</span></div><label class="switch"><input type="checkbox"><span></span></label></div></div><div class="actions modal-actions"><button class="btn primary" type="button" id="saveApiPreview">Save Access</button><button class="btn" type="button" id="rotateApiPreview">Rotate Access</button></div>`);
  document.querySelector("#saveApiPreview")?.addEventListener("click", () => { document.querySelector("#saveApiPreview").textContent = "Saved in preview ✓"; });
  document.querySelector("#rotateApiPreview")?.addEventListener("click", () => { document.querySelector("#rotateApiPreview").textContent = "Rotation preview ✓"; });
}));

document.querySelectorAll(".server-leave").forEach(btn => btn.addEventListener("click", () => {
  const name = btn.dataset.server;
  openModal(`<div class="modal-icon danger-text">!</div><div class="eyebrow">DANGEROUS ACTION</div><h2>Leave ${name}?</h2><p class="modal-description">The bot would leave this server in a connected backend. This button is only a visual mockup right now.</p><div class="confirm-box"><span>Server connection will be removed.</span><span class="badge danger">CONFIRMATION REQUIRED</span></div><div class="actions modal-actions"><button class="btn danger" type="button" id="confirmLeave">Leave Server</button><button class="btn" type="button" id="cancelLeave">Cancel</button></div>`);
  document.querySelector("#confirmLeave")?.addEventListener("click", () => { document.querySelector("#confirmLeave").textContent = "Preview only ✓"; });
  document.querySelector("#cancelLeave")?.addEventListener("click", closeModal);
}));

function actionModal(kind, heading, description) {
  openModal(`<div class="modal-icon">${kind === "danger" ? "!" : "✓"}</div><div class="eyebrow">${kind === "danger" ? "CONFIRMATION" : "ACTION"}</div><h2>${heading}</h2><p class="modal-description">${description}</p><div class="actions modal-actions"><button class="btn ${kind === "danger" ? "danger" : "primary"}" id="genericConfirm">Continue</button><button class="btn" id="genericCancel">Cancel</button></div>`);
  document.querySelector("#genericConfirm")?.addEventListener("click", () => { document.querySelector("#genericConfirm").textContent = "Preview only ✓"; });
  document.querySelector("#genericCancel")?.addEventListener("click", closeModal);
}

document.querySelectorAll(".btn").forEach(btn => {
  if (btn.matches(".server-invite,.server-manage,.server-api,.server-leave")) return;
  btn.addEventListener("click", () => {
    const label = btn.textContent.trim().replace(/^[^A-Za-z]+/, "").toLowerCase();
    if (label === "open bot control") showPage("control");
    else if (label.includes("open logs") || label === "view logs") showPage("logs");
    else if (label === "start bot" || label === "start") actionModal("normal", "Start bot", "This frontend is ready for a backend connection. No process is started.");
    else if (label === "stop bot" || label === "stop") actionModal("danger", "Stop bot", "This frontend is ready for a backend connection. No process is stopped.");
    else if (label === "restart") actionModal("normal", "Restart bot", "Restart behavior is simulated. Nothing is executed.");
    else if (label === "refresh") actionModal("normal", "Refresh", "Fresh data will be requested here once a backend is connected.");
    else if (label === "search") actionModal("normal", "Search servers", "The server search flow is ready for backend integration.");
    else if (label === "clear") actionModal("danger", "Clear logs", "Log deletion is not executed in this frontend-only version.");
    else if (["add owner", "manage owners", "change owner"].includes(label)) actionModal("normal", label, "Owner management is currently a UI-only workflow.");
    else if (label === "save changes" || label === "edit") actionModal("normal", label, "Changes are simulated and are not written anywhere.");
    else if (label === "generate code") actionModal("normal", "Generate security code", "The real security-code service is not called by this frontend.");
    else if (label === "check for updates") actionModal("normal", "Check for updates", "The future update service can query GitHub releases. Network access is not used here.");
  });
});

showPage(location.hash.slice(1) || "dashboard");
