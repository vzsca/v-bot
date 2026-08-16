"""
Centralized bot configuration.

Everything sensitive (token, permanent owner IDs) comes from the .env file
and is NEVER hardcoded into the source code. This makes it possible to share
or version the script without exposing this information.
"""

import os
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("v-bot")


# --- Bot token ---
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logger.critical("No token found: add DISCORD_TOKEN to your .env file")
    raise SystemExit("DISCORD_TOKEN missing from .env")


def _parse_owner_id(raw: str | None, var_name: str) -> int:
    """Parses a required owner ID and cleanly stops the bot if it is invalid or missing."""
    if not raw or not raw.strip():
        logger.critical(f"{var_name} missing from .env")
        raise SystemExit(f"{var_name} missing from .env")
    try:
        return int(raw.strip())
    except ValueError:
        logger.critical(f"{var_name} is invalid in .env (must be a numeric Discord ID)")
        raise SystemExit(f"{var_name} is invalid in .env")


def _parse_owner_id_list(raw: str | None) -> list[int]:
    """Parses a comma-separated list of IDs. Invalid entries are silently ignored."""
    ids: list[int] = []
    if not raw:
        return ids
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            logger.warning(f"Invalid secondary owner ID ignored: '{part}'")
    return ids


# --- Permanent owners ---
# OWNER_PRINCIPAL: a single ID, the bot's principal owner (required).
# OWNERS_SECONDARY: list of additional IDs, as many as needed (optional).
OWNER_PRINCIPAL: int = _parse_owner_id(os.getenv("OWNER_PRINCIPAL_ID"), "OWNER_PRINCIPAL_ID")
OWNERS_SECONDARY: list[int] = [
    uid for uid in _parse_owner_id_list(os.getenv("OWNERS_SECONDARY_IDS"))
    if uid != OWNER_PRINCIPAL
]

# Ordered list (principal first) -> used for display (owner_list, etc.)
PERMANENT_OWNERS: list[int] = [OWNER_PRINCIPAL] + OWNERS_SECONDARY

# Frozen set -> O(1) permission checks instead of iterating through a list.
# Adding a secondary owner is done through start_bot.bat (add_secondary_owner
# command), which edits .env directly; restarting the bot reloads this list
# from .env.
PERMANENT_OWNERS_SET: frozenset[int] = frozenset(PERMANENT_OWNERS)

# --- Twitch API ---
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "").strip()
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "").strip()

# --- Bot identity ---
BOT_NAME = os.getenv("BOT_NAME", "v-bot").strip()
BOT_PREFIX = os.getenv("BOT_PREFIX", "v!").strip()

if not BOT_PREFIX:
    BOT_PREFIX = "v!"

PREFIXES = [BOT_PREFIX, BOT_PREFIX.upper()]

# --- General bot settings ---
MAX_SPAM = 20                  # spam command limit
MAX_RAID_AMOUNT = 15           # raid command limit (roles/channels created)
SNIPE_LIMIT = 15               # number of deleted messages kept in memory per channel
TEMP_AUTH_CLEAN_INTERVAL = 10  # seconds between temporary owner cleanup cycles


def _parse_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in ("1", "true", "on", "yes")


# Sensitive commands (raid, remove_raid, dmall, spam): DISABLED by default.
# Isolated in cogs/dangerous.py, which is only loaded by main.py if this flag
# is true -> when disabled, these commands simply do not exist in the bot's
# command tree (they are not merely blocked by a check).
# Toggled from the start_bot.bat panel (toggle_dangerous command), not via
# Discord, and requires a bot restart to take effect.
DANGEROUS_COMMANDS_ENABLED: bool = _parse_bool(
    os.getenv("DANGEROUS_COMMANDS_ENABLED"),
    default=False,
)

# Version displayed in the bot's Discord status (see cogs/events.py, on_ready)
# and available elsewhere if needed. Must be manually incremented after each
# notable change -- it is not automatically linked to git or anything else.

VERSION = "3.8.1"
