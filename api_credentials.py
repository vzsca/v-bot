"""Persistent, guild-isolated storage for per-server API credentials."""

import copy
import json
import os
import tempfile
import threading
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent / "api_credentials.json"
_LOCK = threading.RLock()


def _load_unlocked() -> dict[str, dict[str, str]]:
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(guild_id): values for guild_id, values in data.items() if isinstance(values, dict)}


def _save_unlocked(data: dict[str, dict[str, str]]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".api_credentials.", suffix=".tmp", dir=CONFIG_FILE.parent)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_name, CONFIG_FILE)
        if os.name != "nt":
            try:
                os.chmod(CONFIG_FILE, 0o600)
            except OSError:
                pass
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def get(guild_id: int, platform: str) -> dict[str, str] | None:
    with _LOCK:
        values = _load_unlocked().get(str(guild_id), {}).get(platform)
        return copy.deepcopy(values) if isinstance(values, dict) else None


def set_credentials(guild_id: int, platform: str, credentials: dict[str, str]) -> None:
    if guild_id <= 0:
        raise ValueError("guild_id must be positive")
    if platform not in {"twitch", "youtube"}:
        raise ValueError("unsupported platform")
    with _LOCK:
        data = _load_unlocked()
        data.setdefault(str(guild_id), {})[platform] = dict(credentials)
        _save_unlocked(data)


def remove(guild_id: int, platform: str) -> bool:
    with _LOCK:
        data = _load_unlocked()
        guild = data.get(str(guild_id), {})
        if platform not in guild:
            return False
        guild.pop(platform, None)
        if guild:
            data[str(guild_id)] = guild
        else:
            data.pop(str(guild_id), None)
        _save_unlocked(data)
        return True
