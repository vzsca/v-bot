"""Global, per-user and per-command rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from discord.ext import commands

import config


class RateLimitExceeded(commands.CheckFailure):
    """Raised when a command exceeds the configured rate limit."""

    def __init__(self, retry_after: float):
        self.retry_after = max(0.1, retry_after)
        super().__init__(f"⏳ Too many commands. Please wait {self.retry_after:.1f}s.")


class CommandRateLimiter:
    """Sliding-window limiter with global-user and per-command buckets."""

    def __init__(self):
        self._global: dict[tuple[int, int], deque[float]] = defaultdict(deque)
        self._commands: dict[tuple[int, int, str], deque[float]] = defaultdict(deque)

    @staticmethod
    def _trim(hits: deque[float], cutoff: float) -> None:
        while hits and hits[0] <= cutoff:
            hits.popleft()

    def check(self, guild_id: int, user_id: int, command: str, *, owner: bool = False) -> None:
        now = time.monotonic()
        cutoff = now - config.GLOBAL_COMMAND_WINDOW
        global_key = (guild_id, user_id)
        command_key = (guild_id, user_id, command)
        global_hits = self._global[global_key]
        command_hits = self._commands[command_key]
        self._trim(global_hits, cutoff)
        self._trim(command_hits, cutoff)

        global_limit = config.OWNER_COMMAND_LIMIT if owner else config.GLOBAL_COMMAND_LIMIT
        command_limit = max(2, global_limit // 2)
        if len(global_hits) >= global_limit:
            raise RateLimitExceeded(config.GLOBAL_COMMAND_WINDOW - (now - global_hits[0]))
        if len(command_hits) >= command_limit:
            raise RateLimitExceeded(config.GLOBAL_COMMAND_WINDOW - (now - command_hits[0]))

        global_hits.append(now)
        command_hits.append(now)

    def prune(self) -> None:
        cutoff = time.monotonic() - config.GLOBAL_COMMAND_WINDOW
        for buckets in (self._global, self._commands):
            for key, hits in list(buckets.items()):
                self._trim(hits, cutoff)
                if not hits:
                    buckets.pop(key, None)


rate_limiter = CommandRateLimiter()
