"""Runtime security services: audit trail and suspicious-action detection."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass

import config
import security_log


@dataclass(frozen=True, slots=True)
class AuditEntry:
    timestamp: float
    guild_id: int
    channel_id: int
    user_id: int
    command: str
    success: bool


class SecurityService:
    def __init__(self) -> None:
        self.audit: deque[AuditEntry] = deque(maxlen=config.AUDIT_LOG_RETENTION)
        self._actions: dict[tuple[int, int], deque[float]] = defaultdict(deque)

    def record_command(self, *, guild_id: int, channel_id: int, user_id: int, command: str, success: bool) -> bool:
        now = time.monotonic()
        self.audit.append(AuditEntry(now, guild_id, channel_id, user_id, command, success))
        if not success or guild_id <= 0:
            return False
        key = (guild_id, user_id)
        actions = self._actions[key]
        cutoff = now - config.SUSPICIOUS_ACTION_WINDOW
        while actions and actions[0] <= cutoff:
            actions.popleft()
        actions.append(now)
        if len(actions) == config.SUSPICIOUS_ACTION_THRESHOLD:
            security_log.log_security_event(
                f"Suspicious command burst: guild={guild_id} user={user_id} "
                f"{len(actions)} commands in {config.SUSPICIOUS_ACTION_WINDOW:.0f}s",
                actor=str(user_id),
            )
            return True
        return False

    def prune(self) -> None:
        cutoff = time.monotonic() - config.SUSPICIOUS_ACTION_WINDOW
        for key, actions in list(self._actions.items()):
            while actions and actions[0] <= cutoff:
                actions.popleft()
            if not actions:
                self._actions.pop(key, None)


security = SecurityService()
