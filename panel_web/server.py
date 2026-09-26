"""Local-only aiohttp control panel for v-bot."""

from __future__ import annotations

import hmac
import json
import os
import secrets
import sys
import time
from pathlib import Path

import psutil
from aiohttp import web

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent
TOKEN_FILE = STATIC_DIR / ".token"
SESSION_COOKIE = "vbot_panel_session"
SESSION_TTL = 3600
ACTIONS = {"spam", "dmall", "raid", "remove_raid"}


def _load_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")


def _token() -> str:
    value = os.getenv("PANEL_WEB_TOKEN", "").strip()
    if value:
        return value

    if TOKEN_FILE.exists():
        value = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value

    value = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(value + "\n", encoding="utf-8")
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass

    print(f"Web panel token: {value}")
    return value


def _authorized(request: web.Request) -> bool:
    session = request.cookies.get(SESSION_COOKIE, "")
    if not session:
        return False
    expires_at = request.app["sessions"].get(session)
    if expires_at is None:
        return False
    if expires_at <= time.time():
        request.app["sessions"].pop(session, None)
        return False
    return True


@web.middleware
async def auth(request: web.Request, handler):
    public_paths = {"/", "/panel_web", "/panel_web/", "/panel_web/signin", "/panel_web/signin/", "/panel_web/app.js", "/panel_web/style.css", "/api/login"}
    page_paths = {"/panel_web/dashboard", "/panel_web/dashboard/", "/panel_web/instance", "/panel_web/instance/", "/panel_web/activity", "/panel_web/activity/", "/panel_web/logs", "/panel_web/logs/", "/panel_web/security", "/panel_web/security/"}
    if request.path in public_paths:
        if request.path in {"/signin", "/signin/"} and _authorized(request):
            raise web.HTTPFound("/panel_web/dashboard")
        return await handler(request)
    if request.path in page_paths:
        if not _authorized(request):
            raise web.HTTPFound("/panel_web/signin")
        return await handler(request)
    if not _authorized(request):
        return web.json_response({"error": "authentication required"}, status=401)
    return await handler(request)


async def index(request: web.Request) -> web.Response:
    del request
    raise web.HTTPFound("/panel_web/signin")


async def asset(request: web.Request) -> web.FileResponse:
    return web.FileResponse(STATIC_DIR / request.match_info["name"])


async def login(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except (json.JSONDecodeError, ValueError):
        return web.json_response({"error": "invalid JSON"}, status=400)

    if not hmac.compare_digest(str(data.get("token", "")), _token()):
        return web.json_response({"error": "invalid token"}, status=401)

    session = secrets.token_urlsafe(32)
    request.app["sessions"][session] = time.time() + SESSION_TTL
    response = web.json_response({"ok": True})
    response.set_cookie(
        SESSION_COOKIE,
        session,
        httponly=True,
        samesite="Strict",
        max_age=SESSION_TTL,
        path="/",
    )
    return response


async def logout(request: web.Request) -> web.Response:
    request.app["sessions"].pop(request.cookies.get(SESSION_COOKIE, ""), None)
    response = web.json_response({"ok": True})
    response.del_cookie(SESSION_COOKIE, path="/")
    return response


async def status(request: web.Request) -> web.Response:
    del request

    sys.path.insert(0, str(ROOT / "app"))
    import config
    from version import VERSION

    pid_file = ROOT / "bot.pid"
    bot_pid = None
    if pid_file.exists():
        try:
            candidate = int(pid_file.read_text(encoding="utf-8").strip())
            if candidate > 0 and psutil.pid_exists(candidate):
                bot_pid = candidate
        except (OSError, ValueError):
            pass

    return web.json_response(
        {
            "version": VERSION,
            "platform": sys.platform,
            "bot_running": bot_pid is not None,
            "pid": bot_pid,
            "dangerous_commands_enabled": config.DANGEROUS_COMMANDS_ENABLED,
            "action_code_ttl": config.ACTION_CODE_TTL,
        }
    )


async def action_code(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except (json.JSONDecodeError, ValueError):
        return web.json_response({"error": "invalid JSON"}, status=400)

    action = str(data.get("action", "")).strip().lower()
    if action not in ACTIONS:
        return web.json_response({"error": "unknown sensitive action"}, status=400)

    sys.path.insert(0, str(ROOT / "app"))
    import security
    import security_log

    try:
        code, expires_at = security.issue_action_code(action)
    except Exception:
        return web.json_response({"error": "failed to generate security code"}, status=500)

    security_log.log_security_event(
        f"One-time action code generated for {action}",
        actor="web-panel",
    )
    return web.json_response(
        {"action": action, "code": code, "expires_at": expires_at}
    )


async def logs(request: web.Request) -> web.Response:
    del request
    path = ROOT / "bot.log"
    lines = (
        path.read_text(encoding="utf-8", errors="replace").splitlines()[-100:]
        if path.exists()
        else []
    )
    return web.json_response({"lines": lines})


def create_app() -> web.Application:
    _load_env()
    app = web.Application(middlewares=[auth])
    app["sessions"] = {}
    app.router.add_get("/", index)
    app.router.add_get("/panel_web", index)
    app.router.add_get("/panel_web/", index)
    for route, directory in (
        ("/panel_web/signin", "signin"),
        ("/panel_web/dashboard", "dashboard"),
        ("/panel_web/instance", "instance"),
        ("/panel_web/activity", "activity_log"),
        ("/panel_web/logs", "logs"),
        ("/panel_web/security", "security"),
    ):
        app.router.add_get(route, lambda request, directory=directory: web.FileResponse(STATIC_DIR / directory / "index.html"))
        app.router.add_get(route + "/", lambda request, directory=directory: web.FileResponse(STATIC_DIR / directory / "index.html"))
    app.router.add_get("/panel_web/{name:app.js|style.css}", asset)
    app.router.add_post("/api/login", login)
    app.router.add_post("/api/logout", logout)
    app.router.add_get("/api/status", status)
    app.router.add_get("/api/logs", logs)
    app.router.add_post("/api/action-code", action_code)
    return app


def main() -> None:
    _load_env()
    host = os.getenv("PANEL_WEB_HOST", "127.0.0.1").strip()
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("PANEL_WEB_HOST must remain localhost.")

    port = int(os.getenv("PANEL_WEB_PORT", "8765"))
    _token()
    print(f"Web panel: http://127.0.0.1:{port}/panel_web/signin")
    web.run_app(create_app(), host=host, port=port, access_log=None)


if __name__ == "__main__":
    main()
