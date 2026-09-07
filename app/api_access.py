"""Persistent allow-list of guilds allowed to configure API credentials from panel.py."""

import json
import threading
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent / "api_config_access.json"
_LOCK = threading.RLock()


def _load_unlocked() -> set[int]:
    if not CONFIG_FILE.exists():
        return set()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    guilds = data.get("guild_ids", []) if isinstance(data, dict) else []
    return {int(g) for g in guilds if isinstance(g, int) and g > 0}


def get_allowed_guilds() -> set[int]:
    with _LOCK:
        return _load_unlocked()


def is_allowed(guild_id: int) -> bool:
    return guild_id in get_allowed_guilds()


def set_allowed(guild_id: int, allowed: bool) -> bool:
    if guild_id <= 0:
        return False
    with _LOCK:
        guilds = _load_unlocked()
        if allowed:
            guilds.add(guild_id)
        else:
            guilds.discard(guild_id)
        tmp = CONFIG_FILE.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps({"guild_ids": sorted(guilds)}, indent=4), encoding="utf-8")
            tmp.replace(CONFIG_FILE)
            return True
        except OSError:
            tmp.unlink(missing_ok=True)
            return False
