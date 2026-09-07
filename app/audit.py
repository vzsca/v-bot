"""Structured in-memory audit trail and suspicious-action detection."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass

import config
import security_log


@dataclass(frozen=True, slots=True)
class AuditEvent:
    timestamp: float
    guild_id: int
    actor_id: int
    action: str
    target_id: int | None = None
    success: bool = True


class AuditManager:
    def __init__(self, max_events: int = config.AUDIT_LOG_RETENTION):
        self.events: deque[AuditEvent] = deque(maxlen=max_events)
        self._actions: dict[tuple[int, int], deque[float]] = defaultdict(deque)

    def record(self, guild_id: int, actor_id: int, action: str, target_id: int | None = None, success: bool = True) -> bool:
        now = time.monotonic()
        event = AuditEvent(now, guild_id, actor_id, action, target_id, success)
        self.events.append(event)
        key = (guild_id, actor_id)
        hits = self._actions[key]
        cutoff = now - config.SUSPICIOUS_ACTION_WINDOW
        while hits and hits[0] <= cutoff:
            hits.popleft()
        hits.append(now)
        suspicious = len(hits) >= config.SUSPICIOUS_ACTION_THRESHOLD
        security_log.log_security_event(
            f"audit action={action} guild={guild_id} target={target_id or '-'} success={success}",
            actor=str(actor_id),
        )
        if suspicious:
            security_log.log_security_event(
                f"SUSPICIOUS ACTION BURST: {len(hits)} actions in {config.SUSPICIOUS_ACTION_WINDOW:.0f}s",
                actor=str(actor_id),
            )
        return suspicious

    def recent(self, guild_id: int, limit: int = 50) -> list[AuditEvent]:
        if limit < 1:
            return []
        return [event for event in reversed(self.events) if event.guild_id == guild_id][:limit]

    def prune(self) -> None:
        cutoff = time.monotonic() - config.SUSPICIOUS_ACTION_WINDOW
        for key, hits in list(self._actions.items()):
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if not hits:
                self._actions.pop(key, None)


manager = AuditManager()
