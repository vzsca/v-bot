"""
Interactive cross-platform control panel for v-bot.

Compatible with:
- Windows
- Linux
- macOS
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

import security_log
from deps import install_requirements


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parent

ENV_PATH = ROOT / ".env"
BOT_PID_FILE = ROOT / "bot.pid"
BOT_START_FILE = ROOT / "bot.start"
SERVERS_FILE = ROOT / "servers.txt"
LOG_FILE = ROOT / "bot.log"
SECURITY_LOG_FILE = ROOT / "security.log"


# ============================================================
# Platform / Python executable
# ============================================================

IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


if IS_WINDOWS:
    PYTHON_EXE = ROOT / "venv" / "Scripts" / "python.exe"
else:
    PYTHON_EXE = ROOT / "venv" / "bin" / "python"


# ============================================================
# .env utilities
# ============================================================

def _read_env_lines() -> list[str]:
    if not ENV_PATH.exists():
        return []

    return ENV_PATH.read_text(
        encoding="utf-8"
    ).splitlines()


def _write_env_lines(lines: list[str]) -> None:
    ENV_PATH.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def get_env_value(key: str) -> str:
    prefix = f"{key}="

    for line in _read_env_lines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()

    return ""


def set_env_value(key: str, value: str) -> None:
    lines = _read_env_lines()
    prefix = f"{key}="

    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = f"{key}={value}"
            _write_env_lines(lines)
            return

    lines.append(f"{key}={value}")
    _write_env_lines(lines)


# ============================================================
# Bot process management
# ============================================================

def _get_bot_pid() -> int | None:
    if not BOT_PID_FILE.exists():
        return None

    try:
        pid = int(
            BOT_PID_FILE.read_text(
                encoding="utf-8"
            ).strip()
        )
    except (ValueError, OSError):
        return None

    if psutil.pid_exists(pid):
        return pid

    _clear_pid_files()
    return None


def _clear_pid_files() -> None:
    BOT_PID_FILE.unlink(missing_ok=True)
    BOT_START_FILE.unlink(missing_ok=True)


def is_running() -> bool:
    return _get_bot_pid() is not None


# ============================================================
# Start / Stop / Restart
# ============================================================

def cmd_start() -> None:
    if is_running():
        print("The bot is already running.")
        return

    if not PYTHON_EXE.exists():
        print("[ERROR] Python virtual environment not found.")
        print(f"Expected Python executable: {PYTHON_EXE}")
        print("Run the initial setup first.")
        return

    main_file = ROOT / "main.py"

    if not main_file.exists():
        print("[ERROR] main.py was not found.")
        return

    print("Starting bot...")

    env = os.environ.copy()

    # Consistent UTF-8 behavior across platforms.
    env["PYTHONUTF8"] = "1"

    command = [
        str(PYTHON_EXE),
        str(main_file),
    ]

    try:
        if IS_WINDOWS:
            # CREATE_NEW_CONSOLE only exists on Windows.
            process = subprocess.Popen(
                command,
                cwd=str(ROOT),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                env=env,
            )

        else:
            # Linux / macOS
            process = subprocess.Popen(
                command,
                cwd=str(ROOT),
                env=env,
                start_new_session=True,
            )

    except OSError as e:
        print(f"[ERROR] Failed to start the bot: {e}")
        return

    BOT_PID_FILE.write_text(
        str(process.pid),
        encoding="utf-8",
    )

    BOT_START_FILE.write_text(
        str(int(time.time())),
        encoding="utf-8",
    )

    time.sleep(2)

    if is_running():
        print("Bot started.")
        print(f"PID: {process.pid}")
    else:
        print('Failed to start the bot. Type "logs" to see why.')


def cmd_stop() -> None:
    pid = _get_bot_pid()

    if pid is None:
        print("The bot is not running.")
        return

    try:
        proc = psutil.Process(pid)

        # Kill child processes first.
        children = proc.children(recursive=True)

        for child in children:
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

    except psutil.Error as e:
        print(f"[ERROR] Failed to stop the bot: {e}")
        return

    _clear_pid_files()

    print("Bot stopped.")


def cmd_restart() -> None:
    print("Restarting bot...")

    cmd_stop()

    time.sleep(2)

    cmd_start()


# ============================================================
# Status / Uptime
# ============================================================

def cmd_status() -> None:
    pid = _get_bot_pid()

    if pid is None:
        print("Bot inactive.")
        return

    try:
        process = psutil.Process(pid)

        print("Bot active.")
        print(f"PID: {pid}")
        print(f"Status: {process.status()}")

    except psutil.NoSuchProcess:
        _clear_pid_files()
        print("Bot inactive.")


def cmd_uptime() -> None:
    if not BOT_START_FILE.exists():
        print("Uptime unknown.")
        return

    try:
        start_epoch = int(
            BOT_START_FILE.read_text(
                encoding="utf-8"
            ).strip()
        )

    except (ValueError, OSError):
        print("Uptime unknown.")
        return

    elapsed = max(
        0,
        int(time.time()) - start_epoch,
    )

    hours, remainder = divmod(
        elapsed,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    print(
        f"The bot has been running for "
        f"{hours}h {minutes}m {seconds}s."
    )


# ============================================================
# Update
# ============================================================

def cmd_update() -> None:
    print("Updating dependencies:")

    try:
        install_requirements(upgrade=True)
    except Exception as e:
        print(f"[ERROR] Failed to update dependencies: {e}")
        return

    print("Update complete.")


# ============================================================
# Logs
# ============================================================

def _display_log_file(
    file_path: Path,
    title: str,
    lines_count: int = 50,
) -> None:

    if not file_path.exists():
        print(f"{file_path.name} does not exist yet.")
        return

    try:
        lines = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

    except OSError as e:
        print(f"[ERROR] Unable to read {file_path.name}: {e}")
        return

    last_lines = lines[-lines_count:]

    print()
    print(
        f"--- {title} "
        f"(last {len(last_lines)} entries "
        f"out of {len(lines)}) ---"
    )

    if not last_lines:
        print("(empty)")
        return

    for line in last_lines:
        print(line)


def cmd_logs() -> None:
    _display_log_file(
        LOG_FILE,
        "bot.log",
        lines_count=50,
    )


def cmd_security_logs() -> None:
    _display_log_file(
        SECURITY_LOG_FILE,
        "security.log",
        lines_count=30,
    )


# ============================================================
# Servers
# ============================================================

def cmd_servers() -> None:
    if not SERVERS_FILE.exists():
        print(
            "List unavailable: the bot has not "
            "finished connecting yet."
        )
        return

    try:
        content = SERVERS_FILE.read_text(
            encoding="utf-8"
        )
    except OSError as e:
        print(f"[ERROR] Unable to read servers.txt: {e}")
        return

    print()
    print(content)


# ============================================================
# Owner management
# ============================================================

def cmd_add_secondary_owner() -> None:
    new_id = input(
        "Discord ID of the new secondary owner: "
    ).strip()

    if not new_id:
        print("[ERROR] No ID entered.")
        return

    if not new_id.isdigit():
        print("[ERROR] The ID must contain digits only.")
        return

    current = get_env_value(
        "OWNERS_SECONDARY_IDS"
    )

    existing_ids = [
        x.strip()
        for x in current.split(",")
        if x.strip()
    ]

    if new_id in existing_ids:
        print(
            "This ID is already a secondary owner in .env."
        )
        return

    existing_ids.append(new_id)

    set_env_value(
        "OWNERS_SECONDARY_IDS",
        ",".join(existing_ids),
    )

    security_log.log_security_event(
        f"Permanent secondary owner added: {new_id}",
        actor="panel",
    )

    print(
        f"Secondary owner {new_id} added to .env."
    )

    print(
        "The change will take effect when "
        "the bot is (re)started."
    )


def cmd_set_token() -> None:
    new_token = input(
        "New Discord token: "
    ).strip()

    if not new_token:
        print(
            "[ERROR] No token entered, nothing was changed."
        )
        return

    set_env_value(
        "DISCORD_TOKEN",
        new_token,
    )

    # The token value is NEVER logged.
    security_log.log_security_event(
        "Discord token changed",
        actor="panel",
    )

    print("Token saved to .env.")

    print(
        "The change will take effect when "
        "the bot is (re)started."
    )


def cmd_set_principal_owner() -> None:
    new_id = input(
        "Enter the Discord ID of the principal owner: "
    ).strip()

    if not new_id:
        print(
            "[ERROR] No ID entered, nothing was changed."
        )
        return

    if not new_id.isdigit():
        print(
            "[ERROR] The ID must contain digits only, "
            "nothing was changed."
        )
        return

    set_env_value(
        "OWNER_PRINCIPAL_ID",
        new_id,
    )

    security_log.log_security_event(
        f"Principal owner set: {new_id}",
        actor="panel",
    )

    print(
        "Principal owner saved to .env."
    )

    print(
        "The change will take effect when "
        "the bot is (re)started."
    )


# ============================================================
# Sensitive commands
# ============================================================

def _dangerous_commands_enabled() -> bool:
    return get_env_value(
        "DANGEROUS_COMMANDS_ENABLED"
    ).strip().lower() in (
        "1",
        "true",
        "on",
        "yes",
    )


def cmd_toggle_dangerous() -> None:
    """
    Enables/disables sensitive commands.

    When disabled, the dangerous Cog is not loaded by the bot.
    A restart is required for the change to take effect.
    """

    if _dangerous_commands_enabled():

        set_env_value(
            "DANGEROUS_COMMANDS_ENABLED",
            "false",
        )

        security_log.log_security_event(
            "Sensitive commands DISABLED "
            "(raid/remove_raid/dmall/spam)",
            actor="panel",
        )

        print(
            "Sensitive commands "
            "(raid, remove_raid, dmall, spam) DISABLED."
        )

        print(
            "The change will take effect when "
            "the bot is (re)started."
        )

        return

    print()

    print(
        "You are about to ENABLE the sensitive commands:"
        " raid, remove_raid, dmall, spam."
    )

    print(
        "These commands can cause serious damage "
        "if the token or an owner account is compromised."
    )

    confirm = input(
        "Type ENABLE (in uppercase) to confirm, "
        "or anything else to cancel: "
    ).strip()

    if confirm != "ENABLE":
        print("Cancelled, nothing was changed.")
        return

    set_env_value(
        "DANGEROUS_COMMANDS_ENABLED",
        "true",
    )

    security_log.log_security_event(
        "Sensitive commands ENABLED "
        "(raid/remove_raid/dmall/spam)",
        actor="panel",
    )

    print(
        "Sensitive commands ENABLED."
    )

    print(
        "The change will take effect when "
        "the bot is (re)started."
    )


# ============================================================
# Prefix
# ============================================================

def cmd_set_prefix() -> None:
    new_prefix = input(
        "New prefix: "
    ).strip()

    if not new_prefix:
        print(
            "[ERROR] No prefix entered, "
            "nothing was changed."
        )
        return

    if len(new_prefix) > 10:
        print(
            "[ERROR] The prefix cannot exceed "
            "10 characters."
        )
        return

    if any(char.isspace() for char in new_prefix):
        print(
            "[ERROR] The prefix cannot contain spaces."
        )
        return

    set_env_value(
        "BOT_PREFIX",
        new_prefix,
    )

    security_log.log_security_event(
        f"Bot prefix changed: {new_prefix}",
        actor="panel",
    )

    print(
        f"Prefix saved to .env: {new_prefix}"
    )

    print(
        "The change will take effect on "
        "the next bot restart."
    )


# ============================================================
# Twitch API
# ============================================================

def cmd_set_twitch_api() -> None:
    """Configure Twitch Client ID and Client Secret."""

    print()
    print("=== Twitch API Configuration ===")

    client_id = input(
        "Twitch Client ID: "
    ).strip()

    if not client_id:
        print(
            "[ERROR] No Client ID entered, "
            "nothing was changed."
        )
        return

    client_secret = input(
        "Twitch Client Secret: "
    ).strip()

    if not client_secret:
        print(
            "[ERROR] No Client Secret entered, "
            "nothing was changed."
        )
        return

    set_env_value(
        "TWITCH_CLIENT_ID",
        client_id,
    )

    set_env_value(
        "TWITCH_CLIENT_SECRET",
        client_secret,
    )

    security_log.log_security_event(
        "Twitch API credentials changed",
        actor="panel",
    )

    print(
        "Twitch API credentials saved to .env."
    )

    print(
        "The change will take effect on "
        "the next bot restart."
    )

# ============================================================
# YouTube API
# ============================================================

def cmd_set_youtube_api() -> None:
    """Configure the YouTube API key."""

    print()
    print("=== YouTube API Configuration ===")

    api_key = input(
        "YouTube API Key: "
    ).strip()

    if not api_key:
        print(
            "[ERROR] No API key entered, "
            "nothing was changed."
        )
        return

    set_env_value(
        "YOUTUBE_API_KEY",
        api_key,
    )

    security_log.log_security_event(
        "YouTube API key changed",
        actor="panel",
    )

    print(
        "YouTube API key saved to .env."
    )

    print(
        "The change will take effect on "
        "the next bot restart."
    )


# ============================================================
# Commands
# ============================================================

COMMANDS = [
    (
        "start",
        "start the bot",
        cmd_start,
    ),
    (
        "stop",
        "stop the bot",
        cmd_stop,
    ),
    (
        "restart",
        "restart the bot",
        cmd_restart,
    ),
    (
        "status",
        "current bot status",
        cmd_status,
    ),
    (
        "uptime",
        "how long the bot has been running",
        cmd_uptime,
    ),
    (
        "update",
        "update dependencies",
        cmd_update,
    ),
    (
        "logs",
        "display the latest bot.log entries",
        cmd_logs,
    ),
    (
        "security_logs",
        "display security.log",
        cmd_security_logs,
    ),
    (
        "servers",
        "list the servers the bot is connected to",
        cmd_servers,
    ),
    (
        "add_secondary_owner",
        "add a permanent secondary owner to .env",
        cmd_add_secondary_owner,
    ),
    (
        "set_token",
        "set or change the Discord token in .env",
        cmd_set_token,
    ),
    (
        "set_principal_owner",
        "set or change the principal owner in .env",
        cmd_set_principal_owner,
    ),
    (
        "toggle_dangerous",
        "enable/disable raid, remove_raid, dmall, spam",
        cmd_toggle_dangerous,
    ),
    (
        "set_prefix",
        "set or change the prefix in .env",
        cmd_set_prefix,
    ),
    (
        "set_twitch_api",
        "set or change the Twitch API credentials",
        cmd_set_twitch_api,
    ),
    (
    "set_youtube_api",
    "set or change the YouTube API key",
    cmd_set_youtube_api,
    ),
]

COMMAND_MAP = {
    name: func
    for name, _, func in COMMANDS
}


# ============================================================
# Help
# ============================================================

def cmd_help() -> None:
    print()
    print("===== v-bot =====")
    print()

    width = (
        max(
            len(name)
            for name, _, _ in COMMANDS
        )
        + 2
    )

    for name, desc, _ in COMMANDS:
        print(
            f"{name.ljust(width)}- {desc}"
        )

    print(
        f"{'help'.ljust(width)}- "
        "display this list again"
    )

    print(
        f"{'exit'.ljust(width)}- "
        "close this panel "
        "(the bot will continue running)"
    )

    print()


# ============================================================
# Startup checks
# ============================================================

def check_principal_owner() -> None:
    if get_env_value(
        "OWNER_PRINCIPAL_ID"
    ):
        return

    print()

    print(
        "No principal owner is defined in .env "
        "(OWNER_PRINCIPAL_ID)."
    )

    print(
        "The bot cannot start without it."
    )

    cmd_set_principal_owner()


def check_token() -> None:
    if get_env_value(
        "DISCORD_TOKEN"
    ):
        return

    print()

    print(
        "No Discord token is defined in .env "
        "(DISCORD_TOKEN)."
    )

    print(
        "The bot cannot connect without it."
    )

    cmd_set_token()


# ============================================================
# Main panel
# ============================================================

def main() -> None:

    print("===================================")
    print("          v-bot Control Panel")
    print("===================================")
    print()

    print(
        f"Platform: "
        f"{'Windows' if IS_WINDOWS else 'macOS' if IS_MACOS else 'Linux' if IS_LINUX else sys.platform}"
    )

    print(
        f"Python: {PYTHON_EXE}"
    )

    print()

    if not ENV_PATH.exists():
        print(
            "[WARNING] .env file not found. "
            "The bot will fail to start."
        )
        print()

    else:
        check_principal_owner()
        check_token()

    print(
        'Type "help" for the list of panel commands.'
    )

    while True:
        print()

        try:
            cmd = input(
                "v-bot> "
            ).strip().lower()

        except (EOFError, KeyboardInterrupt):
            print()
            break

        if cmd == "exit":
            break

        elif cmd == "help":
            cmd_help()

        elif cmd in COMMAND_MAP:
            try:
                COMMAND_MAP[cmd]()
            except Exception as e:
                print(
                    f"[ERROR] Command failed: {e}"
                )

        elif cmd:
            print(
                f'Unknown command "{cmd}". '
                'Type "help" for the list.'
            )


if __name__ == "__main__":
    main()
