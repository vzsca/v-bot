"""Local-only aiohttp control panel for v-bot."""

from __future__ import annotations

import asyncio
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
    expires_at = request.app["sessions"].get(session)
    if not session or expires_at is None:
        return False
    if expires_at <= time.time():
        request.app["sessions"].pop(session, None)
        return False
    return True


@web.middleware
async def auth(request: web.Request, handler):
    public_paths = {
        "/", "/panel_web", "/panel_web/", "/panel_web/signin", "/panel_web/signin/",
        "/panel_web/app.js", "/panel_web/style.css", "/api/login",
    }
    page_paths = {
        "/panel_web/dashboard", "/panel_web/dashboard/",
        "/panel_web/instance", "/panel_web/instance/",
        "/panel_web/activity", "/panel_web/activity/",
        "/panel_web/logs", "/panel_web/logs/",
        "/panel_web/security", "/panel_web/security/",
        "/panel_web/manege", "/panel_web/manege/",
        "/panel_web/settings", "/panel_web/settings/",
    }
    if request.path in public_paths:
        if request.path in {"/panel_web/signin", "/panel_web/signin/"} and _authorized(request):
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
        SESSION_COOKIE, session, httponly=True, samesite="Strict",
        max_age=SESSION_TTL, path="/",
    )
    return response


async def logout(request: web.Request) -> web.Response:
    request.app["sessions"].pop(request.cookies.get(SESSION_COOKIE, ""), None)
    response = web.json_response({"ok": True})
    response.del_cookie(SESSION_COOKIE, path="/")
    return response


def _bot(app: web.Application):
    return app["bot"]


def _bot_uptime(app: web.Application) -> int:
    started = app.get("bot_started_at")
    return max(0, int(time.time() - started)) if started else 0


def _running(app: web.Application) -> bool:
    bot = _bot(app)
    return bool(bot.is_ready() and not bot.is_closed())


async def _run_bot(app: web.Application) -> None:
    bot = _bot(app)
    try:
        await bot.start(app["config"].TOKEN)
    except asyncio.CancelledError:
        raise
    except Exception:
        app["bot_error"] = "Bot stopped unexpectedly. Check logs."
    finally:
        app["bot_task"] = None


async def _ensure_bot_started(app: web.Application) -> None:
    if app.get("bot_task") and not app["bot_task"].done():
        return
    app["bot_error"] = None
    app["bot_started_at"] = time.time()
    app["bot_task"] = asyncio.create_task(_run_bot(app))
    await asyncio.sleep(0.15)


async def _stop_bot(app: web.Application) -> None:
    bot = _bot(app)
    if not bot.is_closed():
        await bot.close()
    task = app.get("bot_task")
    if task and not task.done():
        try:
            await asyncio.wait_for(task, timeout=5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            task.cancel()
    app["bot_task"] = None
    app["bot_started_at"] = None


async def control(request: web.Request) -> web.Response:
    action = str((await request.json()).get("action", "")).strip().lower()
    if action == "start":
        await _ensure_bot_started(request.app)
    elif action == "stop":
        await _stop_bot(request.app)
    elif action == "restart":
        await _stop_bot(request.app)
        await asyncio.sleep(0.5)
        await _ensure_bot_started(request.app)
    else:
        return web.json_response({"error": "unknown control action"}, status=400)
    return await status(request)


async def status(request: web.Request) -> web.Response:
    app = request.app
    bot = _bot(app)
    process = psutil.Process(os.getpid())
    version = app["version"]
    platform = sys.platform
    cpu = 0.0
    memory = 0.0
    try:
        cpu = process.cpu_percent(interval=None)
        memory = process.memory_info().rss / (1024 * 1024)
    except psutil.Error:
        pass
    return web.json_response(
        {
            "version": version,
            "platform": platform,
            "bot_running": _running(app),
            "pid": os.getpid(),
            "process_status": process.status() if process.is_running() else "stopped",
            "uptime": _bot_uptime(app),
            "cpu": round(cpu, 1),
            "ram_mb": round(memory, 1),
            "guild_count": len(bot.guilds),
            "dangerous_commands_enabled": app["config"].DANGEROUS_COMMANDS_ENABLED,
            "action_code_ttl": app["config"].ACTION_CODE_TTL,
            "bot_error": app.get("bot_error"),
        }
    )


async def logs(request: web.Request) -> web.Response:
    del request
    path = ROOT / "bot.log"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-200:] if path.exists() else []
    return web.json_response({"lines": lines})


async def security_logs(request: web.Request) -> web.Response:
    del request
    path = ROOT / "security.log"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-100:] if path.exists() else []
    return web.json_response({"lines": lines})


async def action_code(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except (json.JSONDecodeError, ValueError):
        return web.json_response({"error": "invalid JSON"}, status=400)
    action = str(data.get("action", "")).strip().lower()
    if action not in ACTIONS:
        return web.json_response({"error": "unknown sensitive action"}, status=400)
    from app import security, security_log
    try:
        code, expires_at = security.issue_action_code(action)
    except Exception:
        return web.json_response({"error": "failed to generate security code"}, status=500)
    security_log.log_security_event(f"One-time action code generated for {action}", actor="web-panel")
    return web.json_response({"action": action, "code": code, "expires_at": expires_at})


def _env_value(key: str) -> str:
    from dotenv import dotenv_values
    values = dotenv_values(ROOT / ".env")
    return str(values.get(key) or "")


def _set_env_value(key: str, value: str) -> None:
    from panel_web.env_tools import set_env_value
    set_env_value(key, value)


async def config_get(request: web.Request) -> web.Response:
    del request
    from app import api_access
    secondary = [x.strip() for x in _env_value("OWNERS_SECONDARY_IDS").split(",") if x.strip()]
    return web.json_response(
        {
            "principal_owner": _env_value("OWNER_PRINCIPAL_ID"),
            "secondary_owners": secondary,
            "dangerous_commands_enabled": _env_value("DANGEROUS_COMMANDS_ENABLED").lower() in {"1", "true", "yes", "on"},
            "prefix": _env_value("BOT_PREFIX"),
            "twitch_configured": bool(_env_value("TWITCH_CLIENT_ID") and _env_value("TWITCH_CLIENT_SECRET")),
            "youtube_configured": bool(_env_value("YOUTUBE_API_KEY")),
            "api_allowed_guilds": len(api_access.get_allowed_guilds()),
            "token_configured": bool(_env_value("DISCORD_TOKEN")),
        }
    )


async def config_update(request: web.Request) -> web.Response:
    data = await request.json()
    from app import security_log
    allowed = {
        "OWNER_PRINCIPAL_ID", "OWNERS_SECONDARY_IDS", "DANGEROUS_COMMANDS_ENABLED",
        "BOT_PREFIX", "DISCORD_TOKEN", "TWITCH_CLIENT_ID", "TWITCH_CLIENT_SECRET",
        "YOUTUBE_API_KEY",
    }
    for key, value in data.items():
        if key not in allowed:
            continue
        if key == "OWNERS_SECONDARY_IDS" and isinstance(value, list):
            value = ",".join(str(x).strip() for x in value if str(x).strip())
        value = str(value).strip()
        if key == "DANGEROUS_COMMANDS_ENABLED":
            value = "true" if value.lower() in {"1", "true", "yes", "on"} else "false"
        _set_env_value(key, value)
    security_log.log_security_event("Configuration changed through web panel", actor="web-panel")
    return await config_get(request)


async def servers(request: web.Request) -> web.Response:
    bot = _bot(request.app)
    result = []
    for guild in sorted(bot.guilds, key=lambda g: g.name.casefold()):
        result.append(
            {
                "id": guild.id,
                "name": guild.name,
                "owner_id": guild.owner_id,
                "owner": str(guild.owner) if guild.owner else None,
                "members": guild.member_count,
                "joined_at": guild.me.joined_at.isoformat() if guild.me and guild.me.joined_at else None,
                "api_allowed": _api_allowed(guild.id),
            }
        )
    return web.json_response({"servers": result, "count": len(result)})


def _api_allowed(guild_id: int) -> bool:
    from app import api_access
    return api_access.is_allowed(guild_id)


async def server_details(request: web.Request) -> web.Response:
    guild_id = int(request.match_info["guild_id"])
    guild = _bot(request.app).get_guild(guild_id)
    if guild is None:
        return web.json_response({"error": "server not found"}, status=404)
    return web.json_response(
        {
            "id": guild.id,
            "name": guild.name,
            "owner_id": guild.owner_id,
            "owner": str(guild.owner) if guild.owner else None,
            "members": guild.member_count,
            "joined_at": guild.me.joined_at.isoformat() if guild.me and guild.me.joined_at else None,
            "api_allowed": _api_allowed(guild.id),
        }
    )


async def server_action(request: web.Request) -> web.Response:
    guild_id = int(request.match_info["guild_id"])
    guild = _bot(request.app).get_guild(guild_id)
    if guild is None:
        return web.json_response({"error": "server not found"}, status=404)
    data = await request.json()
    action = str(data.get("action", "")).strip().lower()
    from app import api_access, security_log
    if action == "api_access":
        allowed = bool(data.get("enabled"))
        if not api_access.set_allowed(guild_id, allowed):
            return web.json_response({"error": "unable to update API access"}, status=500)
        security_log.log_security_event(
            f"API configuration {'enabled' if allowed else 'disabled'} for guild {guild_id}",
            actor="web-panel",
        )
        return web.json_response({"ok": True, "api_allowed": allowed})
    if action == "invite":
        me = guild.me
        if me is None:
            return web.json_response({"error": "bot member not found"}, status=400)
        for channel in guild.text_channels:
            if channel.permissions_for(me).create_instant_invite:
                try:
                    invite = await channel.create_invite(max_age=3600, max_uses=1)
                    return web.json_response({"ok": True, "url": invite.url})
                except Exception:
                    continue
        return web.json_response({"error": "unable to create an invite"}, status=403)
    if action == "leave":
        name = guild.name
        try:
            await guild.leave()
        except Exception:
            return web.json_response({"error": "unable to leave server"}, status=502)
        security_log.log_security_event(f"Bot left guild {name} ({guild_id})", actor="web-panel")
        return web.json_response({"ok": True})
    return web.json_response({"error": "unknown server action"}, status=400)


async def on_startup(app: web.Application) -> None:
    await _ensure_bot_started(app)


async def on_cleanup(app: web.Application) -> None:
    await _stop_bot(app)


def create_app() -> web.Application:
    _load_env()
    from app import config
    from extensions import get_extensions, is_dangerous_extension
    import main as bot_main

    app = web.Application(middlewares=[auth])
    app["sessions"] = {}
    app["config"] = config
    app["version"] = bot_main.VERSION if hasattr(bot_main, "VERSION") else __import__("version").VERSION
    app["bot"] = bot_main.bot
    app["extensions_loaded"] = False

    async def prepare_bot(application: web.Application) -> None:
        if application["extensions_loaded"]:
            return
        for extension in get_extensions(config.DANGEROUS_COMMANDS_ENABLED):
            await application["bot"].load_extension(extension)
        application["extensions_loaded"] = True
        application["is_dangerous_extension"] = is_dangerous_extension

    async def start(application: web.Application) -> None:
        await prepare_bot(application)
        await on_startup(application)

    app.on_startup.append(start)
    app.on_cleanup.append(on_cleanup)

    app.router.add_get("/", index)
    app.router.add_get("/panel_web", index)
    app.router.add_get("/panel_web/", index)
    for route, directory in (
        ("/panel_web/signin", "signin"),
        ("/panel_web/dashboard", "dashboard"),
        ("/panel_web/instance", "instance"),
        ("/panel_web/activity", "activity"),
        ("/panel_web/logs", "logs"),
        ("/panel_web/security", "security"),
        ("/panel_web/manege", "manege"),
        ("/panel_web/settings", "settings"),
    ):
        app.router.add_get(route, lambda request, directory=directory: web.FileResponse(STATIC_DIR / directory / "index.html"))
        app.router.add_get(route + "/", lambda request, directory=directory: web.FileResponse(STATIC_DIR / directory / "index.html"))
    app.router.add_get("/panel_web/{name:app.js|style.css}", asset)
    app.router.add_post("/api/login", login)
    app.router.add_post("/api/logout", logout)
    app.router.add_get("/api/status", status)
    app.router.add_get("/api/logs", logs)
    app.router.add_get("/api/security-logs", security_logs)
    app.router.add_post("/api/action-code", action_code)
    app.router.add_get("/api/config", config_get)
    app.router.add_post("/api/config", config_update)
    app.router.add_post("/api/control", control)
    app.router.add_get("/api/servers", servers)
    app.router.add_get("/api/servers/{guild_id}", server_details)
    app.router.add_post("/api/servers/{guild_id}/action", server_action)
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
