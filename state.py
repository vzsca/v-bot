"""
Centralized container for all in-memory data shared between Cogs.
"""

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
        self.temp_authorized_users: dict[int, float] = {}  # {user_id: expiry_timestamp}
        self.sniped_messages: dict[int, list[dict]] = {}   # {channel_id: [data, ...]}
        self.created_raid_channels: set[int] = set()
        self.created_raid_roles: set[int] = set()

        # Anti-double-execution protection: {(command_name, guild_id_or_user_id)}
        # while a heavy command (raid, dmall, spam) is already running.
        self.running_commands: set[tuple[str, int]] = set()

    # --- Temporary owners ---

    def is_temp_authorized(self, user_id: int) -> bool:
        expiry = self.temp_authorized_users.get(user_id)
        return expiry is not None and expiry > time.time()

    def add_temp_owner(self, user_id: int, duration: int) -> float:
        expiry = time.time() + max(1, duration)
        self.temp_authorized_users[user_id] = expiry
        return expiry

    def clean_expired(self) -> list[int]:
        """Removes expired temporary owners and returns the list of removed IDs."""
        now = time.time()
        expired = [uid for uid, expiry in self.temp_authorized_users.items() if expiry < now]
        for uid in expired:
            del self.temp_authorized_users[uid]
        return expired

    # --- Snipe ---

    def add_sniped(self, channel_id: int, data: dict, limit: int) -> None:
        bucket = self.sniped_messages.setdefault(channel_id, [])
        bucket.insert(0, data)
        if len(bucket) > limit:
            bucket.pop()


# Single instance, imported by all Cogs: `from state import state`
state = BotState()


# Instance unique, importée par tous les cogs : `from state import state`
state = BotState()
