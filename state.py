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
        self.temp_authorized_users: dict[int, float] = {}
        self.sniped_messages: dict[int, list[dict]] = {}
        self.created_raid_channels: set[int] = set()
        self.created_raid_roles: set[int] = set()
        self.running_commands: set[tuple[str, int]] = set()

    def is_temp_authorized(self, user_id: int) -> bool:
        expiry = self.temp_authorized_users.get(user_id)
        if expiry is None:
            return False
        if expiry <= time.time():
            self.temp_authorized_users.pop(user_id, None)
            return False
        return True

    def add_temp_owner(self, user_id: int, duration: int) -> float:
        if duration < 1:
            raise ValueError("Temporary owner duration must be at least 1 second.")
        expiry = time.time() + duration
        self.temp_authorized_users[user_id] = expiry
        return expiry

    def clean_expired(self) -> list[int]:
        now = time.time()
        expired = [uid for uid, expiry in self.temp_authorized_users.items() if expiry <= now]
        for uid in expired:
            self.temp_authorized_users.pop(uid, None)
        return expired

    def add_sniped(self, channel_id: int, data: dict, limit: int) -> None:
        bucket = self.sniped_messages.setdefault(channel_id, [])
        bucket.insert(0, data)
        if len(bucket) > limit:
            del bucket[limit:]


# Single process-wide instance. Do not create another BotState instance here.
state = BotState()
