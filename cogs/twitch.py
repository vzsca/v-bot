"""
Twitch integration and automatic stream announcements.

This cog handles:
- Twitch API authentication
- Automatic live detection
- Automatic stream announcements
- Creating announcements
- Listing announcements
- Testing announcements
- Deleting announcements

Configuration is stored in twitch_config.json.
"""

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
import discord
from discord.ext import commands, tasks

import checks
import config

logger = logging.getLogger("v-bot")

TWITCH_CONFIG_FILE = (
    Path(__file__).resolve().parent.parent / "twitch_config.json"
)


class TwitchCog(commands.Cog, name="Twitch"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.twitch_access_token: str | None = None

        self._ensure_config_file()
        self.twitch_task.start()

    def cog_unload(self):
        self.twitch_task.cancel()

    # ==========================================================
    # Configuration
    # ==========================================================

    def _ensure_config_file(self) -> None:
        """Create twitch_config.json if it does not exist."""
        if TWITCH_CONFIG_FILE.exists():
            return

        try:
            with open(TWITCH_CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(
                    {"announcements": []},
                    file,
                    indent=4,
                    ensure_ascii=False,
                )
        except OSError:
            logger.exception("Unable to create twitch_config.json.")

    def _load_config(self) -> dict:
        """Load Twitch configuration."""
        self._ensure_config_file()

        try:
            with open(TWITCH_CONFIG_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return {"announcements": []}

            if not isinstance(data.get("announcements"), list):
                data["announcements"] = []

            return data

        except (OSError, json.JSONDecodeError):
            logger.exception("Unable to load twitch_config.json.")
            return {"announcements": []}

    def _save_config(self, data: dict) -> bool:
        """Save Twitch configuration."""
        try:
            with open(TWITCH_CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )
            return True

        except OSError:
            logger.exception("Unable to save twitch_config.json.")
            return False

    # ==========================================================
    # Twitch URL
    # ==========================================================

    @staticmethod
    def _extract_twitch_login(twitch_url: str) -> str | None:
        """Extract the Twitch username from a Twitch channel URL."""
        try:
            parsed = urlparse(twitch_url.strip())

            if parsed.scheme not in ("http", "https"):
                return None

            if parsed.netloc.lower() not in {
                "twitch.tv",
                "www.twitch.tv",
            }:
                return None

            path = parsed.path.strip("/")

            if not path:
                return None

            login = path.split("/")[0].lower()

            # Avoid accepting Twitch special pages.
            if login in {
                "directory",
                "downloads",
                "jobs",
                "p",
                "search",
                "settings",
                "subscriptions",
                "videos",
            }:
                return None

            return login

        except Exception:
            return None

    # ==========================================================
    # Twitch API
    # ==========================================================

    async def _get_access_token(
        self,
        session: aiohttp.ClientSession,
    ) -> str | None:
        """Get an application access token from Twitch."""

        if (
            not config.TWITCH_CLIENT_ID
            or not config.TWITCH_CLIENT_SECRET
        ):
            logger.warning(
                "Twitch API credentials are missing. "
                "Set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET in .env."
            )
            return None

        try:
            async with session.post(
                "https://id.twitch.tv/oauth2/token",
                params={
                    "client_id": config.TWITCH_CLIENT_ID,
                    "client_secret": config.TWITCH_CLIENT_SECRET,
                    "grant_type": "client_credentials",
                },
            ) as response:

                if response.status != 200:
                    logger.error(
                        "Unable to obtain Twitch access token "
                        f"(HTTP {response.status})."
                    )
                    return None

                data = await response.json()
                token = data.get("access_token")

                if not token:
                    logger.error(
                        "Twitch did not return an access token."
                    )
                    return None

                self.twitch_access_token = token
                return token

        except aiohttp.ClientError:
            logger.exception(
                "Twitch authentication request failed."
            )
            return None

    async def _get_stream_data(
        self,
        session: aiohttp.ClientSession,
        twitch_login: str,
    ) -> dict | None:
        """Return current Twitch stream data, or None if offline."""

        if not self.twitch_access_token:
            self.twitch_access_token = await self._get_access_token(
                session
            )

        if not self.twitch_access_token:
            return None

        headers = {
            "Client-Id": config.TWITCH_CLIENT_ID,
            "Authorization": (
                f"Bearer {self.twitch_access_token}"
            ),
        }

        try:
            async with session.get(
                "https://api.twitch.tv/helix/streams",
                headers=headers,
                params={
                    "user_login": twitch_login,
                },
            ) as response:

                if response.status == 401:
                    self.twitch_access_token = None
                    return None

                if response.status != 200:
                    logger.warning(
                        f"Twitch API returned HTTP {response.status} "
                        f"for channel {twitch_login}."
                    )
                    return None

                data = await response.json()
                streams = data.get("data", [])

                if not streams:
                    return None

                stream = streams[0]

                return {
                    "streamer": twitch_login,
                    "title": stream.get("title", ""),
                    "game": stream.get("game_name", ""),
                    "url": f"https://www.twitch.tv/{twitch_login}",
                }

        except aiohttp.ClientError:
            logger.exception(
                f"Unable to get Twitch stream data: {twitch_login}"
            )
            return None

    # ==========================================================
    # Announcement helpers
    # ==========================================================

    @staticmethod
    def _format_message(
        message: str,
        stream_data: dict,
    ) -> str:
        """Replace supported placeholders in an announcement."""
        return (
            message
            .replace(
                "{streamer}",
                str(stream_data.get("streamer", "")),
            )
            .replace(
                "{title}",
                str(stream_data.get("title", "")),
            )
            .replace(
                "{game}",
                str(stream_data.get("game", "")),
            )
            .replace(
                "{url}",
                str(stream_data.get("url", "")),
            )
        )

    async def _send_announcement(
        self,
        announcement: dict,
        stream_data: dict | None = None,
    ) -> bool:
        """Send an announcement to its configured Discord channel."""

        channel_id = announcement.get("channel_id")
        message = announcement.get("message")
        twitch_url = announcement.get("twitch_url")

        if not channel_id or not message or not twitch_url:
            return False

        twitch_login = self._extract_twitch_login(twitch_url)

        if not twitch_login:
            return False

        channel = self.bot.get_channel(int(channel_id))

        if channel is None:
            return False

        if stream_data is None:
            stream_data = {
                "streamer": twitch_login,
                "title": "",
                "game": "",
                "url": twitch_url,
            }

        formatted_message = self._format_message(
            message,
            stream_data,
        )

        try:
            await channel.send(formatted_message)
            return True

        except discord.Forbidden:
            logger.warning(
                f"Missing permission to send messages in channel "
                f"{channel_id}."
            )
            return False

        except discord.HTTPException:
            logger.exception(
                f"Failed to send Twitch announcement for "
                f"{twitch_login}."
            )
            return False

    # ==========================================================
    # create_annonce
    # ==========================================================

    @commands.command(name="create_annonce")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def create_annonce(self, ctx):
        """
        Create a Twitch stream announcement.

        The bot asks for:
        1. Twitch channel URL
        2. Announcement message
        3. Discord channel
        """

        def check(message: discord.Message) -> bool:
            return (
                message.author.id == ctx.author.id
                and message.channel.id == ctx.channel.id
            )

        # ------------------------------------------------------
        # Twitch URL
        # ------------------------------------------------------

        await ctx.send(
            "📺 **Create Twitch announcement**\n\n"
            "Send the Twitch channel URL.\n"
            "You have **1 minute**."
        )

        try:
            response = await self.bot.wait_for(
                "message",
                timeout=60,
                check=check,
            )
        except TimeoutError:
            await ctx.send("⏰ Time expired.")
            return

        twitch_url = response.content.strip()
        twitch_login = self._extract_twitch_login(twitch_url)

        if not twitch_login:
            await ctx.send(
                "❌ Invalid Twitch channel URL.\n"
                "Example: `https://www.twitch.tv/example`"
            )
            return

        # ------------------------------------------------------
        # Announcement message
        # ------------------------------------------------------

        await ctx.send(
            "💬 **Send the announcement message.**\n"
            "You have **1 minute**.\n\n"
            "Available placeholders:\n"
            "`{streamer}` → Twitch username\n"
            "`{title}` → Stream title\n"
            "`{game}` → Stream category\n"
            "`{url}` → Twitch stream URL"
        )

        try:
            response = await self.bot.wait_for(
                "message",
                timeout=60,
                check=check,
            )
        except TimeoutError:
            await ctx.send("⏰ Time expired.")
            return

        announcement_message = response.content.strip()

        if not announcement_message:
            await ctx.send(
                "❌ The announcement message cannot be empty."
            )
            return

        # ------------------------------------------------------
        # Discord channel
        # ------------------------------------------------------

        await ctx.send(
            "📢 **Mention the Discord channel where the announcement "
            "should be sent.**\n"
            "You have **1 minute**.\n\n"
            "Example: `#announcements`"
        )

        def channel_check(message: discord.Message) -> bool:
            return (
                message.author.id == ctx.author.id
                and message.channel.id == ctx.channel.id
                and bool(message.channel_mentions)
            )

        try:
            response = await self.bot.wait_for(
                "message",
                timeout=60,
                check=channel_check,
            )
        except TimeoutError:
            await ctx.send("⏰ Time expired.")
            return

        target_channel = response.channel_mentions[0]

        # ------------------------------------------------------
        # Save announcement
        # ------------------------------------------------------

        twitch_config = self._load_config()

        announcement_id = 1

        existing_ids = [
            announcement.get("id")
            for announcement in twitch_config["announcements"]
            if isinstance(announcement.get("id"), int)
        ]

        if existing_ids:
            announcement_id = max(existing_ids) + 1

        announcement = {
            "id": announcement_id,
            "twitch_url": twitch_url,
            "message": announcement_message,
            "channel_id": target_channel.id,
            "was_live": False,
        }

        twitch_config["announcements"].append(announcement)

        if not self._save_config(twitch_config):
            await ctx.send(
                "❌ Failed to save the Twitch announcement."
            )
            return

        embed = discord.Embed(
            title="✅ Twitch announcement created",
            color=discord.Color.green(),
        )

        embed.add_field(
            name="ID",
            value=f"`{announcement_id}`",
            inline=True,
        )

        embed.add_field(
            name="Twitch",
            value=twitch_url,
            inline=True,
        )

        embed.add_field(
            name="Discord channel",
            value=target_channel.mention,
            inline=True,
        )

        embed.add_field(
            name="Message",
            value=announcement_message,
            inline=False,
        )

        await ctx.send(embed=embed)

    # ==========================================================
    # annonces
    # ==========================================================

    @commands.command(name="annonces")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def annonces(self, ctx):
        """List all configured Twitch announcements."""

        twitch_config = self._load_config()
        announcements = twitch_config.get("announcements", [])

        if not announcements:
            await ctx.send(
                "📭 No Twitch announcements are configured."
            )
            return

        embed = discord.Embed(
            title="📺 Twitch announcements",
            description=(
                f"**{len(announcements)}** announcement(s) configured."
            ),
            color=discord.Color.purple(),
        )

        for announcement in announcements:
            announcement_id = announcement.get("id", "?")
            twitch_url = announcement.get(
                "twitch_url",
                "Unknown",
            )
            channel_id = announcement.get("channel_id")
            message = announcement.get(
                "message",
                "No message",
            )

            discord_channel = (
                f"<#{channel_id}>"
                if channel_id
                else "Unknown"
            )

            twitch_login = self._extract_twitch_login(
                twitch_url
            )

            status = (
                "🟢 LIVE"
                if announcement.get("was_live", False)
                else "⚫ Offline"
            )

            embed.add_field(
                name=f"#{announcement_id} — {twitch_login or 'Unknown'}",
                value=(
                    f"**Twitch:** {twitch_url}\n"
                    f"**Channel:** {discord_channel}\n"
                    f"**Status:** {status}\n"
                    f"**Message:** {message}"
                ),
                inline=False,
            )

        await ctx.send(embed=embed)

    # ==========================================================
    # test_annonce
    # ==========================================================

    @commands.command(name="test_annonce")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def test_annonce(self, ctx, announcement_id: int):
        """Test a Twitch announcement."""

        twitch_config = self._load_config()

        announcement = next(
            (
                item
                for item in twitch_config["announcements"]
                if item.get("id") == announcement_id
            ),
            None,
        )

        if announcement is None:
            await ctx.send(
                f"❌ Announcement `{announcement_id}` not found."
            )
            return

        success = await self._send_announcement(
            announcement
        )

        if success:
            await ctx.send(
                f"✅ Test announcement `{announcement_id}` sent."
            )
        else:
            await ctx.send(
                "❌ Unable to send the test announcement.\n"
                "Check the configured Discord channel and bot permissions."
            )

    # ==========================================================
    # delete_annonce
    # ==========================================================

    @commands.command(name="delete_annonce")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def delete_annonce(
        self,
        ctx,
        announcement_id: int,
    ):
        """Delete a Twitch announcement."""

        twitch_config = self._load_config()

        announcements = twitch_config["announcements"]

        announcement = next(
            (
                item
                for item in announcements
                if item.get("id") == announcement_id
            ),
            None,
        )

        if announcement is None:
            await ctx.send(
                f"❌ Announcement `{announcement_id}` not found."
            )
            return

        announcements.remove(announcement)

        if not self._save_config(twitch_config):
            await ctx.send(
                "❌ Failed to save the configuration."
            )
            return

        await ctx.send(
            f"🗑️ Twitch announcement `{announcement_id}` deleted."
        )

    # ==========================================================
    # Twitch background task
    # ==========================================================

    @tasks.loop(seconds=60)
    async def twitch_task(self):
        """
        Check all configured Twitch channels every 60 seconds.

        An announcement is sent only when the channel changes from
        offline to live.
        """

        twitch_config = self._load_config()
        announcements = twitch_config.get("announcements", [])

        if not announcements:
            return

        if (
            not config.TWITCH_CLIENT_ID
            or not config.TWITCH_CLIENT_SECRET
        ):
            return

        config_changed = False

        async with aiohttp.ClientSession() as session:

            for announcement in announcements:

                twitch_url = announcement.get("twitch_url")

                if not twitch_url:
                    continue

                twitch_login = self._extract_twitch_login(
                    twitch_url
                )

                if not twitch_login:
                    logger.warning(
                        f"Invalid Twitch URL: {twitch_url}"
                    )
                    continue

                stream_data = await self._get_stream_data(
                    session,
                    twitch_login,
                )

                is_live = stream_data is not None

                was_live = announcement.get(
                    "was_live",
                    False,
                )

                # Offline -> Live
                if is_live and not was_live:

                    success = await self._send_announcement(
                        announcement,
                        stream_data,
                    )

                    if success:
                        announcement["was_live"] = True
                        config_changed = True

                # Live -> Offline
                elif not is_live and was_live:

                    announcement["was_live"] = False
                    config_changed = True

        if config_changed:
            self._save_config(twitch_config)

    @twitch_task.before_loop
    async def before_twitch_task(self):
        """Wait until the Discord bot is ready."""
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(TwitchCog(bot))
