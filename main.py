"""Bot entry point."""

import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

LOG_FILE = os.path.join(ROOT, "bot.log")
_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), _handler],
)
logger = logging.getLogger("v-bot")

try:
    import checks
    import config
    import discord
    from discord.ext import commands
    from extensions import get_extensions, is_dangerous_extension
except SystemExit as e:
    logger.critical("Bot could not start (invalid configuration): %s", e)
    sys.exit(1)
except Exception:
    logger.exception("Unexpected error while loading the configuration.")
    sys.exit(1)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix=config.PREFIXES, intents=intents, help_command=None)
bot.add_check(checks.global_check)


async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send(str(error) or "❌ You do not have permission to use this command.")
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: `{error.param.name}`.")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument. Check the command usage and try again.")
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Please wait {error.retry_after:.1f}s before trying again.")
        return
    logger.error(
        "Unhandled command error in %s",
        getattr(ctx.command, "qualified_name", "unknown"),
        exc_info=(type(error), error, error.__traceback__),
    )
    try:
        await ctx.send("⚠️ An internal error occurred while executing the command.")
    except discord.HTTPException:
        logger.exception("Could not report command error to Discord.")


bot.on_command_error = on_command_error


async def on_error(event_method, *args, **kwargs):
    logger.error("Unhandled error in event handler '%s'", event_method, exc_info=sys.exc_info())


bot.on_error = on_error


async def main():
    extensions = get_extensions(config.DANGEROUS_COMMANDS_ENABLED)
    if config.DANGEROUS_COMMANDS_ENABLED:
        logger.warning("Sensitive commands ENABLED with safety confirmations and guild-scoped cleanup.")
    else:
        logger.info("Sensitive commands DISABLED - no sensitive cog loaded.")

    async with bot:
        for extension in extensions:
            await bot.load_extension(extension)
            logger.info("Extension loaded: %s", extension)
            if is_dangerous_extension(extension):
                logger.warning("Loaded sensitive extension: %s", extension)
        await bot.start(config.TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except discord.LoginFailure:
        logger.critical("Discord login failed: token is invalid or empty.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped (Ctrl+C).")
    except Exception:
        logger.exception("The bot stopped due to an unhandled error.")
        sys.exit(1)
