"""
Configuration centralisée du bot.

Tout ce qui est sensible (token, IDs des owners permanents) vient du fichier
.env et n'apparaît JAMAIS en dur dans le code source. Cela permet de partager
ou versionner le script sans exposer ces informations.
"""

import os
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("v-bot")


# --- Token du bot ---
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logger.critical("Aucun token trouvé : ajoutez DISCORD_TOKEN dans votre fichier .env")
    raise SystemExit("DISCORD_TOKEN manquant dans .env")


def _parse_owner_id(raw: str | None, var_name: str) -> int:
    """Parse un ID owner obligatoire, arrête le bot proprement si invalide/absent."""
    if not raw or not raw.strip():
        logger.critical(f"{var_name} manquant dans .env")
        raise SystemExit(f"{var_name} manquant dans .env")
    try:
        return int(raw.strip())
    except ValueError:
        logger.critical(f"{var_name} invalide dans .env (doit être un ID Discord numérique)")
        raise SystemExit(f"{var_name} invalide dans .env")


def _parse_owner_id_list(raw: str | None) -> list[int]:
    """Parse une liste d'IDs séparés par des virgules. Ignore silencieusement les entrées invalides."""
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
            logger.warning(f"ID owner secondaire ignoré (invalide) : '{part}'")
    return ids


# --- Owners permanents ---
# OWNER_PRINCIPAL : un seul ID, l'owner principal du bot (obligatoire).
# OWNERS_SECONDARY : liste d'IDs supplémentaires, autant que voulu (optionnel).
OWNER_PRINCIPAL: int = _parse_owner_id(os.getenv("OWNER_PRINCIPAL_ID"), "OWNER_PRINCIPAL_ID")
OWNERS_SECONDARY: list[int] = [
    uid for uid in _parse_owner_id_list(os.getenv("OWNERS_SECONDARY_IDS"))
    if uid != OWNER_PRINCIPAL
]

# Liste ordonnée (principal en premier) -> utilisée pour l'affichage (owner_list, etc.)
PERMANENT_OWNERS: list[int] = [OWNER_PRINCIPAL] + OWNERS_SECONDARY

# Set figé -> vérifications de permission en O(1) au lieu d'un parcours de liste.
# L'ajout d'un owner secondaire se fait via start_bot.bat (commande
# add_secondary_owner), qui édite .env directement ; un redémarrage du bot
# recharge cette liste depuis .env.
PERMANENT_OWNERS_SET: frozenset[int] = frozenset(PERMANENT_OWNERS)


# --- Identité du bot ---
BOT_NAME = os.getenv("BOT_NAME", "v-bot").strip()
BOT_PREFIX = os.getenv("BOT_PREFIX", "v!").strip()

if not BOT_PREFIX:
    BOT_PREFIX = "v!"

PREFIXES = [BOT_PREFIX, BOT_PREFIX.upper()]

# --- Réglages généraux du bot ---
MAX_SPAM = 20                 # limite de la commande spam
MAX_RAID_AMOUNT = 15          # limite de la commande raid (rôles/salons créés)
SNIPE_LIMIT = 15              # nombre de messages supprimés gardés en mémoire par salon
TEMP_AUTH_CLEAN_INTERVAL = 10  # secondes entre deux nettoyages des owners temporaires


def _parse_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in ("1", "true", "on", "yes")


# Commandes sensibles (raid, remove_raid, dmall, spam) : DÉSACTIVÉES par défaut.
# Isolées dans cogs/dangerous.py, qui n'est chargé par main.py que si ce flag
# est vrai -> quand c'est désactivé, ces commandes n'existent tout simplement
# pas dans l'arbre de commandes du bot (pas juste bloquées par un check).
# Se bascule depuis le panel start_bot.bat (commande toggle_dangerous), pas
# via Discord, et nécessite un redémarrage du bot pour prendre effet.
DANGEROUS_COMMANDS_ENABLED: bool = _parse_bool(os.getenv("DANGEROUS_COMMANDS_ENABLED"), default=False)

# Version affichée dans le statut Discord du bot (cf. cogs/events.py, on_ready)
# et utilisable ailleurs si besoin. À incrémenter manuellement à chaque
# changement notable -- pas de lien automatique avec git ou autre.

VERSION = os.getenv("BOT_VERSION", "v-bot").strip()
