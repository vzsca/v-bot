"""Centralized runtime state with persistence for security-critical data."""

from __future__ import annotations

import copy
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from safe_json import JsonStoreError, atomic_write, load_object


STATE_FILE = Path(__file__).resolve().parent.parent / "bot_state.json"
_STATE_LOCK = threading.RLock()


class BotState:
    __slots__ = (
        "created_raid_channels",
        "created_raid_roles",
        "disabled_guilds",
        "kill_switch",
        "running_commands",
        "sniped_messages",
        "temp_authorized_users",
    )

    def __init__(self):
        self.kill_switch: bool = False
        self.disabled_guilds: set[int] = set()
        self.temp_authorized_users: dict[tuple[int, int], float] = {}
        self.sniped_messages: dict[int, list[dict]] = {}
        self.created_raid_channels: dict[int, set[int]] = {}
        self.created_raid_roles: dict[int, set[int]] = {}
        self.running_commands: set[tuple[str, int]] = set()
        self._load_persistent_state()

    def _load_persistent_state(self) -> None:
        if not STATE_FILE.exists():
            return
        try:
            data = load_object(STATE_FILE, {})
        except JsonStoreError:
            self.kill_switch = True
            return
        if not isinstance(data, dict):
            self.kill_switch = True
            return

        self.kill_switch = bool(data.get("kill_switch", False))
        raw_disabled = data.get("disabled_guilds", [])
        if isinstance(raw_disabled, list):
            self.disabled_guilds = {int(value) for value in raw_disabled if isinstance(value, int) and value > 0}

        for field, target in (
            ("created_raid_channels", self.created_raid_channels),
            ("created_raid_roles", self.created_raid_roles),
        ):
            raw = data.get(field, {})
            if not isinstance(raw, dict):
                continue
            for guild_id, values in raw.items():
                try:
                    parsed_guild_id = int(guild_id)
                except (TypeError, ValueError):
                    continue
                if parsed_guild_id <= 0 or not isinstance(values, list):
                    continue
                target[parsed_guild_id] = {
                    int(value) for value in values if isinstance(value, int) and value > 0
                }

    def _persistent_payload(self) -> dict:
        return {
            "kill_switch": self.kill_switch,
            "disabled_guilds": sorted(self.disabled_guilds),
            "created_raid_channels": {
                str(guild_id): sorted(channel_ids)
                for guild_id, channel_ids in self.created_raid_channels.items()
                if channel_ids
            },
            "created_raid_roles": {
                str(guild_id): sorted(role_ids)
                for guild_id, role_ids in self.created_raid_roles.items()
                if role_ids
            },
        }

    def _save_persistent_state(self) -> bool:
        try:
            atomic_write(
                STATE_FILE,
                copy.deepcopy(self._persistent_payload()),
                mode=0o600 if os.name == "posix" else None,
            )
        except JsonStoreError:
            return False
        return True

    def set_kill_switch(self, enabled: bool) -> bool:
        with _STATE_LOCK:
            previous = self.kill_switch
            self.kill_switch = bool(enabled)
            if self._save_persistent_state():
                return True
            if not enabled:
                self.kill_switch = previous
            return False

    def set_guild_disabled(self, guild_id: int, disabled: bool) -> bool:
        if guild_id <= 0:
            raise ValueError("guild_id must be positive")
        with _STATE_LOCK:
            was_disabled = guild_id in self.disabled_guilds
            if disabled:
                self.disabled_guilds.add(guild_id)
            else:
                self.disabled_guilds.discard(guild_id)
            if self._save_persistent_state():
                return True
            if was_disabled:
                self.disabled_guilds.add(guild_id)
            else:
                self.disabled_guilds.discard(guild_id)
            return False

    def is_temp_authorized(self, guild_id: int | None, user_id: int) -> bool:
        if guild_id is None:
            return False
        key = (guild_id, user_id)
        expiry = self.temp_authorized_users.get(key)
        if expiry is None:
            return False
        if expiry <= time.time():
            self.temp_authorized_users.pop(key, None)
            return False
        return True

    def add_temp_owner(self, guild_id: int, user_id: int, duration: int) -> float:
        if guild_id <= 0 or user_id <= 0:
            raise ValueError("Guild and user IDs must be positive.")
        if duration < 1:
            raise ValueError("Temporary owner duration must be at least 1 second.")
        expiry = time.time() + duration
        self.temp_authorized_users[(guild_id, user_id)] = expiry
        return expiry

    def clean_expired(self) -> list[tuple[int, int]]:
        now = time.time()
        expired = [key for key, expiry in self.temp_authorized_users.items() if expiry <= now]
        for key in expired:
            self.temp_authorized_users.pop(key, None)
        return expired

    def add_raid_channel(self, guild_id: int, channel_id: int) -> bool:
        with _STATE_LOCK:
            self.created_raid_channels.setdefault(guild_id, set()).add(channel_id)
            return self._save_persistent_state()

    def add_raid_role(self, guild_id: int, role_id: int) -> bool:
        with _STATE_LOCK:
            self.created_raid_roles.setdefault(guild_id, set()).add(role_id)
            return self._save_persistent_state()

    def discard_raid_channel(self, guild_id: int, channel_id: int) -> bool:
        with _STATE_LOCK:
            bucket = self.created_raid_channels.get(guild_id)
            if bucket:
                bucket.discard(channel_id)
                if not bucket:
                    self.created_raid_channels.pop(guild_id, None)
            return self._save_persistent_state()

    def discard_raid_role(self, guild_id: int, role_id: int) -> bool:
        with _STATE_LOCK:
            bucket = self.created_raid_roles.get(guild_id)
            if bucket:
                bucket.discard(role_id)
                if not bucket:
                    self.created_raid_roles.pop(guild_id, None)
            return self._save_persistent_state()

    def add_sniped(self, channel_id: int, data: dict, limit: int) -> None:
        if limit < 1:
            raise ValueError("Snipe limit must be positive.")
        bucket = self.sniped_messages.setdefault(channel_id, [])
        bucket.insert(0, data)
        if len(bucket) > limit:
            del bucket[limit:]

    @staticmethod
    def _snipe_timestamp(item: dict) -> float | None:
        value = item.get("time")
        if isinstance(value, datetime):
            return value.timestamp()
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return None
        return None

    def clean_snipes(self, retention_seconds: int) -> int:
        if retention_seconds < 0:
            raise ValueError("Snipe retention cannot be negative.")
        now = time.time()
        removed = 0
        for channel_id, bucket in list(self.sniped_messages.items()):
            fresh = []
            for item in bucket:
                timestamp = self._snipe_timestamp(item)
                if timestamp is not None and 0 <= now - timestamp <= retention_seconds:
                    fresh.append(item)
                else:
                    removed += 1
            if fresh:
                self.sniped_messages[channel_id] = fresh
            else:
                self.sniped_messages.pop(channel_id, None)
        return removed


state = BotState()
