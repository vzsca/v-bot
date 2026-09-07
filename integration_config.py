"""Integration credentials with runtime-reloaded, guild-scoped configuration."""

import os
import threading
import time
from pathlib import Path

from dotenv import dotenv_values

import api_access

_ENV_PATH = Path(__file__).resolve().parent / ".env"
_LOCK = threading.RLock()
_ENV_CACHE: dict[str, str] = {}
_ENV_MTIME_NS: int | None = None
_ENV_CHECK_INTERVAL = 2.0
_LAST_ENV_CHECK = 0.0


def _guild_key(prefix: str, guild_id: int) -> str:
    if not isinstance(guild_id, int) or guild_id <= 0:
        raise ValueError("guild_id must be a positive integer")
    return f"{prefix}_{guild_id}"


def _env() -> dict[str, str]:
    global _ENV_MTIME_NS, _LAST_ENV_CHECK, _ENV_CACHE
    now = time.monotonic()
    if now - _LAST_ENV_CHECK < _ENV_CHECK_INTERVAL:
        return _ENV_CACHE
    with _LOCK:
        _LAST_ENV_CHECK = now
        try:
            mtime = _ENV_PATH.stat().st_mtime_ns
        except OSError:
            mtime = None
        if mtime != _ENV_MTIME_NS:
            # Start with process environment for deployments that don't use .env,
            # then let the local .env override it so panel changes take effect.
            merged = dict(os.environ)
            values = dotenv_values(_ENV_PATH)
            merged.update({str(k): str(v).strip() for k, v in values.items() if k and v is not None})
            _ENV_CACHE = merged
            _ENV_MTIME_NS = mtime
        return _ENV_CACHE


def _valid_secret(value: str, minimum: int = 8) -> bool:
    return minimum <= len(value) <= 512 and "\x00" not in value


def get_twitch_credentials(guild_id: int) -> tuple[str, str] | None:
    env = _env()
    if api_access.is_allowed(guild_id):
        client_id = env.get("TWITCH_CLIENT_ID", "").strip()
        client_secret = env.get("TWITCH_CLIENT_SECRET", "").strip()
    else:
        client_id = env.get(_guild_key("TWITCH_CLIENT_ID", guild_id), "").strip()
        client_secret = env.get(_guild_key("TWITCH_CLIENT_SECRET", guild_id), "").strip()
    if not client_id or not _valid_secret(client_id) or not client_secret or not _valid_secret(client_secret):
        return None
    return client_id, client_secret


def get_youtube_api_key(guild_id: int) -> str | None:
    env = _env()
    key = env.get("YOUTUBE_API_KEY", "").strip() if api_access.is_allowed(guild_id) else env.get(_guild_key("YOUTUBE_API_KEY", guild_id), "").strip()
    if not key or not _valid_secret(key):
        return None
    return key
