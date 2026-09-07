"""Bot entry point."""

import asyncio
import logging
import os
import sys

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.log")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, encoding="utf-8")])
logger = logging.getLogger("v-bot")

try:
    import discord
    from discord.ext import commands
    import config
    import checks
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


async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    """Centralized command error handling: never expose internal exception text."""
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
    logger.exception("Unhandled command error in %s", getattr(ctx.command, "qualified_name", "unknown"), exc_info=error)
    await ctx.send("⚠️ An internal error occurred while executing the command.")


bot.on_command_error = on_command_error


async def on_error(event_method: str, *args, **kwargs) -> None:
    logger.exception("Unhandled error in event handler '%s'", event_method)


bot.on_error = on_error

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
    logger.info("Sensitive commands DISABLED - cogs.dangerous not loaded.")


async def main():
    async with bot:
        for extension in EXTENSIONS:
            await bot.load_extension(extension)
            logger.info("Extension loaded: %s", extension)
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
