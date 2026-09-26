const $ = id => document.getElementById(id);
const DEMO = window.location.hostname.endsWith("github.io");
const DEMO_TOKEN = "vbot-demo-token";
const DEMO_LOGS = [
  "[DEMO] v-bot started successfully",
  "[DEMO] Connected to Discord gateway",
  "[DEMO] No real Discord action was executed"
];

async function api(path, options = {}) {
  if (DEMO) return demoApi(path, options);
  const r = await fetch(path, { credentials: "same-origin", ...options });
  if (r.status === 401) {
    $("dashboard").hidden = true;
    $("login").hidden = false;
    throw new Error("Authentication required");
  }
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || "Request failed");
  return d;
}

function demoApi(path, options = {}) {
  if (path === "/api/login") {
    let body = {};
    try { body = JSON.parse(options.body || "{}"); } catch {}
    if (body.token !== DEMO_TOKEN) throw new Error("Invalid demo token. Use: vbot-demo-token");
    return { ok: true };
  }
  if (path === "/api/logout") return { ok: true };
  if (path === "/api/status") {
    return {
      version: "demo",
      platform: "github-pages",
      bot_running: true,
      pid: 12345,
      dangerous_commands_enabled: false,
      action_code_ttl: 60,
      demo: true
    };
  }
  if (path === "/api/logs") return { lines: DEMO_LOGS };
  if (path === "/api/action-code") {
    let body = {};
    try { body = JSON.parse(options.body || "{}"); } catch {}
    const action = body.action || "unknown";
    return {
      action,
      code: "123456",
      expires_at: Math.floor(Date.now() / 1000) + 60,
      demo: true
    };
  }
  throw new Error("Unknown demo endpoint");
}

async function refresh() {
  const s = await api("/api/status");
  $("status").textContent = JSON.stringify(s, null, 2);
  const l = await api("/api/logs");
  $("logs").textContent = l.lines.join("\n") || "No log entries.";
}

if (DEMO) {
  $("mode").textContent = "Web Panel • DEMO";
  $("demoBanner").hidden = false;
}

$("loginBtn").onclick = async () => {
  try {
    await api("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: $("token").value })
    });
    $("token").value = "";
    $("login").hidden = true;
    $("dashboard").hidden = false;
    await refresh();
  } catch (e) {
    $("loginError").textContent = e.message;
  }
};

$("codeBtn").onclick = async () => {
  try {
    $("code").textContent = JSON.stringify(
      await api("/api/action-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: $("action").value })
      }),
      null,
      2
    );
  } catch (e) {
    $("code").textContent = e.message;
  }
};

$("logoutBtn").onclick = async () => {
  await api("/api/logout", { method: "POST" });
  $("dashboard").hidden = true;
  $("login").hidden = false;
};

setInterval(() => refresh().catch(() => {}), 5000);
