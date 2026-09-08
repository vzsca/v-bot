"""Interactive cross-platform control panel for v-bot."""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import security_log
from security import issue_action_code
from version import VERSION

ENV_PATH = ROOT / ".env"
BOT_PID_FILE = ROOT / "bot.pid"
BOT_START_FILE = ROOT / "bot.start"
SERVERS_FILE = ROOT / "servers.txt"
LOG_FILE = ROOT / "bot.log"
SECURITY_LOG_FILE = ROOT / "security.log"

IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

if IS_WINDOWS:
    PYTHON_EXE = ROOT / "venv" / "Scripts" / "python.exe"
else:
    PYTHON_EXE = ROOT / "venv" / "bin" / "python"


def _read_env_lines() -> list[str]:
    if not ENV_PATH.exists():
        return []
    return ENV_PATH.read_text(encoding="utf-8").splitlines()


def _write_env_lines(lines: list[str]) -> None:
    """Atomically replace .env without exposing a partial file."""
    content = "\n".join(lines) + "\n"
    temp_path: Path | None = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix=".env.", suffix=".tmp", dir=ROOT, text=True)
        temp_path = Path(temp_name)
        if not IS_WINDOWS:
            try:
                os.chmod(temp_path, 0o600)
            except OSError:
                pass
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, ENV_PATH)
        temp_path = None
        if not IS_WINDOWS:
            try:
                os.chmod(ENV_PATH, 0o600)
            except OSError:
                pass
    except OSError as exc:
        raise OSError(f"Unable to atomically write .env: {exc}") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def get_env_value(key: str) -> str:
    prefix = f"{key}="
    for line in _read_env_lines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def set_env_value(key: str, value: str) -> None:
    if not key or "=" in key or "\n" in key or "\r" in key:
        raise ValueError("Invalid .env key.")
    if "\n" in value or "\r" in value:
        raise ValueError(".env values cannot contain newlines.")
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
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        return {
            "pid": int(data["pid"]),
            "create_time": float(data["create_time"]),
            "started_at": int(data.get("started_at", data["create_time"])),
        }
    except (KeyError, TypeError, ValueError):
        return None


def _write_process_metadata(pid: int) -> None:
    process = psutil.Process(pid)
    metadata = {"pid": pid, "create_time": process.create_time(), "started_at": int(time.time())}
    temp_path: Path | None = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix="bot.start.", suffix=".tmp", dir=ROOT, text=True)
        temp_path = Path(temp_name)
        if not IS_WINDOWS:
            try:
                os.chmod(temp_path, 0o600)
            except OSError:
                pass
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            json.dump(metadata, file, separators=(",", ":"))
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, BOT_START_FILE)
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def _clear_pid_files() -> None:
    BOT_PID_FILE.unlink(missing_ok=True)
    BOT_START_FILE.unlink(missing_ok=True)


def _get_bot_pid() -> int | None:
    if not BOT_PID_FILE.exists():
        return None
    try:
        pid = int(BOT_PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None
    if pid <= 0:
        _clear_pid_files()
        return None
    try:
        process = psutil.Process(pid)
        metadata = _read_process_metadata()
        if metadata is None or metadata["pid"] != pid:
            _clear_pid_files()
            return None
        if abs(process.create_time() - metadata["create_time"]) > 1.0:
            _clear_pid_files()
            return None
        if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
            _clear_pid_files()
            return None
        return pid
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        _clear_pid_files()
        return None


def is_running() -> bool:
    return _get_bot_pid() is not None


def _format_uptime(seconds: int) -> str:
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


def _owner_status() -> tuple[str, list[str]]:
    principal = get_env_value("OWNER_PRINCIPAL_ID") or "not configured"
    secondary = [value.strip() for value in get_env_value("OWNERS_SECONDARY_IDS").split(",") if value.strip()]
    return principal, secondary


def cmd_start() -> bool:
    if is_running():
        print("The bot is already running.")
        return True
    if not PYTHON_EXE.exists():
        print("[ERROR] Python virtual environment not found.")
        print(f"Expected Python executable: {PYTHON_EXE}")
        print("Run the initial setup first.")
        return False
    main_file = ROOT / "main.py"
    if not main_file.exists():
        print("[ERROR] main.py was not found.")
        return False
    print("Starting bot...")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    command = [str(PYTHON_EXE), str(main_file)]
    try:
        if IS_WINDOWS:
            process = subprocess.Popen(command, cwd=str(ROOT), creationflags=subprocess.CREATE_NEW_CONSOLE, env=env)
        else:
            process = subprocess.Popen(command, cwd=str(ROOT), env=env, start_new_session=True)
        _write_process_metadata(process.pid)
        BOT_PID_FILE.write_text(str(process.pid), encoding="utf-8")
    except (OSError, psutil.Error) as exc:
        print(f"[ERROR] Failed to start the bot: {exc}")
        return False
    time.sleep(2)
    if is_running():
        print("Bot started.")
        print(f"PID: {process.pid}")
        return True
    print('Failed to start the bot. Type "logs" to see why.')
    return False


def cmd_stop() -> bool:
    pid = _get_bot_pid()
    if pid is None:
        print("The bot is not running.")
        return True
    try:
        proc = psutil.Process(pid)
        for child in proc.children(recursive=True):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        try:
            proc.kill()
        except psutil.NoSuchProcess:
            pass
    except psutil.NoSuchProcess:
        pass
    except psutil.Error as exc:
        print(f"[ERROR] Failed to stop the bot: {exc}")
        return False
    _clear_pid_files()
    print("Bot stopped.")
    return True


def cmd_restart() -> bool:
    print("Restarting bot...")
    if not cmd_stop():
        return False
    time.sleep(2)
    return cmd_start()


def cmd_status() -> None:
    principal, secondary = _owner_status()
    print("\n===== v-bot status =====")
    print("Version:", VERSION)
    print("Platform:", "Windows" if IS_WINDOWS else "macOS" if IS_MACOS else "Linux" if IS_LINUX else sys.platform)
    print("Python:", PYTHON_EXE)
    print("Principal owner:", principal)
    print("Secondary owners:", ", ".join(secondary) if secondary else "none")
    print("Secondary owner count:", f"{len(secondary)}/5")
    print("Dangerous commands:", "enabled" if get_env_value("DANGEROUS_COMMANDS_ENABLED").lower() in {"1", "true", "yes", "on"} else "disabled")
    print(".env:", "present" if ENV_PATH.exists() else "missing")
    commit = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
    except OSError:
        pass
    print("Current commit:", commit[:12] if commit else "unavailable")

    pid = _get_bot_pid()
    if pid is None:
        print("State: INACTIVE")
        print("Uptime: not running")
        return
    try:
        process = psutil.Process(pid)
        metadata = _read_process_metadata() or {}
        uptime = max(0, int(time.time() - float(metadata.get("started_at", process.create_time()))))
        memory = process.memory_info().rss / (1024 * 1024)
        print("State: ACTIVE")
        print("PID:", pid)
        print("Process:", process.status())
        print("Uptime:", _format_uptime(uptime))
        print(f"CPU: {process.cpu_percent(interval=0.1):.1f}%")
        print(f"RAM: {memory:.1f} MB")
    except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
        print(f"State: unavailable ({exc})")


def cmd_uptime() -> None:
    metadata = _read_process_metadata()
    if metadata is None:
        print("Uptime unknown.")
        return
    print(f"The bot has been running for {_format_uptime(int(time.time() - metadata.get('started_at', time.time())))}.")


def _display_log_file(file_path: Path, title: str, lines_count: int = 50) -> None:
    if not file_path.exists():
        print(f"{file_path.name} does not exist yet.")
        return
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        print(f"[ERROR] Unable to read {file_path.name}: {exc}")
        return
    last_lines = lines[-lines_count:]
    print()
    print(f"--- {title} (last {len(last_lines)} entries out of {len(lines)}) ---")
    for line in last_lines:
        print(line)


def cmd_logs() -> None:
    _display_log_file(LOG_FILE, "bot.log")


def cmd_security_logs() -> None:
    _display_log_file(SECURITY_LOG_FILE, "security.log", 30)


def cmd_servers() -> None:
    if not SERVERS_FILE.exists():
        print("List unavailable: the bot has not finished connecting yet.")
        return
    print(SERVERS_FILE.read_text(encoding="utf-8"))


def cmd_add_secondary_owner() -> None:
    new_id = input("Discord ID of the new secondary owner: ").strip()
    if not new_id or not new_id.isdigit():
        print("[ERROR] The ID must contain digits only.")
        return
    principal, existing = _owner_status()
    if new_id == principal:
        print("[ERROR] The principal owner cannot also be a secondary owner.")
        return
    if new_id in existing:
        print("This ID is already a secondary owner in .env.")
        return
    if len(existing) >= 5:
        print("[ERROR] Maximum of 5 secondary owners reached.")
        return
    existing.append(new_id)
    set_env_value("OWNERS_SECONDARY_IDS", ",".join(existing))
    security_log.log_security_event(f"Permanent secondary owner added: {new_id}", actor="panel")
    print(f"Secondary owner {new_id} added to .env.")
    print("The change will take effect when the bot is (re)started.")


def cmd_set_token() -> None:
    new_token = input("New Discord token: ").strip()
    if new_token:
        set_env_value("DISCORD_TOKEN", new_token)
        security_log.log_security_event("Discord token changed", actor="panel")
        print("Token saved to .env.")


def cmd_set_principal_owner() -> None:
    new_id = input("Enter the Discord ID of the principal owner: ").strip()
    if not new_id or not new_id.isdigit():
        print("[ERROR] The ID must contain digits only.")
        return
    secondary = [value.strip() for value in get_env_value("OWNERS_SECONDARY_IDS").split(",") if value.strip()]
    if new_id in secondary:
        print("[ERROR] This ID is already a secondary owner. Remove it first.")
        return
    set_env_value("OWNER_PRINCIPAL_ID", new_id)
    security_log.log_security_event(f"Principal owner set: {new_id}", actor="panel")
    print("Principal owner saved to .env.")


def _dangerous_commands_enabled() -> bool:
    return get_env_value("DANGEROUS_COMMANDS_ENABLED").strip().lower() in {"1", "true", "on", "yes"}


def cmd_toggle_dangerous() -> None:
    value = "false" if _dangerous_commands_enabled() else "true"
    if value == "true" and input("Type ENABLE to confirm: ").strip() != "ENABLE":
        print("Cancelled.")
        return
    set_env_value("DANGEROUS_COMMANDS_ENABLED", value)
    security_log.log_security_event(f"Sensitive commands {'ENABLED' if value == 'true' else 'DISABLED'}", actor="panel")
    print(f"Sensitive commands {'ENABLED' if value == 'true' else 'DISABLED'}. Restart required.")


def cmd_action_code() -> None:
    try:
        code, expires_at = issue_action_code()
    except Exception as exc:
        print(f"[ERROR] Failed to generate action code: {exc}")
        return
    remaining = max(0, expires_at - int(time.time()))
    security_log.log_security_event("One-time sensitive action code generated", actor="panel")
    print("\n===== sensitive action code =====")
    print(f"Code: {code}")
    print(f"Valid for approximately {remaining} seconds.")
    print("The code is one-time use. Do not share it.")


def cmd_set_prefix() -> None:
    value = input("New prefix: ").strip()
    if not value or len(value) > 10 or any(char.isspace() for char in value):
        print("[ERROR] Invalid prefix.")
        return
    set_env_value("BOT_PREFIX", value)
    print(f"Prefix saved: {value}. Restart required.")


def cmd_set_twitch_api() -> None:
    client_id = input("Twitch Client ID: ").strip()
    client_secret = input("Twitch Client Secret: ").strip()
    if not client_id or not client_secret:
        print("[ERROR] Both values are required.")
        return
    set_env_value("TWITCH_CLIENT_ID", client_id)
    set_env_value("TWITCH_CLIENT_SECRET", client_secret)
    security_log.log_security_event("Twitch API credentials changed", actor="panel")
    print("Twitch API credentials saved to .env.")


def cmd_set_youtube_api() -> None:
    api_key = input("YouTube API Key: ").strip()
    if not api_key:
        print("[ERROR] API key required.")
        return
    set_env_value("YOUTUBE_API_KEY", api_key)
    security_log.log_security_event("YouTube API key changed", actor="panel")
    print("YouTube API key saved to .env.")


COMMANDS = [
    ("start", "start the bot", cmd_start),
    ("stop", "stop the bot", cmd_stop),
    ("restart", "restart the bot", cmd_restart),
    ("status", "full bot/process status", cmd_status),
    ("uptime", "show bot uptime", cmd_uptime),
    ("logs", "display bot.log", cmd_logs),
    ("security_logs", "display security.log", cmd_security_logs),
    ("servers", "list connected servers", cmd_servers),
    ("add_secondary_owner", "add a secondary owner (max 5)", cmd_add_secondary_owner),
    ("set_token", "set Discord token", cmd_set_token),
    ("set_principal_owner", "set principal owner", cmd_set_principal_owner),
    ("toggle_dangerous", "enable/disable sensitive commands", cmd_toggle_dangerous),
    ("action_code", "generate a one-time code for a sensitive command", cmd_action_code),
    ("set_prefix", "set bot prefix", cmd_set_prefix),
    ("set_twitch_api", "set main Twitch API", cmd_set_twitch_api),
    ("set_youtube_api", "set main YouTube API", cmd_set_youtube_api),
]
COMMAND_MAP = {name: func for name, _, func in COMMANDS}


def cmd_help() -> None:
    print("\n===== v-bot =====")
    width = max(len(name) for name, _, _ in COMMANDS) + 2
    for name, desc, _ in COMMANDS:
        print(f"{name.ljust(width)}- {desc}")
    print(f"{'help'.ljust(width)}- display this list again")
    print(f"{'exit'.ljust(width)}- close this panel")


def check_principal_owner() -> None:
    if not get_env_value("OWNER_PRINCIPAL_ID"):
        print("No principal owner is defined in .env.")
        cmd_set_principal_owner()


def check_token() -> None:
    if not get_env_value("DISCORD_TOKEN"):
        print("No Discord token is defined in .env.")
        cmd_set_token()


def main() -> None:
    print("===================================")
    print("          v-bot Control Panel")
    print("===================================")
    print(f"Version: {VERSION}")
    print(f"Platform: {'Windows' if IS_WINDOWS else 'macOS' if IS_MACOS else 'Linux' if IS_LINUX else sys.platform}")
    print(f"Python: {PYTHON_EXE}")
    if not ENV_PATH.exists():
        print("[WARNING] .env file not found. The bot will fail to start.")
    else:
        check_principal_owner()
        check_token()
    print('Type "help" for the list of panel commands.')
    while True:
        try:
            cmd = input("v-bot> ").strip().lower()
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
