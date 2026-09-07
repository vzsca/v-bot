"""Integration credentials with shared panel access or per-guild credentials."""

import os

import api_access


def _guild_key(prefix: str, guild_id: int) -> str:
    if not isinstance(guild_id, int) or guild_id <= 0:
        raise ValueError("guild_id must be a positive integer")
    return f"{prefix}_{guild_id}"


def get_twitch_credentials(guild_id: int) -> tuple[str, str] | None:
    if api_access.is_allowed(guild_id):
        client_id = os.getenv("TWITCH_CLIENT_ID", "").strip()
        client_secret = os.getenv("TWITCH_CLIENT_SECRET", "").strip()
    else:
        client_id = os.getenv(_guild_key("TWITCH_CLIENT_ID", guild_id), "").strip()
        client_secret = os.getenv(_guild_key("TWITCH_CLIENT_SECRET", guild_id), "").strip()
    if not client_id or not client_secret:
        return None
    return client_id, client_secret


def get_youtube_api_key(guild_id: int) -> str | None:
    if api_access.is_allowed(guild_id):
        key = os.getenv("YOUTUBE_API_KEY", "").strip()
    else:
        key = os.getenv(_guild_key("YOUTUBE_API_KEY", guild_id), "").strip()
    return key or None
