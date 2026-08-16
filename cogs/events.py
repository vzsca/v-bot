"""
Global bot events + background task.
"""

import logging
import os

import discord
from discord.ext import commands, tasks

import checks
import config
import exceptions
from state import state

logger = logging.getLogger("v-bot")

# File listing connected servers, located at the project root (read by the
# "servers" command in the start_bot.bat panel). This list is no longer logged
# to bot.log/the console to avoid cluttering the logs on every startup.
SERVERS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "servers.txt",
)


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._intents_text: str | None = None  # calculated once (intents do not change)
        self.clean_expired_users.start()

    def cog_unload(self):
        self.clean_expired_users.cancel()

    # --- Background task ---
    @tasks.loop(seconds=config.TEMP_AUTH_CLEAN_INTERVAL)
    async def clean_expired_users(self):
        for uid in state.clean_expired():
            logger.info(f"🔴 User {uid} removed from temporary authorized users.")

    def _write_servers_file(self):
        """Writes the list of connected servers to servers.txt (read by the .bat panel)."""
        try:
            lines = [f"{g.name} (id: {g.id})" for g in self.bot.guilds]
            with open(SERVERS_FILE, "w", encoding="utf-8") as f:
                f.write(f"{len(lines)} connected server(s):\n\n")
                f.write("\n".join(lines))
                f.write("\n")
        except OSError as e:
            logger.warning(f"Unable to write {SERVERS_FILE}: {e}")

    # --- Events ---
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Connected as {self.bot.user} (ID: {self.bot.user.id})")

        if self.bot.user.name != config.BOT_NAME:
            try:
                await self.bot.user.edit(username=config.BOT_NAME)
                logger.info(f"Bot name changed: {config.BOT_NAME}")
            except Exception as e:
                logger.warning(f"Unable to change bot name: {e}")

        try:
            synced = await self.bot.tree.sync()
            logger.info(f"Commands synchronized: {len(synced)}")
        except Exception as e:
            logger.warning(f"Command synchronization error: {e}")

        try:
            await self.bot.change_presence(
                activity=discord.CustomActivity(name=f"Version {config.VERSION}")
            )
        except Exception as e:
            logger.warning(f"Unable to set Discord status: {e}")

        logger.info(f"The bot is connected to {len(self.bot.guilds)} servers.")
        self._write_servers_file()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self._write_servers_file()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self._write_servers_file()

    def _build_intents_text(self) -> str:
        # Intents are fixed at startup: build the string only once
        # instead of rebuilding it every time the bot is mentioned.
        if self._intents_text is None:
            intents = self.bot.intents
            self._intents_text = "\n".join([
                f"• intents.guilds: **{intents.guilds}**",
                f"• intents.members: **{intents.members}**",
                f"• intents.message_content: **{intents.message_content}**",
                f"• intents.messages: **{intents.messages}**",
                f"• intents.reactions: **{intents.reactions}**",
            ])
        return self._intents_text

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        mention = f"<@{self.bot.user.id}>"
        mention_nick = f"<@!{self.bot.user.id}>"

        if not (
            message.content.startswith(mention)
            or message.content.startswith(mention_nick)
        ):
            return

        # Permanent/temporary owners -> detailed embed (intents, Kill Switch,
        # admin status, etc.).
        # Everyone else -> generic message, to avoid exposing operational
        # information to anyone who mentions the bot.
        if checks.is_owner_or_temp(message.author.id):
            await message.channel.send(
                embed=self._build_owner_embed(message)
            )
        else:
            await message.channel.send(
                embed=self._build_general_embed()
            )

    def _build_owner_embed(self, message: discord.Message) -> discord.Embed:
        perms = message.guild.me.guild_permissions if message.guild else None
        has_admin = perms.administrator if perms else False
        kill_status = "🚨 ENABLED" if state.kill_switch else "Disabled"
        color = discord.Color.red() if state.kill_switch else discord.Color.blue()

        embed = discord.Embed(
            title=f"{self.bot.user.name} is operational!",
            color=color,
        )

        embed.add_field(
            name="System status",
            value=(
                f"• Administrator: **{has_admin}**\n"
                f"• Kill Switch: **{kill_status}**\n"
                f"• Prefix: `{config.PREFIXES[0]}`"
            ),
            inline=False,
        )

        embed.add_field(
            name="Security & access",
            value="   ⚠️ Some commands may be restricted for security reasons.",
            inline=False,
        )

        embed.add_field(
            name="Enabled intents",
            value=self._build_intents_text(),
            inline=False,
        )

        embed.set_footer(
            text=f"Request sent by {message.author}",
            icon_url=(
                message.author.avatar.url
                if getattr(message.author, "avatar", None)
                else None
            ),
        )
        return embed

    def _build_general_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"👋 Hi, I'm {self.bot.user.name}!",
            description=f"Use `{config.PREFIXES[0]}help` to see what I can do.",
            color=discord.Color.blue(),
        )
        return embed

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message or message.author.bot:
            return
        if not message.content and not message.attachments:
            return

        data = {
            "type": "delete",
            "content": message.content or "[empty content]",
            "author": str(message.author),
            "author_avatar": message.author.display_avatar.url,
            "time": message.created_at,
            "attachments": (
                [a.url for a in message.attachments]
                if message.attachments
                else []
            ),
        }
        state.add_sniped(message.channel.id, data, config.SNIPE_LIMIT)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(
                "Sorry, this command does not exist. Use `v!help` to see "
                "the list of available commands."
            )

        elif isinstance(error, commands.NoPrivateMessage):
            # discord.py's default message is in English -> replace it
            # with an English message consistent with the rest of the bot.
            await ctx.send(
                "❌ This command cannot be used in private messages."
            )

        elif isinstance(
            error,
            (
                exceptions.NotPermanentOwner,
                exceptions.NotOwnerOrTemp,
                exceptions.NotOwnerOrGuildOwner,
            ),
        ):
            # Permission denial: worth logging (who attempted what),
            # unlike routine blocks (Kill Switch, already running), which
            # are normal bot behavior.
            logger.warning(
                f"Permission denied for '{ctx.command}' "
                f"to {ctx.author} ({ctx.author.id})."
            )
            await ctx.send(str(error))

        elif isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))

        else:
            logger.exception("Command error:", exc_info=error)
            await ctx.send(f"An error occurred: `{error}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
