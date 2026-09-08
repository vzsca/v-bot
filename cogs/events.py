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
import security_log
from rate_limit import rate_limiter
from security import security
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
        rate_limiter.prune()
        security.prune()
        now = time.monotonic()
        self._mention_cooldowns = {key: expiry for key, expiry in self._mention_cooldowns.items() if expiry > now}

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
    async def on_command_completion(self, ctx):
        command = getattr(ctx.command, "qualified_name", "unknown")
        guild_id = ctx.guild.id if ctx.guild else 0
        channel_id = ctx.channel.id if getattr(ctx.channel, "id", None) else 0
        suspicious = security.record_command(
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=ctx.author.id,
            command=command,
            success=True,
        )
        security_log.log_security_event(
            f"Command executed: guild={guild_id} channel={channel_id} user={ctx.author.id} command={command}"
        )
        if suspicious:
            logger.warning("Suspicious command burst detected: guild=%s user=%s", guild_id, ctx.author.id)

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
        await message.channel.send(embed=self._build_mention_embed(message))

    @staticmethod
    def _has_moderation_access(member: discord.Member) -> bool:
        permissions = member.guild_permissions
        return any(
            getattr(permissions, permission, False)
            for permission in (
                "moderate_members",
                "kick_members",
                "ban_members",
                "manage_messages",
                "manage_channels",
                "manage_roles",
            )
        )

    def _get_mention_role(self, message: discord.Message) -> str:
        if not isinstance(message.author, discord.Member):
            return "member"
        member = message.author
        guild_id = message.guild.id if message.guild else None
        if checks.is_owner_or_temp(member.id, guild_id):
            return "owner"
        if member.guild_permissions.administrator:
            return "admin"
        if self._has_moderation_access(member):
            return "mod"
        return "member"

    def _build_mention_embed(self, message: discord.Message) -> discord.Embed:
        role = self._get_mention_role(message)
        builders = {
            "owner": self._build_owner_embed,
            "admin": self._build_admin_embed,
            "mod": self._build_mod_embed,
            "member": self._build_member_embed,
        }
        return builders[role](message)

    def _base_mention_embed(self, message: discord.Message, title: str, color: discord.Color) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=(
                f"I'm **{self.bot.user.name}**, currently online and ready to help.\n"
                f"Use `{config.PREFIXES[0]}help` to see the commands available to you."
            ),
            color=color,
        )
        embed.set_footer(
            text=f"Requested by {message.author} • v-bot {config.VERSION}",
            icon_url=message.author.display_avatar.url,
        )
        return embed

    def _build_member_embed(self, message: discord.Message) -> discord.Embed:
        embed = self._base_mention_embed(message, f"👋 Hi, {message.author.display_name}!", discord.Color.blue())
        embed.add_field(
            name="✨ What I can do",
            value=(
                "🛡️ **Moderation** — available when you have the required permissions\n"
                "📣 **Twitch / YouTube** — automatic announcements on configured servers\n"
                "🔎 **Information** — server, user and bot information\n"
                "🧹 **Utilities** — deleted-message snipe and other tools"
            ),
            inline=False,
        )
        embed.add_field(
            name="📖 Useful commands",
            value=(
                f"`{config.PREFIXES[0]}help` — browse your available commands\n"
                f"`{config.PREFIXES[0]}help general` — general commands\n"
                f"`{config.PREFIXES[0]}ping` — check my latency"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔗 Need more help?",
            value=(
                f"[📖 Documentation]({DOCS_URL}) • [💬 Support Server]({OFFICIAL_SERVER_URL})\n"
                f"Support: **{SUPPORT_EMAIL}**"
            ),
            inline=False,
        )
        return embed

    def _build_mod_embed(self, message: discord.Message) -> discord.Embed:
        embed = self._base_mention_embed(message, "🛡️ v-bot • Moderation Access", discord.Color.orange())
        embed.add_field(
            name="🔐 Your access",
            value=(
                "You have at least one moderation permission.\n"
                "Each command still checks its exact Discord permission."
            ),
            inline=False,
        )
        embed.add_field(
            name="🛠️ Useful moderation commands",
            value=(
                f"`{config.PREFIXES[0]}help mod` — moderation command list\n"
                f"`{config.PREFIXES[0]}mute @user` — timeout a member\n"
                f"`{config.PREFIXES[0]}kick @user` — remove a member\n"
                f"`{config.PREFIXES[0]}ban @user` — ban a member\n"
                f"`{config.PREFIXES[0]}clear <amount>` — delete messages\n"
                f"`{config.PREFIXES[0]}slowmode <seconds>` — change channel slowmode"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚠️ Important",
            value="Discord role hierarchy and the bot's own permissions still apply to moderation actions.",
            inline=False,
        )
        return embed

    def _build_admin_embed(self, message: discord.Message) -> discord.Embed:
        embed = self._base_mention_embed(message, "⚙️ v-bot • Administrator Access", discord.Color.blurple())
        embed.add_field(
            name="👮 Your access",
            value=(
                "You have the **Administrator** permission.\n"
                "This gives you access to the server administration and announcement features."
            ),
            inline=False,
        )
        embed.add_field(
            name="📢 Useful commands",
            value=(
                f"`{config.PREFIXES[0]}help admin` — admin command list\n"
                f"`{config.PREFIXES[0]}api_status` — check API configuration\n"
                f"`{config.PREFIXES[0]}set_api twitch|yt` — configure integrations\n"
                f"`{config.PREFIXES[0]}create_annonce` — create an automatic announcement\n"
                f"`{config.PREFIXES[0]}annonces` — list configured announcements"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔒 Security",
            value="API secrets are kept out of normal messages and sensitive bot actions may require additional security validation.",
            inline=False,
        )
        return embed

    def _build_owner_embed(self, message: discord.Message) -> discord.Embed:
        perms = message.guild.me.guild_permissions if message.guild and message.guild.me else None
        has_admin = perms.administrator if perms else False
        kill_status = "🚨 ENABLED" if state.kill_switch else "Disabled"
        color = discord.Color.red() if state.kill_switch else discord.Color.gold()
        embed = self._base_mention_embed(message, "👑 v-bot • Owner Access", color)
        embed.add_field(
            name="🟢 System status",
            value=(
                f"• Kill Switch: **{kill_status}**\n"
                f"• Bot Administrator: **{has_admin}**\n"
                f"• Connected servers: **{len(self.bot.guilds)}**\n"
                f"• Prefix: `{config.PREFIXES[0]}`\n"
                f"• Version: **{config.VERSION}**"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛠️ Useful commands",
            value=(
                f"`{config.PREFIXES[0]}help owner` — owner commands\n"
                f"`{config.PREFIXES[0]}killswitch` — emergency bot control\n"
                f"`{config.PREFIXES[0]}owner_list` — view configured owners\n"
                f"`{config.PREFIXES[0]}servers` — server management"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔐 Sensitive actions",
            value=(
                "Some high-impact commands require a one-time 6-digit security code. "
                "Generate one locally with `action_code`, then send it when the bot asks for validation."
            ),
            inline=False,
        )
        return embed

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
            security.record_command(guild_id=ctx.guild.id if ctx.guild else 0, channel_id=ctx.channel.id, user_id=ctx.author.id, command=getattr(ctx.command, "qualified_name", "unknown"), success=False)
            await ctx.send(str(error))
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))
        else:
            logger.exception("Command error", exc_info=error)
            await ctx.send("An internal error occurred while processing this command.")


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
