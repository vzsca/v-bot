"""Global, per-user and per-guild command rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from discord.ext import commands

import config


class RateLimitExceeded(commands.CheckFailure):
    """Raised when the global command limiter rejects a command."""

    def __init__(self, retry_after: float):
        self.retry_after = max(0.1, retry_after)
        super().__init__(f"⏳ Too many commands. Please wait {self.retry_after:.1f}s.")


class CommandRateLimiter:
    def __init__(self, limit: int = config.GLOBAL_COMMAND_LIMIT, window: float = config.GLOBAL_COMMAND_WINDOW):
        self.limit = limit
        self.window = window
        self._hits: dict[tuple[int, int, str], deque[float]] = defaultdict(deque)

    def check(self, guild_id: int, user_id: int, command: str, *, owner: bool = False) -> None:
        now = time.monotonic()
        key = (guild_id, user_id, command)
        hits = self._hits[key]
        cutoff = now - self.window
        while hits and hits[0] <= cutoff:
            hits.popleft()
        limit = config.OWNER_COMMAND_LIMIT if owner else self.limit
        if len(hits) >= limit:
            raise RateLimitExceeded(self.window - (now - hits[0]))
        hits.append(now)

    def prune(self) -> None:
        cutoff = time.monotonic() - self.window
        for key, hits in list(self._hits.items()):
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if not hits:
                self._hits.pop(key, None)


rate_limiter = CommandRateLimiter()
