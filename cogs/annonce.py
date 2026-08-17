"""
Announcement management.

This cog handles:
- Creating announcements
- Listing announcements
- Testing announcements
- Deleting announcements
- Detecting the announcement platform

Platform-specific API handling and background tasks
are handled by their respective cogs.
"""

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import discord
from discord.ext import commands

import checks

logger = logging.getLogger("v-bot")

ANNOUNCE_CONFIG_FILE = (
    Path(__file__).resolve().parent.parent / "annonce_config.json"
)


class AnnonceCog(commands.Cog, name="Announcements"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._ensure_config_file()

    # ==========================================================
    # Configuration
    # ==========================================================

    def _ensure_config_file(self) -> None:
        """Create annonce_config.json if it does not exist."""

        if ANNOUNCE_CONFIG_FILE.exists():
            return

        try:
            with open(
                ANNOUNCE_CONFIG_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    {"announcements": []},
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

        except OSError:
            logger.exception(
                "Unable to create annonce_config.json."
            )

    def _load_config(self) -> dict:
        """Load announcement configuration."""

        self._ensure_config_file()

        try:
            with open(
                ANNOUNCE_CONFIG_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return {"announcements": []}

            if not isinstance(
                data.get("announcements"),
                list,
            ):
                data["announcements"] = []

            return data

        except (
            OSError,
            json.JSONDecodeError,
        ):
            logger.exception(
                "Unable to load annonce_config.json."
            )

            return {"announcements": []}

    def _save_config(self, data: dict) -> bool:
        """Save announcement configuration."""

        try:
            with open(
                ANNOUNCE_CONFIG_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

            return True

        except OSError:
            logger.exception(
                "Unable to save annonce_config.json."
            )

            return False

    # ==========================================================
    # Platform detection
    # ==========================================================

    @staticmethod
    def _detect_platform(url: str) -> str | None:
        """Detect the platform from a URL."""

        try:
            parsed = urlparse(url.strip())

            if parsed.scheme not in (
                "http",
                "https",
            ):
                return None

            hostname = (
                parsed.netloc
                .lower()
                .split(":")[0]
            )

            if hostname in {
                "twitch.tv",
                "www.twitch.tv",
            }:
                return "twitch"

            if hostname in {
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
            }:
                return "youtube"

            return None

        except Exception:
            return None

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _get_next_id(
        announcements: list[dict],
    ) -> int:
        """Generate the next announcement ID."""

        existing_ids = [
            announcement.get("id")
            for announcement in announcements
            if isinstance(
                announcement.get("id"),
                int,
            )
        ]

        if not existing_ids:
            return 1

        return max(existing_ids) + 1

    # ==========================================================
    # create_annonce
    # ==========================================================

    @commands.command(name="create_annonce")
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def create_annonce(
        self,
        ctx: commands.Context,
    ):
        """Create a Twitch or YouTube announcement."""

        def message_check(
            message: discord.Message,
        ) -> bool:
            return (
                message.author.id == ctx.author.id
                and message.channel.id == ctx.channel.id
            )

        # ------------------------------------------------------
        # Platform URL
        # ------------------------------------------------------

        await ctx.send(
            "📢 **Create announcement**\n\n"
            "Send the Twitch or YouTube channel URL.\n"
            "You have **1 minute**."
        )

        try:
            response = await self.bot.wait_for(
                "message",
                timeout=60,
                check=message_check,
            )

        except TimeoutError:
            await ctx.send("⏰ Time expired.")
            return

        source_url = response.content.strip()

        platform = self._detect_platform(
            source_url
        )

        if platform is None:
            await ctx.send(
                "❌ Unsupported URL.\n"
                "Please provide a Twitch or YouTube channel URL."
            )
            return

        # ------------------------------------------------------
        # Announcement message
        # ------------------------------------------------------

        if platform == "twitch":
            placeholders = (
                "`{streamer}` → Twitch username\n"
                "`{title}` → Stream title\n"
                "`{game}` → Stream category\n"
                "`{url}` → Twitch stream URL"
            )

        elif platform == "youtube":
            placeholders = (
                "`{channel}` → YouTube channel name\n"
                "`{title}` → Video title\n"
                "`{url}` → YouTube video URL"
            )

        else:
            placeholders = (
                "`{url}` → Platform URL"
            )

        await ctx.send(
            "💬 **Send the announcement message.**\n"
            "You have **1 minute**.\n\n"
            "Available placeholders:\n"
            f"{placeholders}"
        )

        try:
            response = await self.bot.wait_for(
                "message",
                timeout=60,
                check=message_check,
            )

        except TimeoutError:
            await ctx.send("⏰ Time expired.")
            return

        announcement_message = (
            response.content.strip()
        )

        if not announcement_message:
            await ctx.send(
                "❌ The announcement message cannot be empty."
            )
            return

        # ------------------------------------------------------
        # Discord channel
        # ------------------------------------------------------

        await ctx.send(
            "📢 **Mention the Discord channel where "
            "the announcement should be sent.**\n"
            "You have **1 minute**.\n\n"
            "Example: `#announcements`"
        )

        def channel_check(
            message: discord.Message,
        ) -> bool:
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
        # Create announcement
        # ------------------------------------------------------

        announcement_config = self._load_config()

        announcements = announcement_config[
            "announcements"
        ]

        announcement_id = self._get_next_id(
            announcements
        )

        announcement = {
            "id": announcement_id,
            "type": platform,
            "source_url": source_url,
            "message": announcement_message,
            "channel_id": target_channel.id,
        }

        # Platform-specific state is initialized
        # by the corresponding platform cog.

        if platform == "twitch":
            announcement["was_live"] = False

        elif platform == "youtube":
            announcement["last_video_id"] = None

        announcements.append(
            announcement
        )

        if not self._save_config(
            announcement_config
        ):
            await ctx.send(
                "❌ Failed to save the announcement."
            )
            return

        # ------------------------------------------------------
        # Confirmation
        # ------------------------------------------------------

        embed = discord.Embed(
            title="✅ Announcement created",
            color=discord.Color.green(),
        )

        embed.add_field(
            name="ID",
            value=f"`{announcement_id}`",
            inline=True,
        )

        embed.add_field(
            name="Platform",
            value=platform.capitalize(),
            inline=True,
        )

        embed.add_field(
            name="Discord channel",
            value=target_channel.mention,
            inline=True,
        )

        embed.add_field(
            name="Source",
            value=source_url,
            inline=False,
        )

        embed.add_field(
            name="Message",
            value=announcement_message,
            inline=False,
        )

        await ctx.send(
            embed=embed
        )

    # ==========================================================
    # annonces
    # ==========================================================

    @commands.command(name="annonces")
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def annonces(
        self,
        ctx: commands.Context,
    ):
        """List all configured announcements."""

        announcement_config = (
            self._load_config()
        )

        announcements = announcement_config.get(
            "announcements",
            [],
        )

        if not announcements:
            await ctx.send(
                "📭 No announcements are configured."
            )
            return

        embed = discord.Embed(
            title="📢 Announcements",
            description=(
                f"**{len(announcements)}** "
                "announcement(s) configured."
            ),
            color=discord.Color.purple(),
        )

        for announcement in announcements:
            announcement_id = announcement.get(
                "id",
                "?",
            )

            platform = announcement.get(
                "type",
                "unknown",
            )

            source_url = announcement.get(
                "source_url",
                "Unknown",
            )

            channel_id = announcement.get(
                "channel_id"
            )

            message = announcement.get(
                "message",
                "No message",
            )

            discord_channel = (
                f"<#{channel_id}>"
                if channel_id
                else "Unknown"
            )

            if platform == "twitch":
                status = (
                    "🟢 LIVE"
                    if announcement.get(
                        "was_live",
                        False,
                    )
                    else "⚫ Offline"
                )

            elif platform == "youtube":
                status = "🟢 Enabled"

            else:
                status = "❔ Unknown"

            embed.add_field(
                name=(
                    f"#{announcement_id} — "
                    f"{platform.capitalize()}"
                ),
                value=(
                    f"**Source:** {source_url}\n"
                    f"**Channel:** {discord_channel}\n"
                    f"**Status:** {status}\n"
                    f"**Message:** {message}"
                ),
                inline=False,
            )

        await ctx.send(
            embed=embed
        )

    # ==========================================================
    # test_annonce
    # ==========================================================

    @commands.command(name="test_annonce")
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def test_annonce(
        self,
        ctx: commands.Context,
        announcement_id: int,
    ):
        """
        Test an announcement.

        The actual test data is generated by the
        corresponding platform cog.
        """

        announcement_config = (
            self._load_config()
        )

        announcement = next(
            (
                item
                for item in announcement_config[
                    "announcements"
                ]
                if item.get("id")
                == announcement_id
            ),
            None,
        )

        if announcement is None:
            await ctx.send(
                f"❌ Announcement `{announcement_id}` "
                "not found."
            )
            return

        platform = announcement.get(
            "type"
        )

        if platform not in {
            "twitch",
            "youtube",
        }:
            await ctx.send(
                "❌ Unsupported announcement platform."
            )
            return

        # Dispatch the test to the platform cog.
        cog_name = (
            "TwitchCog"
            if platform == "twitch"
            else "YouTubeCog"
        )

        platform_cog = self.bot.get_cog(
            cog_name
        )

        if platform_cog is None:
            await ctx.send(
                f"❌ The `{platform}` integration "
                "is not loaded."
            )
            return

        test_method = getattr(
            platform_cog,
            "test_announcement",
            None,
        )

        if test_method is None:
            await ctx.send(
                f"❌ The `{platform}` integration "
                "does not support announcement testing."
            )
            return

        success = await test_method(
            announcement
        )

        if success:
            await ctx.send(
                f"✅ Test announcement "
                f"`{announcement_id}` sent."
            )
        else:
            await ctx.send(
                "❌ Unable to send the test announcement.\n"
                "Check the configured Discord channel "
                "and bot permissions."
            )

    # ==========================================================
    # delete_annonce
    # ==========================================================

    @commands.command(name="delete_annonce")
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def delete_annonce(
        self,
        ctx: commands.Context,
        announcement_id: int,
    ):
        """Delete an announcement."""

        announcement_config = (
            self._load_config()
        )

        announcements = (
            announcement_config[
                "announcements"
            ]
        )

        announcement = next(
            (
                item
                for item in announcements
                if item.get("id")
                == announcement_id
            ),
            None,
        )

        if announcement is None:
            await ctx.send(
                f"❌ Announcement `{announcement_id}` "
                "not found."
            )
            return

        announcements.remove(
            announcement
        )

        if not self._save_config(
            announcement_config
        ):
            await ctx.send(
                "❌ Failed to save the configuration."
            )
            return

        await ctx.send(
            f"🗑️ Announcement "
            f"`{announcement_id}` deleted."
        )


async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        AnnonceCog(bot)
    )
