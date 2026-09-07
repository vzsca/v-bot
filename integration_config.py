"""Per-guild API credential access.

Credentials are stored in .env under guild-specific variable names:
TWITCH_CLIENT_ID_<GUILD_ID>
TWITCH_CLIENT_SECRET_<GUILD_ID>
YOUTUBE_API_KEY_<GUILD_ID>

There is intentionally no global fallback: a server without credentials cannot
use the corresponding integration. This prevents one server's API credentials
from being reused by another server.
"""

import os


def _guild_key(prefix: str, guild_id: int) -> str:
    if not isinstance(guild_id, int) or guild_id <= 0:
        raise ValueError("guild_id must be a positive integer")
    return f"{prefix}_{guild_id}"


def get_twitch_credentials(guild_id: int) -> tuple[str, str] | None:
    client_id = os.getenv(_guild_key("TWITCH_CLIENT_ID", guild_id), "").strip()
    client_secret = os.getenv(_guild_key("TWITCH_CLIENT_SECRET", guild_id), "").strip()
    if not client_id or not client_secret:
        return None
    return client_id, client_secret


def get_youtube_api_key(guild_id: int) -> str | None:
    key = os.getenv(_guild_key("YOUTUBE_API_KEY", guild_id), "").strip()
    return key or None
