"""Persistent, guild-scoped storage for moderation reports (warm)."""

import copy
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from safe_json import JsonStoreError, atomic_write, load_object

logger = logging.getLogger("v-bot")
STORE_FILE = Path(__file__).resolve().parent.parent / "warm_reports.json"
_LOCK = threading.RLock()
MAX_REPORTS_PER_GUILD = 2000


def _normalize(data: object) -> dict:
    if not isinstance(data, dict):
        raise JsonStoreError(f"Invalid warm report store structure in {STORE_FILE}")
    reports = data.get("reports")
    if not isinstance(reports, list):
        raise JsonStoreError(f"Invalid warm reports list in {STORE_FILE}")
    clean = []
    for item in reports:
        if not isinstance(item, dict):
            continue
        if any(not isinstance(item.get(key), int) or item[key] <= 0 for key in ("guild_id", "target_id", "reporter_id")):
            continue
        if not isinstance(item.get("created_at"), str):
            continue
        reason = item.get("reason", "")
        if not isinstance(reason, str):
            reason = ""
        clean.append({
            "guild_id": item["guild_id"],
            "target_id": item["target_id"],
            "reporter_id": item["reporter_id"],
            "created_at": item["created_at"][:40],
            "reason": reason[:1000],
        })
    return {"reports": clean}


def _load_unlocked() -> dict:
    return _normalize(load_object(STORE_FILE, {"reports": []}))


def _save_unlocked(data: dict) -> bool:
    try:
        atomic_write(STORE_FILE, _normalize(data), mode=0o600)
        return True
    except JsonStoreError:
        logger.exception("Unable to persist warm reports.")
        return False


def add(guild_id: int, target_id: int, reporter_id: int, reason: str = "") -> tuple[bool, dict | None]:
    with _LOCK:
        data = _load_unlocked()
        guild_reports = [r for r in data["reports"] if r["guild_id"] == guild_id]
        if len(guild_reports) >= MAX_REPORTS_PER_GUILD:
            return False, None
        report = {
            "guild_id": guild_id,
            "target_id": target_id,
            "reporter_id": reporter_id,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "reason": reason.strip()[:1000],
        }
        working = copy.deepcopy(data)
        working["reports"].append(report)
        if not _save_unlocked(working):
            return False, None
        return True, report


def delete_for_target(guild_id: int, target_id: int, report_number: int) -> tuple[bool, dict | None]:
    """Delete a 1-based report number from one target's guild-scoped report list."""
    if report_number < 1:
        return False, None
    with _LOCK:
        data = _load_unlocked()
        matching_indices = [
            index for index, report in enumerate(data["reports"])
            if report["guild_id"] == guild_id and report["target_id"] == target_id
        ]
        if report_number > len(matching_indices):
            return False, None
        store_index = matching_indices[report_number - 1]
        removed = dict(data["reports"][store_index])
        working = copy.deepcopy(data)
        del working["reports"][store_index]
        if not _save_unlocked(working):
            return False, None
        return True, removed


def for_target(guild_id: int, target_id: int) -> list[dict]:
    with _LOCK:
        data = _load_unlocked()
        return [
            dict(report) for report in data["reports"]
            if report["guild_id"] == guild_id and report["target_id"] == target_id
        ]
