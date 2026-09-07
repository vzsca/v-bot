"""Lightweight runtime metrics for commands, events and API calls."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(slots=True)
class Metrics:
    commands: Counter[str]
    command_errors: Counter[str]
    events: Counter[str]
    api_requests: Counter[str]
    api_errors: Counter[str]

    @classmethod
    def create(cls) -> Metrics:
        return cls(Counter(), Counter(), Counter(), Counter(), Counter())

    def command(self, name: str, success: bool = True) -> None:
        self.commands[name] += 1
        if not success:
            self.command_errors[name] += 1

    def event(self, name: str) -> None:
        self.events[name] += 1

    def api(self, service: str, success: bool = True) -> None:
        self.api_requests[service] += 1
        if not success:
            self.api_errors[service] += 1

    def snapshot(self) -> dict[str, dict[str, int]]:
        return {
            "commands": dict(self.commands),
            "command_errors": dict(self.command_errors),
            "events": dict(self.events),
            "api_requests": dict(self.api_requests),
            "api_errors": dict(self.api_errors),
        }


metrics = Metrics.create()
