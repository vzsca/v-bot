"""
Interactive cross-platform control panel for v-bot.

Compatible with Windows, Linux and macOS.
"""

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
from deps import install_requirements
from updater import current_commit, repository_status, requirements_changed, rollback_code, update_code
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
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = f"{key}={value}"
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
        return {"pid": int(data["pid"]), "create_time": float(data["create_time"]), "started_at": int(data.get("started_at", data["create_time"]))}
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


def _clear_pid_files() -> None:
    BOT_PID_FILE.unlink(missing_ok=True)
    BOT_START_FILE.unlink(missing_ok=True)


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
    secondary = [x.strip() for x in get_env_value("OWNERS_SECONDARY_IDS").split(",") if x.strip()]
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
    bot_name = get_env_value("BOT_NAME") or "not configured"
    print("\n===== v-bot status =====")
    print("Bot:", bot_name)
    print("Version:", VERSION)
    print("Platform:", "Windows" if IS_WINDOWS else "macOS" if IS_MACOS else "Linux" if IS_LINUX else sys.platform)
    print("Python:", PYTHON_EXE)
    print("Principal owner:", principal)
    print("Secondary owners:", ", ".join(secondary) if secondary else "none")
    print("Secondary owner count:", f"{len(secondary)}/5")
    print("Dangerous commands:", "enabled" if get_env_value("DANGEROUS_COMMANDS_ENABLED").lower() in {"1", "true", "yes", "on"} else "disabled")
    print(".env:", "present" if ENV_PATH.exists() else "missing")

    repo_ok, behind, ahead, repo_message = repository_status(fetch=True)
    if repo_ok:
        if behind:
            print(f"Repository: UPDATE AVAILABLE ({behind} commit(s))")
        elif ahead:
            print(f"Repository: local branch ahead by {ahead} commit(s)")
        else:
            print("Repository: up to date")
    else:
        print(f"Repository: unavailable ({repo_message})")
    commit = current_commit()
    if commit:
        print("Current commit:", commit[:12])

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


def cmd_update() -> bool:
    print("\n===== v-bot updater =====")
    repo_ok, behind, ahead, message = repository_status(fetch=True)
    if not repo_ok:
        print(f"[ERROR] {message}")
        return False
    if behind == 0:
        print("No update available; the bot was not stopped.")
        return True
    if ahead:
        print("[ERROR] Local branch has commits not present on origin/main; update aborted.")
        return False

    old_commit = current_commit()
    was_running = is_running()
    if was_running and not cmd_stop():
        return False
    time.sleep(1)

    ok, changed, update_message = update_code()
    print(update_message)
    if not ok:
        if was_running:
            cmd_start()
        return False

    new_commit = current_commit()
    if changed and requirements_changed(old_commit, new_commit):
        print("requirements.txt changed; synchronizing dependencies...")
        if not install_requirements(upgrade=False):
            print("[ERROR] Dependency update failed; rolling back source code.")
            rollback_ok, rollback_message = rollback_code(old_commit)
            print(rollback_message)
            if rollback_ok:
                install_requirements(upgrade=False)
            if was_running:
                cmd_start()
            return False
    elif changed:
        print("No dependency changes detected; existing virtual environment kept.")

    if was_running:
        print("Starting the updated bot...")
        if not cmd_start():
            print("[ERROR] Updated bot failed to start; rolling back source code.")
            rollback_ok, rollback_message = rollback_code(old_commit)
            print(rollback_message)
            if rollback_ok and requirements_changed(new_commit, old_commit):
                install_requirements(upgrade=False)
            print("Starting the previous version...")
            cmd_start()
            return False
    print("Update complete. .env and ignored JSON data were not reset.")
    return True


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


def cmd...