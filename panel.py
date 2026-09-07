"""Cross-platform local control panel for v-bot."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil

import config
import security_log
from deps import install_requirements

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
BOT_PID_FILE = ROOT / "bot.pid"
BOT_START_FILE = ROOT / "bot.start"
SERVERS_FILE = ROOT / "servers.txt"
LOG_FILE = ROOT / "bot.log"
SECURITY_LOG_FILE = ROOT / "security.log"

IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")
PYTHON_EXE = ROOT / ("venv/Scripts/python.exe" if IS_WINDOWS else "venv/bin/python")


def _read_env_lines() -> list[str]:
    try:
        return ENV_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def _write_env_lines(lines: list[str]) -> None:
    content = "\n".join(lines) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=".env.", suffix=".tmp", dir=ROOT, text=True)
    temp_path = Path(temp_name)
    try:
        if not IS_WINDOWS:
            os.chmod(temp_path, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, ENV_PATH)
        temp_path = None
        if not IS_WINDOWS:
            os.chmod(ENV_PATH, 0o600)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def get_env_value(key: str) -> str:
    prefix = f"{key}="
    return next((line[len(prefix):].strip() for line in _read_env_lines() if line.startswith(prefix)), "")


def set_env_value(key: str, value: str) -> None:
    if not key or "=" in key or "\n" in key or "\r" in key or "\n" in value or "\r" in value:
        raise ValueError("Invalid .env key/value")
    lines = _read_env_lines()
    prefix = f"{key}="
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = f"{key}={value}"
            _write_env_lines(lines)
            return
    lines.append(f"{key}={value}")
    _write_env_lines(lines)


def _read_process_metadata() -> dict | None:
    try:
        data = json.loads(BOT_START_FILE.read_text(encoding="utf-8"))
        return {"pid": int(data["pid"]), "create_time": float(data["create_time"]), "started_at": int(data["started_at"])}
    except (OSError, ValueError, TypeError, KeyError):
        return None


def _write_process_metadata(pid: int) -> None:
    process = psutil.Process(pid)
    metadata = {"pid": pid, "create_time": process.create_time(), "started_at": int(time.time())}
    fd, temp_name = tempfile.mkstemp(prefix="bot.start.", suffix=".tmp", dir=ROOT, text=True)
    temp_path = Path(temp_name)
    try:
        if not IS_WINDOWS:
            os.chmod(temp_path, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            json.dump(metadata, file, separators=(",", ":"))
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, BOT_START_FILE)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _clear_pid_files() -> None:
    BOT_PID_FILE.unlink(missing_ok=True)
    BOT_START_FILE.unlink(missing_ok=True)


def _get_bot_pid() -> int | None:
    try:
        pid = int(BOT_PID_FILE.read_text(encoding="utf-8").strip())
        metadata = _read_process_metadata()
        if pid <= 0 or metadata is None or metadata["pid"] != pid:
            raise ValueError
        process = psutil.Process(pid)
        if abs(process.create_time() - metadata["create_time"]) > 1.0 or not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
            raise psutil.NoSuchProcess(pid)
        return pid
    except (OSError, ValueError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        _clear_pid_files()
        return None


def is_running() -> bool:
    return _get_bot_pid() is not None


def _format_duration(seconds: int) -> str:
    days, remainder = divmod(max(0, seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def cmd_status() -> None:
    print("\n=== v-bot status ===")
    print(f"Version: {config.VERSION}")
    print(f"Platform: {'Windows' if IS_WINDOWS else 'macOS' if IS_MACOS else 'Linux' if IS_LINUX else sys.platform}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Environment: {'OK' if ENV_PATH.exists() else 'MISSING'}")
    print(f"Principal owner: {config.OWNER_PRINCIPAL}")
    if config.OWNERS_SECONDARY:
        print(f"Secondary owners ({len(config.OWNERS_SECONDARY)}/{config.MAX_SECONDARY_OWNERS}): {', '.join(map(str, config.OWNERS_SECONDARY))}")
    else:
        print(f"Secondary owners: 0/{config.MAX_SECONDARY_OWNERS}")
    pid = _get_bot_pid()
    if pid is None:
        print("Bot: INACTIVE")
        return
    process = psutil.Process(pid)
    metadata = _read_process_metadata()
    uptime = int(time.time() - metadata["started_at"]) if metadata else int(time.time() - process.create_time())
    print("Bot: ONLINE")
    print(f"PID: {pid}")
    print(f"Process: {process.status()}")
    print(f"Uptime: {_format_duration(uptime)}")
    print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
    print(f"CPU: {process.cpu_percent(interval=0.1):.1f}%")


def cmd_start() -> None:
    if is_running():
        print("The bot is already running.")
        return
    if not PYTHON_EXE.exists():
        print(f"[ERROR] Virtual environment not found: {PYTHON_EXE}")
        return
    main_file = ROOT / "main.py"
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    try:
        if IS_WINDOWS:
            process = subprocess.Popen([str(PYTHON_EXE), str(main_file)], cwd=ROOT, creationflags=subprocess.CREATE_NEW_CONSOLE, env=env)
        else:
            process = subprocess.Popen([str(PYTHON_EXE), str(main_file)], cwd=ROOT, start_new_session=True, env=env)
        _write_process_metadata(process.pid)
        BOT_PID_FILE.write_text(str(process.pid), encoding="utf-8")
    except (OSError, psutil.Error) as exc:
        print(f"[ERROR] Failed to start the bot: {exc}")
        return
    time.sleep(2)
    print(f"Bot {'started' if is_running() else 'failed to start'}.")


def cmd_stop() -> None:
    pid = _get_bot_pid()
    if pid is None:
        print("The bot is not running.")
        return
    try:
        process = psutil.Process(pid)
        for child in process.children(recursive=True):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        process.kill()
    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        pass
    except psutil.Error as exc:
        print(f"[ERROR] Failed to stop the bot: {exc}")
        return
    _clear_pid_files()
    print("Bot stopped.")


def cmd_restart() -> None:
    cmd_stop()
    time.sleep(2)
    cmd_start()


def cmd_uptime() -> None:
    metadata = _read_process_metadata()
    if metadata is None or not is_running():
        print("Uptime unknown: bot inactive.")
        return
    print(f"Uptime: {_format_duration(int(time.time() - metadata['started_at']))}")


def cmd_update() -> None:
    try:
        install_requirements(upgrade=True)
        print("Update complete.")
    except Exception as exc:
        print(f"[ERROR] Failed to update dependencies: {exc}")


def _display_log_file(file_path: Path, title: str, lines_count: int) -> None:
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        print(f"{file_path.name} does not exist yet.")
        return
    print(f"\n--- {title} (last {min(lines_count, len(lines))}) ---")
    print("\n".join(lines[-lines_count:]) or "(empty)")


def cmd_logs() -> None:
    _display_log_file(LOG_FILE, "bot.log", 50)


def cmd_security_logs() -> None:
    _display_log_file(SECURITY_LOG_FILE, "security.log", 30)


def cmd_servers() -> None:
    try:
        print(SERVERS_FILE.read_text(encoding="utf-8"))
    except OSError:
        print("Server list unavailable.")


def cmd_add_secondary_owner() -> None:
    current = [x.strip() for x in get_env_value("OWNERS_SECONDARY_IDS").split(",") if x.strip()]
    if len(current) >= config.MAX_SECONDARY_OWNERS:
        print(f"[ERROR] Maximum of {config.MAX_SECONDARY_OWNERS} secondary owners reached.")
        return
    new_id = input("Discord ID of the new secondary owner: ").strip()
    if not new_id.isdigit() or int(new_id) <= 0:
        print("[ERROR] Invalid Discord ID.")
        return
    if int(new_id) == config.OWNER_PRINCIPAL or new_id in current:
        print("[ERROR] This ID is already an owner.")
        return
    current.append(new_id)
    set_env_value("OWNERS_SECONDARY_IDS", ",".join(current))
    security_log.log_security_event("Permanent secondary owner added", actor="panel")
    print(f"Secondary owner added ({len(current)}/{config.MAX_SECONDARY_OWNERS}). Restart required.")


def cmd_set_token() -> None:
    value = input("New Discord token: ").strip()
    if value:
        set_env_value("DISCORD_TOKEN", value)
        security_log.log_security_event("Discord token changed", actor="panel")
        print("Token saved. Restart required.")


def cmd_set_principal_owner() -> None:
    value = input("Discord ID of principal owner: ").strip()
    if value.isdigit() and int(value) > 0:
        set_env_value("OWNER_PRINCIPAL_ID", value)
        print("Principal owner saved. Restart required.")
    else:
        print("[ERROR] Invalid Discord ID.")


def _dangerous_commands_enabled() -> bool:
    return get_env_value("DANGEROUS_COMMANDS_ENABLED").lower() in {"1", "true", "on", "yes"}


def cmd_toggle_dangerous() -> None:
    enabled = _dangerous_commands_enabled()
    if enabled:
        set_env_value("DANGEROUS_COMMANDS_ENABLED", "false")
        print("Sensitive commands disabled. Restart required.")
        return
    if input("Type ENABLE to confirm: ").strip() == "ENABLE":
        set_env_value("DANGEROUS_COMMANDS_ENABLED", "true")
        print("Sensitive commands enabled. Restart required.")
    else:
        print("Cancelled.")


def cmd_set_prefix() -> None:
    value = input("New prefix: ").strip()
    if value and len(value) <= 10 and not any(char.isspace() for char in value):
        set_env_value("BOT_PREFIX", value)
        print("Prefix saved. Restart required.")
    else:
        print("[ERROR] Invalid prefix.")


def cmd_set_twitch_api() -> None:
    client_id = input("Twitch Client ID: ").strip()
    client_secret = input("Twitch Client Secret: ").strip()
    if client_id and client_secret:
        set_env_value("TWITCH_CLIENT_ID", client_id)
        set_env_value("TWITCH_CLIENT_SECRET", client_secret)
        security_log.log_security_event("Twitch API credentials changed", actor="panel")
        print("Twitch credentials saved. Automatic reload enabled.")


def cmd_set_youtube_api() -> None:
    value = input("YouTube API Key: ").strip()
    if value:
        set_env_value("YOUTUBE_API_KEY", value)
        security_log.log_security_event("YouTube API key changed", actor="panel")
        print("YouTube key saved. Automatic reload enabled.")


COMMANDS = [
    ("start", "start the bot", cmd_start),
    ("stop", "stop the bot", cmd_stop),
    ("restart", "restart the bot", cmd_restart),
    ("status", "detailed status, uptime, resources and owners", cmd_status),
    ("uptime", "display bot uptime", cmd_uptime),
    ("update", "update dependencies", cmd_update),
    ("logs", "display recent bot logs", cmd_logs),
    ("security_logs", "display recent security logs", cmd_security_logs),
    ("servers", "list connected servers", cmd_servers),
    ("add_secondary_owner", "add a secondary owner (max 5)", cmd_add_secondary_owner),
    ("set_token", "set Discord token", cmd_set_token),
    ("set_principal_owner", "set principal owner", cmd_set_principal_owner),
    ("toggle_dangerous", "enable/disable sensitive commands", cmd_toggle_dangerous),
    ("set_prefix", "set bot prefix", cmd_set_prefix),
    ("set_twitch_api", "configure main Twitch API", cmd_set_twitch_api),
    ("set_youtube_api", "configure main YouTube API", cmd_set_youtube_api),
]
COMMAND_MAP = {name: func for name, _, func in COMMANDS}


def cmd_help() -> None:
    print("\n===== v-bot Control Panel =====")
    width = max(len(name) for name, _, _ in COMMANDS) + 2
    for name, description, _ in COMMANDS:
        print(f"{name.ljust(width)}- {description}")
    print(f"{'help'.ljust(width)}- display this list")
    print(f"{'exit'.ljust(width)}- close panel")


def check_principal_owner() -> None:
    if not get_env_value("OWNER_PRINCIPAL_ID"):
        cmd_set_principal_owner()


def check_token() -> None:
    if not get_env_value("DISCORD_TOKEN"):
        cmd_set_token()


def main() -> None:
    print("===================================\n          v-bot Control Panel\n===================================")
    print(f"Version: {config.VERSION}")
    print(f"Platform: {'Windows' if IS_WINDOWS else 'macOS' if IS_MACOS else 'Linux' if IS_LINUX else sys.platform}")
    if ENV_PATH.exists():
        check_principal_owner()
        check_token()
    else:
        print("[WARNING] .env file not found.")
    cmd_status()
    print('Type "help" for the list of panel commands.')
    while True:
        try:
            cmd = input("\nv-bot> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if cmd == "exit":
            break
        if cmd == "help":
            cmd_help()
        elif cmd in COMMAND_MAP:
            try:
                COMMAND_MAP[cmd]()
            except Exception as exc:
                print(f"[ERROR] Command failed: {exc}")
        elif cmd:
            print(f'Unknown command "{cmd}". Type "help" for the list.')


if __name__ == "__main__":
    main()
