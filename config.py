"""Centralized bot configuration."""

import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("v-bot")


def _parse_owner_id(raw: str | None, var_name: str) -> int:
    if not raw or not raw.strip():
        logger.critical("%s missing from .env", var_name)
        raise SystemExit(f"{var_name} missing from .env")
    try:
        value = int(raw.strip())
    except ValueError:
        logger.critical("%s is invalid in .env", var_name)
        raise SystemExit(f"{var_name} is invalid in .env")
    if value <= 0:
        logger.critical("%s is invalid in .env", var_name)
        raise SystemExit(f"{var_name} is invalid in .env")
    return value


def _parse_owner_id_list(raw: str | None) -> list[int]:
    ids: list[int] = []
    if not raw or not raw.strip():
        return ids
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit() or int(part) <= 0:
            logger.critical("Invalid secondary owner ID in OWNERS_SECONDARY_IDS.")
            raise SystemExit("OWNERS_SECONDARY_IDS contains an invalid ID")
        value = int(part)
        if value in ids:
            logger.critical("Duplicate secondary owner ID in OWNERS_SECONDARY_IDS.")
            raise SystemExit("OWNERS_SECONDARY_IDS contains a duplicate ID")
        ids.append(value)
    return ids


def _parse_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in ("1", "true", "on", "yes")


TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logger.critical("No token found: add DISCORD_TOKEN to .env file")
    raise SystemExit("DISCORD_TOKEN missing from .env")

OWNER_PRINCIPAL = _parse_owner_id(os.getenv("OWNER_PRINCIPAL_ID"), "OWNER_PRINCIPAL_ID")
OWNERS_SECONDARY = [uid for uid in _parse_owner_id_list(os.getenv("OWNERS_SECONDARY_IDS")) if uid != OWNER_PRINCIPAL]
PERMANENT_OWNERS = [OWNER_PRINCIPAL] + OWNERS_SECONDARY
PERMANENT_OWNERS_SET = frozenset(PERMANENT_OWNERS)

BOT_PREFIX = os.getenv("BOT_PREFIX", "v!").strip() or "v!"
PREFIXES = [BOT_PREFIX, BOT_PREFIX.upper()]

MAX_SPAM = 20
MAX_RAID_AMOUNT = 15
MAX_DMALL_MEMBERS = 500
SNIPE_LIMIT = 15
SNIPE_RETENTION_SECONDS = 15 * 60
TEMP_AUTH_CLEAN_INTERVAL = 10
MENTION_RESPONSE_COOLDOWN = 5
API_CACHE_TTL = 60
API_BACKOFF_MAX = 15 * 60

DANGEROUS_COMMANDS_ENABLED = _parse_bool(os.getenv("DANGEROUS_COMMANDS_ENABLED"), default=False)
VERSION = "3.8.2"
