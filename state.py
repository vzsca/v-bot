"""Centralized container for all in-memory data shared between Cogs."""

import time


class BotState:
    __slots__ = (
        "kill_switch",
        "disabled_guilds",
        "temp_authorized_users",
        "sniped_messages",
        "created_raid_channels",
        "created_raid_roles",
        "running_commands",
    )

    def __init__(self):
        self.kill_switch: bool = False
        self.disabled_guilds: set[int] = set()
        # (guild_id, user_id) -> expiry timestamp. Temporary authorization is guild-scoped.
        self.temp_authorized_users: dict[tuple[int, int], float] = {}
        self.sniped_messages: dict[int, list[dict]] = {}
        # guild_id -> created Discord object IDs. Prevents cross-guild cleanup.
        self.created_raid_channels: dict[int, set[int]] = {}
        self.created_raid_roles: dict[int, set[int]] = {}
        self.running_commands: set[tuple[str, int]] = set()

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

    def add_raid_channel(self, guild_id: int, channel_id: int) -> None:
        self.created_raid_channels.setdefault(guild_id, set()).add(channel_id)

    def add_raid_role(self, guild_id: int, role_id: int) -> None:
        self.created_raid_roles.setdefault(guild_id, set()).add(role_id)

    def discard_raid_channel(self, guild_id: int, channel_id: int) -> None:
        bucket = self.created_raid_channels.get(guild_id)
        if bucket:
            bucket.discard(channel_id)
            if not bucket:
                self.created_raid_channels.pop(guild_id, None)

    def discard_raid_role(self, guild_id: int, role_id: int) -> None:
        bucket = self.created_raid_roles.get(guild_id)
        if bucket:
            bucket.discard(role_id)
            if not bucket:
                self.created_raid_roles.pop(guild_id, None)

    def add_sniped(self, channel_id: int, data: dict, limit: int) -> None:
        bucket = self.sniped_messages.setdefault(channel_id, [])
        bucket.insert(0, data)
        if len(bucket) > limit:
            del bucket[limit:]

    def clean_snipes(self, retention_seconds: int) -> int:
        now = time.time()
        removed = 0
        for channel_id, bucket in list(self.sniped_messages.items()):
            fresh = [m for m in bucket if now - m.get("time", 0).timestamp() <= retention_seconds]
            if fresh:
                self.sniped_messages[channel_id] = fresh
            else:
                self.sniped_messages.pop(channel_id, None)
                removed += 1
        return removed


# Single process-wide instance. Do not create another BotState instance here.
state = BotState()
