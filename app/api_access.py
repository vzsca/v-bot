"""Persistent allow-list of guilds allowed to configure API credentials from panel.py."""

import threading
from pathlib import Path

from safe_json import JsonStoreError, atomic_write, load_object

CONFIG_FILE = Path(__file__).resolve().parent.parent / "api_config_access.json"
_LOCK = threading.RLock()


def _load_unlocked() -> set[int]:
    data = load_object(CONFIG_FILE, {})
    if not isinstance(data, dict):
        raise JsonStoreError(f"Invalid JSON structure in {CONFIG_FILE}")
    guilds = data.get("guild_ids", [])
    if not isinstance(guilds, list):
        raise JsonStoreError(f"Invalid guild_ids structure in {CONFIG_FILE}")
    return {g for g in guilds if isinstance(g, int) and g > 0}


def get_allowed_guilds() -> set[int]:
    with _LOCK:
        return _load_unlocked()


def is_allowed(guild_id: int) -> bool:
    return guild_id in get_allowed_guilds()


def set_allowed(guild_id: int, allowed: bool) -> bool:
    if guild_id <= 0:
        return False
    with _LOCK:
        try:
            guilds = _load_unlocked()
            if allowed:
                guilds.add(guild_id)
            else:
                guilds.discard(guild_id)
            atomic_write(CONFIG_FILE, {"guild_ids": sorted(guilds)})
            return True
        except JsonStoreError:
            return False
