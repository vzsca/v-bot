"""
Point d'entrée du bot.
"""

import asyncio
import logging
import os
import sys

# Logs envoyés à la fois sur la console et dans bot.log (utilisé par la
# commande "logs" du panel start_bot.bat). Configuré en TOUT PREMIER, avant
# d'importer config/checks, pour capturer dans bot.log une éventuelle erreur
# de configuration (.env manquant, token vide, ID owner invalide...) qui se
# produirait sinon avant que la journalisation ne soit prête.
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("v-bot")

try:
    import discord
    from discord.ext import commands

    import config
    import checks
except SystemExit as e:
    logger.critical(f"Le bot n'a pas pu démarrer (configuration invalide) : {e}")
    sys.exit(1)
except Exception:
    logger.exception("Erreur inattendue pendant le chargement de la configuration.")
    sys.exit(1)

# --- Intents ---
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True
intents.reactions = True

# --- Bot ---
bot = commands.Bot(command_prefix=config.PREFIXES, intents=intents, help_command=None)
bot.add_check(checks.global_check)


async def on_error(event_method: str, *args, **kwargs) -> None:
    """
    Filet de sécurité pour TOUTES les erreurs qui ne passent pas par
    on_command_error -- c'est-à-dire toute exception levée dans un event
    handler (on_message, on_guild_join, etc.) plutôt que dans une commande.

    Important : contrairement aux autres events (on_message, on_ready...),
    on_error N'EST PAS dispatché via le système de Cog.listener() de
    discord.py -- il est appelé directement comme méthode du bot
    (`self.on_error(...)` dans _run_event). Un @commands.Cog.listener()
    pour "on_error" ne serait donc JAMAIS déclenché ; il faut l'overrider
    ici, sur l'instance du bot, pour que ce filet existe vraiment.
    """
    logger.exception(f"Erreur non gérée dans l'event handler '{event_method}' (args={args!r})")


bot.on_error = on_error

# --- Cogs à charger ---
EXTENSIONS = [
    "cogs.events",
    "cogs.moderation",
    "cogs.info",
    "cogs.owner",
    "cogs.help_cog",
]

if config.DANGEROUS_COMMANDS_ENABLED:
    EXTENSIONS.append("cogs.dangerous")
    logger.warning("Commandes sensibles ACTIVEES (raid, remove_raid, dmall, spam).")
else:
    logger.info("Commandes sensibles DESACTIVEES (raid, remove_raid, dmall, spam) - cogs.dangerous non charge.")


async def main():
    async with bot:
        for extension in EXTENSIONS:
            await bot.load_extension(extension)
            logger.info(f"Extension chargée : {extension}")
        await bot.start(config.TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except discord.LoginFailure:
        logger.critical("Connexion à Discord refusée : le token dans .env est invalide ou vide.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot arrêté (Ctrl+C).")
    except Exception:
        logger.exception("Le bot s'est arrêté à cause d'une erreur non gérée.")
        sys.exit(1)
