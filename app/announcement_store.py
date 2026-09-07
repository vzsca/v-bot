"""Guild-isolated announcement storage with atomic, fail-safe transactions."""

import copy
import logging
import threading
from pathlib import Path

from safe_json import JsonStoreError, atomic_write, load_object

logger = logging.getLogger("v-bot")
CONFIG_FILE = Path(__file__).resolve().parent.parent / "annonce_config.json"
_LOCK = threading.RLock()


def _normalize(data: object) -> dict:
    if not isinstance(data, dict):
        raise JsonStoreError(f"Invalid announcement configuration structure in {CONFIG_FILE}")
    announcements = data.get("announcements")
    if not isinstance(announcements, list):
        raise JsonStoreError(f"Invalid announcements structure in {CONFIG_FILE}")
    clean = []
    for item in announcements:
        if not isinstance(item, dict):
            continue
        if not isinstance(item.get("guild_id"), int) or item["guild_id"] <= 0:
            continue
        if not isinstance(item.get("id"), int) or item["id"] < 1:
            continue
        clean.append(item)
    return {"announcements": clean}


def _load_unlocked() -> dict:
    data = load_object(CONFIG_FILE, {"announcements": []})
    return _normalize(data)


def _save_unlocked(data: dict) -> bool:
    try:
        atomic_write(CONFIG_FILE, _normalize(data))
        return True
    except JsonStoreError:
        logger.exception("Unable to atomically save announcement configuration.")
        return False


def load() -> dict:
    with _LOCK:
        return _load_unlocked()


def save(data: dict) -> bool:
    with _LOCK:
        return _save_unlocked(data)


def transaction(mutator) -> tuple[bool, object]:
    with _LOCK:
        data = _load_unlocked()
        working = copy.deepcopy(data)
        result = mutator(working)
        if not _save_unlocked(working):
            return False, None
        data.clear()
        data.update(working)
        return True, result


def for_guild(data: dict, guild_id: int) -> list[dict]:
    return [a for a in _normalize(data)["announcements"] if a["guild_id"] == guild_id]


def find(data: dict, guild_id: int, announcement_id: int) -> dict | None:
    return next((a for a in for_guild(data, guild_id) if a["id"] == announcement_id), None)


def next_id(data: dict, guild_id: int) -> int:
    return max((a["id"] for a in for_guild(data, guild_id)), default=0) + 1


def add(data: dict, announcement: dict) -> dict:
    guild_id = announcement["guild_id"]
    announcement = dict(announcement)
    announcement["id"] = next_id(data, guild_id)
    data.setdefault("announcements", []).append(announcement)
    return announcement


def remove(data: dict, guild_id: int, announcement_id: int) -> bool:
    announcement = find(data, guild_id, announcement_id)
    if not announcement:
        return False
    data["announcements"].remove(announcement)
    return True
