"""Integration credentials with global and guild-scoped configuration."""

import os
import threading
import time
from pathlib import Path

from dotenv import dotenv_values

import api_access
import api_credentials

_ENV_PATH = Path(__file__).resolve().parent / ".env"
_LOCK = threading.RLock()
_ENV_CACHE: dict[str, str] = {}
_ENV_MTIME_NS: int | None = None
_ENV_CHECK_INTERVAL = 2.0
_LAST_ENV_CHECK = 0.0


def _valid_secret(value: str, minimum: int = 8) -> bool:
    return minimum <= len(value) <= 512 and "\x00" not in value


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
            merged = dict(os.environ)
            values = dotenv_values(_ENV_PATH)
            merged.update({str(k): str(v).strip() for k, v in values.items() if k and v is not None})
            _ENV_CACHE = merged
            _ENV_MTIME_NS = mtime
        return _ENV_CACHE


def get_twitch_credentials(guild_id: int) -> tuple[str, str] | None:
    if api_access.is_allowed(guild_id):
        env = _env()
        client_id = env.get("TWITCH_CLIENT_ID", "").strip()
        client_secret = env.get("TWITCH_CLIENT_SECRET", "").strip()
    else:
        credentials = api_credentials.get(guild_id, "twitch") or {}
        client_id = str(credentials.get("client_id", "")).strip()
        client_secret = str(credentials.get("client_secret", "")).strip()
    if not client_id or not _valid_secret(client_id) or not client_secret or not _valid_secret(client_secret):
        return None
    return client_id, client_secret


def get_youtube_api_key(guild_id: int) -> str | None:
    if api_access.is_allowed(guild_id):
        key = _env().get("YOUTUBE_API_KEY", "").strip()
    else:
        credentials = api_credentials.get(guild_id, "youtube") or {}
        key = str(credentials.get("api_key", "")).strip()
    return key if _valid_secret(key) else None


def is_configured(guild_id: int, platform: str) -> bool:
    if api_access.is_allowed(guild_id):
        return bool(get_twitch_credentials(guild_id) if platform == "twitch" else get_youtube_api_key(guild_id))
    return api_credentials.configured(guild_id, platform)
