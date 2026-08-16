"""
Twitch live announcement system.

Owners can create, list, delete, and test Twitch announcements.
Each announcement is configured interactively and stored in twitch_config.json.
"""

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import discord
from discord.ext import commands, tasks

import checks
from twitch_api import TwitchAPI


logger = logging.getLogger("v-bot")

CONFIG_FILE = Path(__file__).resolve().parent.parent / "twitch_config.json"


class TwitchCog(commands.Cog, name="Twitch"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.twitch = TwitchAPI()
        self.config = self._load_config()
        self.previous_states: dict[str, bool] = {}

        self.check_streams.start()

    def cog_unload(self):
        self.check_streams.cancel()

    # --- Configuration ---

    def _load_config(self) -> dict:
        if not CONFIG_FILE.exists():
            try:
                CONFIG_FILE.write_text("{}", encoding="utf-8")
            except OSError:
                logger.exception("Could not create twitch_config.json")
            return {}

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return {}

            return data

        except (json.JSONDecodeError, OSError):
            logger.exception("Could not load twitch_config.json")
            return {}

    def _save_config(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(self.config, file, indent=4, ensure_ascii=False)
        except OSError:
            logger.exception("Could not save twitch_config.json")

    def _get_guild_announcements(self, guild_id: int) -> list:
        return self.config.setdefault(str(guild_id), [])

    # --- Twitch URL ---

    @staticmethod
    def _extract_username(url: str) -> str | None:
        try:
            parsed = urlparse(url.strip())

            if parsed.scheme not in ("http", "https"):
                return None

            if parsed.netloc.lower() not in (
                "twitch.tv",
                "www.twitch.tv",
            ):
                return None

            path_parts = parsed.path.strip("/").split("/")

            if not path_parts or not path_parts[0]:
                return None

            username = path_parts[0].strip()

            if not username:
                return None

            return username.lower()

        except Exception:
            return None

    # --- Interactive input ---

    async def _wait_for_message(
        self,
        ctx: commands.Context,
        prompt: str,
    ) -> discord.Message | None:
        await ctx.send(
            f"{prompt}\n"
            "⏱️ You have **1 minute** to respond."
        )

        def check(message: discord.Message) -> bool:
            return (
                message.author.id == ctx.author.id
                and message.channel.id == ctx.channel.id
            )

        try:
            return await self.bot.wait_for(
                "message",
                timeout=60,
                check=check,
            )

        except TimeoutError:
            await ctx.send("⏰ Time expired.")
            return None

    async def _ask_channel(
        self,
        ctx: commands.Context,
    ) -> discord.TextChannel | None:
        message = await self._wait_for_message(
            ctx,
            "📢 Send the channel where the Twitch announcement should be sent "
            "(mention the channel).",
        )

        if message is None:
            return None

        channel = None

        if message.channel_mentions:
            channel = message.channel_mentions[0]

        if channel is None:
            await ctx.send(
                "❌ I couldn't find a channel in your message.\n"
                "Use a channel mention such as `#announcements`."
            )
            return None

        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Please select a text channel.")
            return None

        permissions = channel.permissions_for(ctx.guild.me)

        if not permissions.send_messages:
            await ctx.send(
                f"❌ I cannot send messages in {channel.mention}."
            )
            return None

        return channel

    # --- Create announcement ---

    @commands.command(name="create_annonce")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def create_annonce(self, ctx):
        """Creates a Twitch live announcement interactively."""

        twitch_message = await self._wait_for_message(
            ctx,
            "📺 Send the Twitch channel URL.\n"
            "Example: `https://twitch.tv/streamer`",
        )

        if twitch_message is None:
            return

        username = self._extract_username(twitch_message.content)

        if not username:
            await ctx.send(
                "❌ Invalid Twitch URL.\n"
                "Use: `https://twitch.tv/channel`"
            )
            return

        announcement_message = await self._wait_for_message(
            ctx,
            "📝 Send the announcement message.\n\n"
            "Available variables:\n"
            "`{streamer}` — Twitch username\n"
            "`{title}` — stream title\n"
            "`{game}` — category\n"
            "`{viewers}` — viewer count\n"
            "`{url}` — Twitch stream URL",
        )

        if announcement_message is None:
            return

        message_template = announcement_message.content.strip()

        if not message_template:
            await ctx.send("❌ The announcement message cannot be empty.")
            return

        channel = await self._ask_channel(ctx)

        if channel is None:
            return

        announcement = {
            "twitch_username": username,
            "channel_id": channel.id,
            "message": message_template,
        }

        announcements = self._get_guild_announcements(ctx.guild.id)
        announcements.append(announcement)

        self._save_config()

        announcement_id = len(announcements)

        await ctx.send(
            "✅ **Twitch announcement created!**\n\n"
            f"🆔 ID: `{announcement_id}`\n"
            f"📺 Twitch: **{username}**\n"
            f"📢 Channel: {channel.mention}\n"
            f"📝 Message: `{message_template}`"
        )

    # --- List announcements ---

    @commands.command(name="annonces")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def annonces(self, ctx):
        """Lists Twitch announcements configured for this server."""

        announcements = self._get_guild_announcements(ctx.guild.id)

        if not announcements:
            await ctx.send("📭 No Twitch announcements are configured.")
            return

        embed = discord.Embed(
            title="📺 Twitch Announcements",
            color=discord.Color.purple(),
        )

        for index, announcement in enumerate(announcements, start=1):
            channel = ctx.guild.get_channel(
                announcement["channel_id"]
            )

            channel_text = (
                channel.mention
                if channel
                else f"`{announcement['channel_id']}`"
            )

            embed.add_field(
                name=f"#{index} — {announcement['twitch_username']}",
                value=(
                    f"📢 Channel: {channel_text}\n"
                    f"📝 `{announcement['message'][:500]}`"
                ),
                inline=False,
            )

        await ctx.send(embed=embed)

    # --- Delete announcement ---

    @commands.command(name="delete_annonce")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def delete_annonce(self, ctx, announcement_id: int):
        """Deletes a Twitch announcement."""

        announcements = self._get_guild_announcements(ctx.guild.id)

        if announcement_id < 1 or announcement_id > len(announcements):
            await ctx.send("❌ Invalid announcement ID.")
            return

        deleted = announcements.pop(announcement_id - 1)

        self._save_config()

        await ctx.send(
            "🗑️ Twitch announcement deleted.\n"
            f"📺 Twitch: **{deleted['twitch_username']}**"
        )

    # --- Test announcement ---

    @commands.command(name="test_annonce")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def test_annonce(self, ctx, announcement_id: int):
        """Tests a Twitch announcement."""

        announcements = self._get_guild_announcements(ctx.guild.id)

        if announcement_id < 1 or announcement_id > len(announcements):
            await ctx.send("❌ Invalid announcement ID.")
            return

        announcement = announcements[announcement_id - 1]

        channel = ctx.guild.get_channel(
            announcement["channel_id"]
        )

        if not channel:
            await ctx.send("❌ The configured channel no longer exists.")
            return

        stream = await self.twitch.get_stream(
            announcement["twitch_username"]
        )

        if stream:
            data = self._build_message_data(stream)
        else:
            data = {
                "streamer": announcement["twitch_username"],
                "title": "Test stream",
                "game": "Test category",
                "viewers": "0",
                "url": (
                    "https://twitch.tv/"
                    f"{announcement['twitch_username']}"
                ),
            }

        message = self._format_message(
            announcement["message"],
            data,
        )

        await channel.send(message)

        await ctx.send("✅ Test announcement sent.")

    # --- Twitch monitoring ---

    @tasks.loop(seconds=60)
    async def check_streams(self):
        for guild_id, announcements in list(self.config.items()):
            for index, announcement in enumerate(announcements):
                username = announcement.get("twitch_username")

                if not username:
                    continue

                state_key = f"{guild_id}:{index}:{username}"

                try:
                    stream = await self.twitch.get_stream(username)
                    is_live = stream is not None

                    previous = self.previous_states.get(
                        state_key
                    )

                    self.previous_states[state_key] = is_live

                    # First check only initializes the state.
                    if previous is None:
                        continue

                    # Only announce when going from offline -> online.
                    if not previous and is_live:
                        await self._send_announcement(
                            guild_id,
                            announcement,
                            stream,
                        )

                except Exception:
                    logger.exception(
                        f"Error checking Twitch channel '{username}'."
                    )

    @check_streams.before_loop
    async def before_check_streams(self):
        await self.bot.wait_until_ready()

    # --- Announcement ---

    async def _send_announcement(
        self,
        guild_id: str,
        announcement: dict,
        stream: dict,
    ):
        guild = self.bot.get_guild(int(guild_id))

        if not guild:
            return

        channel = guild.get_channel(
            announcement["channel_id"]
        )

        if not channel:
            return

        data = self._build_message_data(stream)

        message = self._format_message(
            announcement["message"],
            data,
        )

        embed = discord.Embed(
            title=f"🔴 {stream['user_name']} is now live!",
            description=stream["title"],
            url=data["url"],
            color=discord.Color.purple(),
        )

        game = stream.get("game_name") or "Unknown"

        embed.add_field(
            name="🎮 Category",
            value=game,
            inline=True,
        )

        embed.add_field(
            name="👀 Viewers",
            value=str(stream["viewer_count"]),
            inline=True,
        )

        thumbnail = stream.get("thumbnail_url")

        if thumbnail:
            thumbnail = thumbnail.replace(
                "{width}",
                "1280",
            ).replace(
                "{height}",
                "720",
            )

            embed.set_image(url=thumbnail)

        embed.set_footer(text="Twitch")

        view = discord.ui.View()

        view.add_item(
            discord.ui.Button(
                label="Watch stream",
                style=discord.ButtonStyle.link,
                url=data["url"],
            )
        )

        await channel.send(
            content=message,
            embed=embed,
            view=view,
        )

    @staticmethod
    def _build_message_data(stream: dict) -> dict:
        username = stream["user_name"]

        return {
            "streamer": username,
            "title": stream.get("title") or "",
            "game": stream.get("game_name") or "Unknown",
            "viewers": str(stream.get("viewer_count", 0)),
            "url": f"https://twitch.tv/{username}",
        }

    @staticmethod
    def _format_message(template: str, data: dict) -> str:
        try:
            return template.format(**data)
        except (KeyError, ValueError):
            return template


async def setup(bot: commands.Bot):
    await bot.add_cog(TwitchCog(bot))
