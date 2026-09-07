"""Shared, guild-isolated announcement storage."""

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
    # Legacy entries without guild_id cannot safely be associated with a server.
    # They remain on disk for manual migration but are never returned by guild queries.
    return {"announcements": [a for a in announcements if isinstance(a, dict)]}


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
    return [a for a in _normalize(data)["announcements"] if a.get("guild_id") == guild_id]


def find(data: dict, guild_id: int, announcement_id: int) -> dict | None:
    return next((a for a in for_guild(data, guild_id) if a.get("id") == announcement_id), None)
