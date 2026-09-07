"""
Global bot events + background tasks.
"""

import logging
import os
import time

import discord
from discord.ext import commands, tasks

import checks
import config
import exceptions
from state import state

logger = logging.getLogger("v-bot")
SERVERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "servers.txt")

GITHUB_URL = "https://github.com/vzsca/v-bot"
DOCS_URL = "https://github.com/vzsca/v-bot/blob/main/README.md"
TERMS_URL = "https://github.com/vzsca/v-bot/blob/main/TERMS_OF_USE.md"
PRIVACY_URL = "https://github.com/vzsca/v-bot/blob/main/PRIVACY_POLICY.md"
OFFICIAL_SERVER_URL = "https://discord.gg/vgvFA7NJHg"
OFFICIAL_BOT_URL = "https://discord.com/oauth2/authorize?client_id=1335588735794024499"
SUPPORT_EMAIL = "support.v.bot@gmail.com"


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._intents_text: str | None = None
        self._mention_cooldowns: dict[tuple[int, int], float] = {}
        self.clean_expired_users.start()
        self.clean_snipes.start()

    def cog_unload(self):
        self.clean_expired_users.cancel()
        self.clean_snipes.cancel()

    @tasks.loop(seconds=config.TEMP_AUTH_CLEAN_INTERVAL)
    async def clean_expired_users(self):
        for guild_id, user_id in state.clean_expired():
            logger.info("Temporary authorization expired: guild=%s user=%s", guild_id, user_id)

    @tasks.loop(seconds=60)
    async def clean_snipes(self):
        state.clean_snipes(config.SNIPE_RETENTION_SECONDS)
        now = time.time()
        self._mention_cooldowns = {
            key: expiry for key, expiry in self._mention_cooldowns.items() if expiry > now
        }

    def _write_servers_file(self):
        try:
            lines = [f"{g.name} (id: {g.id})" for g in self.bot.guilds]
            with open(SERVERS_FILE, "w", encoding="utf-8") as f:
                f.write(f"{len(lines)} connected server(s):\n\n")
                f.write("\n".join(lines))
                f.write("\n")
        except OSError as e:
            logger.warning("Unable to write %s: %s", SERVERS_FILE, e)

    def _build_intents_text(self) -> str:
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
    async def on_ready(self):
        logger.info("Connected as %s (ID: %s)", self.bot.user, self.bot.user.id)
        # Sync once per process instead of on every Discord READY/reconnect.
        if not getattr(self.bot, "_commands_synced", False):
            try:
                synced = await self.bot.tree.sync()
                self.bot._commands_synced = True
                logger.info("Commands synchronized: %s", len(synced))
            except Exception:
                logger.exception("Command synchronization error")
        try:
            await self.bot.change_presence(activity=discord.CustomActivity(name=f"Version {config.VERSION}"))
        except Exception:
            logger.exception("Unable to set Discord status")
        logger.info("The bot is connected to %s servers.", len(self.bot.guilds))
        self._write_servers_file()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        logger.info("Guild join: %s (%s)", guild.name, guild.id)
        self._write_servers_file()
        embed = discord.Embed(
            title="🤖 Thanks for adding v-bot!",
            description=(f"**v-bot** has successfully joined **{guild.name}**!\n\n"
                         "v-bot is a personal, modular, and security-focused Discord bot designed for moderation, "
                         "server management, owner controls, security systems, and more.\n\n"
                         "You can find the source code, documentation, legal information, and official support below."),
            color=discord.Color.blurple(),
        )
        embed.add_field(name="🔗 Official Links", value=(
            f"[🤖 Add v-bot]({OFFICIAL_BOT_URL}) • [💻 GitHub]({GITHUB_URL}) • [📖 Documentation]({DOCS_URL})\n"
            f"[📜 Terms of Use]({TERMS_URL}) • [🔒 Privacy Policy]({PRIVACY_URL})"), inline=False)
        embed.add_field(name="💬 Support", value=(f"Need help with v-bot?\nJoin our [official Discord server]({OFFICIAL_SERVER_URL}) "
                                                   f"or contact **{SUPPORT_EMAIL}**."), inline=False)
        embed.set_footer(text=f"v-bot • Version {config.VERSION}")
        me = guild.me
        if me is None:
            return
        for channel in guild.text_channels:
            permissions = channel.permissions_for(me)
            if not permissions.view_channel or not permissions.send_messages:
                continue
            try:
                await channel.send(embed=embed)
                break
            except discord.Forbidden:
                continue
            except discord.HTTPException as e:
                logger.warning("Unable to send guild join message in %s: %s", guild.id, e)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self._write_servers_file()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or not self.bot.user:
            return
        mention = f"<@{self.bot.user.id}>"
        mention_nick = f"<@!{self.bot.user.id}>"
        if not (message.content.startswith(mention) or message.content.startswith(mention_nick)):
            return
        key = (message.guild.id if message.guild else 0, message.author.id)
        now = time.monotonic()
        if self._mention_cooldowns.get(key, 0) > now:
            return
        self._mention_cooldowns[key] = now + config.MENTION_RESPONSE_COOLDOWN
        if checks.is_owner_or_temp(message.author.id, message.guild.id if message.guild else None):
            await message.channel.send(embed=self._build_owner_embed(message))
        else:
            await message.channel.send(embed=self._build_general_embed())

    def _build_owner_embed(self, message: discord.Message) -> discord.Embed:
        perms = message.guild.me.guild_permissions if message.guild and message.guild.me else None
        has_admin = perms.administrator if perms else False
        kill_status = "🚨 ENABLED" if state.kill_switch else "Disabled"
        color = discord.Color.red() if state.kill_switch else discord.Color.blue()
        embed = discord.Embed(title=f"{self.bot.user.name} is operational!", color=color)
        embed.add_field(name="System status", value=(f"• Administrator: **{has_admin}**\n"
                                                      f"• Kill Switch: **{kill_status}**\n"
                                                      f"• Prefix: `{config.PREFIXES[0]}`"), inline=False)
        embed.add_field(name="Security & access", value="⚠️ Some commands may be restricted for security reasons.", inline=False)
        embed.add_field(name="Enabled intents", value=self._build_intents_text(), inline=False)
        embed.set_footer(text=f"Request sent by {message.author}", icon_url=message.author.avatar.url if getattr(message.author, "avatar", None) else None)
        return embed

    def _build_general_embed(self) -> discord.Embed:
        return discord.Embed(title=f"👋 Hi, I'm {self.bot.user.name}!",
                              description=f"Use `{config.PREFIXES[0]}help` to see what I can do.",
                              color=discord.Color.blue())

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message or message.author.bot or (not message.content and not message.attachments):
            return
        data = {
            "type": "delete",
            "content": message.content or "[empty content]",
            "author": str(message.author),
            "author_avatar": message.author.display_avatar.url,
            "time": message.created_at,
            "attachments": [a.url for a in message.attachments] if message.attachments else [],
        }
        state.add_sniped(message.channel.id, data, config.SNIPE_LIMIT)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Sorry, this command does not exist. Use `v!help` to see the list of available commands.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ This command cannot be used in private messages.")
        elif isinstance(error, (exceptions.NotPermanentOwner, exceptions.NotOwnerOrTemp, exceptions.NotOwnerOrGuildOwner)):
            logger.warning("Permission denied for '%s' to %s (%s).", ctx.command, ctx.author, ctx.author.id)
            await ctx.send(str(error))
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))
        else:
            logger.exception("Command error", exc_info=error)
            await ctx.send("An internal error occurred while processing this command.")


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
