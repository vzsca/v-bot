"""
Bot entry point.
"""

import asyncio
import logging
import os
import sys

# Logs are sent both to the console and bot.log (used by the
# "logs" command in the start_bot.bat panel). Configured FIRST, before
# importing config/checks, so that any configuration error (.env missing,
# empty token, invalid owner ID, etc.) that would otherwise occur before
# logging is ready is captured in bot.log.
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
    logger.critical(f"Bot could not start (invalid configuration): {e}")
    sys.exit(1)
except Exception:
    logger.exception("Unexpected error while loading the configuration.")
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
    Safety net for ALL errors that do not go through
    on_command_error -- meaning any exception raised in an event
    handler (on_message, on_guild_join, etc.) rather than in a command.

    Important: unlike other events (on_message, on_ready...), on_error
    is NOT dispatched through discord.py's Cog.listener() system -- it
    is called directly as a bot method (`self.on_error(...)` in
    _run_event). A @commands.Cog.listener() for "on_error" would therefore
    NEVER be triggered; it must be overridden here on the bot instance
    for this safety net to actually work.
    """
    logger.exception(f"Unhandled error in event handler '{event_method}' (args={args!r})")


bot.on_error = on_error

# --- Extensions to load ---
EXTENSIONS = [
    "cogs.events",
    "cogs.moderation",
    "cogs.info",
    "cogs.owner",
    "cogs.help_cog",
    "cogs.annonce",
    "cogs.twitch",
    "cogs.youtube",
]

if config.DANGEROUS_COMMANDS_ENABLED:
    EXTENSIONS.append("cogs.dangerous")
    logger.warning("Sensitive commands ENABLED (raid, remove_raid, dmall, spam).")
else:
    logger.info("Sensitive commands DISABLED (raid, remove_raid, dmall, spam) - cogs.dangerous not loaded.")


async def main():
    async with bot:
        for extension in EXTENSIONS:
            await bot.load_extension(extension)
            logger.info(f"Extension loaded: {extension}")
        await bot.start(config.TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except discord.LoginFailure:
        logger.critical("Discord login failed: the token in .env is invalid or empty.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped (Ctrl+C).")
    except Exception:
        logger.exception("The bot stopped due to an unhandled error.")
        sys.exit(1)
