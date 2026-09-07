"""Shared, guild-isolated announcement storage.

Announcement IDs are scoped to a guild: two servers may both have announcement #1.
All reads/writes go through this module so integrations cannot accidentally mix servers.
"""

import json
import logging
import threading
from pathlib import Path

logger = logging.getLogger("v-bot")
CONFIG_FILE = Path(__file__).resolve().parent / "annonce_config.json"
_LOCK = threading.RLock()


def _normalize(data: object) -> dict:
    if not isinstance(data, dict):
        data = {}
    announcements = data.get("announcements")
    if not isinstance(announcements, list):
        announcements = []
    # Entries without guild_id are unsafe to associate with a server and are ignored.
    clean = []
    for item in announcements:
        if not isinstance(item, dict):
            continue
        if not isinstance(item.get("guild_id"), int):
            continue
        if not isinstance(item.get("id"), int) or item["id"] < 1:
            continue
        clean.append(item)
    return {"announcements": clean}


def load() -> dict:
    with _LOCK:
        try:
            if not CONFIG_FILE.exists():
                return {"announcements": []}
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                return _normalize(json.load(file))
        except (OSError, json.JSONDecodeError):
            logger.exception("Unable to load announcement configuration.")
            return {"announcements": []}


def save(data: dict) -> bool:
    normalized = _normalize(data)
    with _LOCK:
        tmp = CONFIG_FILE.with_suffix(".json.tmp")
        try:
            with tmp.open("w", encoding="utf-8") as file:
                json.dump(normalized, file, indent=4, ensure_ascii=False)
                file.flush()
            tmp.replace(CONFIG_FILE)
            return True
        except OSError:
            logger.exception("Unable to atomically save announcement configuration.")
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            return False


def for_guild(data: dict, guild_id: int) -> list[dict]:
    return [a for a in _normalize(data)["announcements"] if a["guild_id"] == guild_id]


def find(data: dict, guild_id: int, announcement_id: int) -> dict | None:
    return next((a for a in for_guild(data, guild_id) if a["id"] == announcement_id), None)


def next_id(data: dict, guild_id: int) -> int:
    """Return the next announcement ID for this guild only."""
    return max((a["id"] for a in for_guild(data, guild_id)), default=0) + 1


def add(data: dict, announcement: dict) -> dict:
    """Add an announcement after enforcing its guild-scoped identity."""
    guild_id = announcement["guild_id"]
    announcement = dict(announcement)
    announcement["id"] = next_id(data, guild_id)
    data["announcements"].append(announcement)
    return announcement


def remove(data: dict, guild_id: int, announcement_id: int) -> bool:
    announcement = find(data, guild_id, announcement_id)
    if not announcement:
        return False
    data["announcements"].remove(announcement)
    return True
