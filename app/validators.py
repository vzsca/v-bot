"""Strict validators shared by commands and integrations."""

from __future__ import annotations

import re

DISCORD_ID_RE = re.compile(r"^[1-9]\d{16,20}$")


def discord_id(value: str | int) -> int:
    """Validate and return a Discord snowflake-like ID."""
    text = str(value).strip()
    if not DISCORD_ID_RE.fullmatch(text):
        raise ValueError("Invalid Discord ID")
    result = int(text)
    if result <= 0:
        raise ValueError("Invalid Discord ID")
    return result


def bounded_text(value: str, *, minimum: int = 1, maximum: int = 2000) -> str:
    text = str(value).strip()
    if not minimum <= len(text) <= maximum:
        raise ValueError(f"Text length must be between {minimum} and {maximum}")
    if "\x00" in text:
        raise ValueError("Text contains an invalid character")
    return text
