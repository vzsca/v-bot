"""Persistent, guild-isolated storage for per-server API credentials."""

import copy
import os
import threading
from pathlib import Path

from safe_json import JsonStoreError, atomic_write, load_object

CONFIG_FILE = Path(__file__).resolve().parent.parent / "api_credentials.json"
_LOCK = threading.RLock()


def _load_unlocked() -> dict[str, dict[str, dict[str, str]]]:
    data = load_object(CONFIG_FILE, {})
    if not isinstance(data, dict):
        raise JsonStoreError(f"Invalid JSON structure in {CONFIG_FILE}")
    clean: dict[str, dict[str, dict[str, str]]] = {}
    for guild_id, values in data.items():
        if not isinstance(guild_id, str) or not guild_id.isdigit() or int(guild_id) <= 0:
            continue
        if not isinstance(values, dict):
            continue
        platforms: dict[str, dict[str, str]] = {}
        for platform, credentials in values.items():
            if platform not in {"twitch", "youtube"} or not isinstance(credentials, dict):
                continue
            if all(isinstance(key, str) and isinstance(value, str) for key, value in credentials.items()):
                platforms[platform] = dict(credentials)
        if platforms:
            clean[guild_id] = platforms
    return clean


def _save_unlocked(data: dict[str, dict[str, dict[str, str]]]) -> None:
    mode = 0o600 if os.name != "nt" else None
    atomic_write(CONFIG_FILE, data, mode=mode)


def get(guild_id: int, platform: str) -> dict[str, str] | None:
    with _LOCK:
        values = _load_unlocked().get(str(guild_id), {}).get(platform)
        return copy.deepcopy(values) if isinstance(values, dict) else None


def set_credentials(guild_id: int, platform: str, credentials: dict[str, str]) -> None:
    if guild_id <= 0:
        raise ValueError("guild_id must be positive")
    if platform not in {"twitch", "youtube"}:
        raise ValueError("unsupported platform")
    if not credentials or not all(isinstance(k, str) and isinstance(v, str) and v for k, v in credentials.items()):
        raise ValueError("credentials must contain non-empty string values")
    with _LOCK:
        data = _load_unlocked()
        data.setdefault(str(guild_id), {})[platform] = dict(credentials)
        _save_unlocked(data)


def remove(guild_id: int, platform: str) -> bool:
    if guild_id <= 0 or platform not in {"twitch", "youtube"}:
        return False
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
