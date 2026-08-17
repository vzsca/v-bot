"""
Automatic Twitch and YouTube announcements.

This cog handles:
- Creating Twitch announcements
- Creating YouTube announcements
- Listing announcements
- Testing announcements
- Deleting announcements
- Automatic Twitch live detection
- Automatic YouTube upload detection

Configuration is stored in annonce_config.json.
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

ANNOUNCE_CONFIG_FILE = (
    Path(__file__).resolve().parent.parent / "annonce_config.json"
)


class AnnonceCog(commands.Cog, name="Announcements"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.twitch_access_token: str | None = None

        self._ensure_config_file()
        self.announcement_task.start()

    def cog_unload(self):
        self.announcement_task.cancel()

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
    # URL detection
    # ==========================================================

    @staticmethod
    def _detect_platform(url: str) -> str | None:
        """Detect whether a URL belongs to Twitch or YouTube."""

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
                "youtu.be",
            }:
                return "youtube"

            return None

        except Exception:
            return None

    # ==========================================================
    # Twitch URL
    # ==========================================================

    @staticmethod
    def _extract_twitch_login(
        twitch_url: str,
    ) -> str | None:
        """Extract the Twitch username from a channel URL."""

        try:
            parsed = urlparse(
                twitch_url.strip()
            )

            if parsed.scheme not in (
                "http",
                "https",
            ):
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
    # YouTube URL
    # ==========================================================

    @staticmethod
    def _extract_youtube_identifier(
        youtube_url: str,
    ) -> tuple[str, str] | None:
        """
        Extract the YouTube channel identifier.

        Supported:
        - https://www.youtube.com/channel/UC...
        - https://www.youtube.com/@username

        Returns:
            ("channel_id", value)
            ("handle", value)
        """

        try:
            parsed = urlparse(
                youtube_url.strip()
            )

            hostname = (
                parsed.netloc
                .lower()
                .split(":")[0]
            )

            if hostname not in {
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
            }:
                return None

            path = parsed.path.strip("/")

            if not path:
                return None

            parts = path.split("/")

            if (
                len(parts) >= 2
                and parts[0].lower() == "channel"
            ):
                return (
                    "channel_id",
                    parts[1],
                )

            if parts[0].startswith("@"):
                return (
                    "handle",
                    parts[0],
                )

            return None

        except Exception:
            return None

    # ==========================================================
    # Twitch API
    # ==========================================================

    async def _get_twitch_access_token(
        self,
        session: aiohttp.ClientSession,
    ) -> str | None:
        """Get a Twitch application access token."""

        if (
            not config.TWITCH_CLIENT_ID
            or not config.TWITCH_CLIENT_SECRET
        ):
            logger.warning(
                "Twitch API credentials are missing."
            )
            return None

        try:
            async with session.post(
                "https://id.twitch.tv/oauth2/token",
                params={
                    "client_id": (
                        config.TWITCH_CLIENT_ID
                    ),
                    "client_secret": (
                        config.TWITCH_CLIENT_SECRET
                    ),
                    "grant_type": (
                        "client_credentials"
                    ),
                },
            ) as response:

                if response.status != 200:
                    logger.error(
                        "Unable to obtain Twitch "
                        f"access token (HTTP {response.status})."
                    )
                    return None

                data = await response.json()

                token = data.get(
                    "access_token"
                )

                if not token:
                    return None

                self.twitch_access_token = token

                return token

        except aiohttp.ClientError:
            logger.exception(
                "Twitch authentication request failed."
            )
            return None

    async def _get_twitch_stream(
        self,
        session: aiohttp.ClientSession,
        twitch_login: str,
    ) -> dict | None:
        """Return Twitch stream data if the channel is live."""

        if not self.twitch_access_token:
            self.twitch_access_token = (
                await self._get_twitch_access_token(
                    session
                )
            )

        if not self.twitch_access_token:
            return None

        headers = {
            "Client-Id": (
                config.TWITCH_CLIENT_ID
            ),
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
                        "Twitch API returned HTTP "
                        f"{response.status} for {twitch_login}."
                    )
                    return None

                data = await response.json()

                streams = data.get(
                    "data",
                    [],
                )

                if not streams:
                    return None

                stream = streams[0]

                return {
                    "streamer": twitch_login,
                    "title": stream.get(
                        "title",
                        "",
                    ),
                    "game": stream.get(
                        "game_name",
                        "",
                    ),
                    "url": (
                        f"https://www.twitch.tv/"
                        f"{twitch_login}"
                    ),
                }

        except aiohttp.ClientError:
            logger.exception(
                "Unable to check Twitch channel "
                f"{twitch_login}."
            )

            return None

    # ==========================================================
    # YouTube API
    # ==========================================================

    async def _get_youtube_channel_id(
        self,
        session: aiohttp.ClientSession,
        identifier_type: str,
        identifier: str,
    ) -> str | None:
        """Resolve a YouTube handle to a channel ID."""

        if not config.YOUTUBE_API_KEY:
            logger.warning(
                "YOUTUBE_API_KEY is missing."
            )
            return None

        if identifier_type == "channel_id":
            return identifier

        try:
            async with session.get(
                "https://www.googleapis.com/"
                "youtube/v3/channels",
                params={
                    "part": "id",
                    "forHandle": identifier,
                    "key": config.YOUTUBE_API_KEY,
                },
            ) as response:

                if response.status != 200:
                    logger.warning(
                        "YouTube API returned HTTP "
                        f"{response.status} while resolving "
                        f"{identifier}."
                    )
                    return None

                data = await response.json()

                channels = data.get(
                    "items",
                    [],
                )

                if not channels:
                    return None

                return channels[0].get("id")

        except aiohttp.ClientError:
            logger.exception(
                "Unable to resolve YouTube channel."
            )
            return None

    async def _get_latest_youtube_video(
        self,
        session: aiohttp.ClientSession,
        channel_id: str,
    ) -> dict | None:
        """Get the latest video uploaded by a YouTube channel."""

        if not config.YOUTUBE_API_KEY:
            return None

        try:
            async with session.get(
                "https://www.googleapis.com/"
                "youtube/v3/search",
                params={
                    "part": "snippet",
                    "channelId": channel_id,
                    "order": "date",
                    "type": "video",
                    "maxResults": 1,
                    "key": config.YOUTUBE_API_KEY,
                },
            ) as response:

                if response.status != 200:
                    logger.warning(
                        "YouTube API returned HTTP "
                        f"{response.status}."
                    )
                    return None

                data = await response.json()

                videos = data.get(
                    "items",
                    [],
                )

                if not videos:
                    return None

                video = videos[0]

                video_id = (
                    video.get("id", {})
                    .get("videoId")
                )

                snippet = video.get(
                    "snippet",
                    {},
                )

                if not video_id:
                    return None

                return {
                    "channel": snippet.get(
                        "channelTitle",
                        "",
                    ),
                    "title": snippet.get(
                        "title",
                        "",
                    ),
                    "url": (
                        "https://www.youtube.com/watch?v="
                        f"{video_id}"
                    ),
                    "video_id": video_id,
                }

        except aiohttp.ClientError:
            logger.exception(
                "Unable to check YouTube channel."
            )
            return None

    # ==========================================================
    # Message formatting
    # ==========================================================

    @staticmethod
    def _format_message(
        message: str,
        data: dict,
    ) -> str:
        """Replace supported announcement placeholders."""

        return (
            message
            .replace(
                "{streamer}",
                str(data.get("streamer", "")),
            )
            .replace(
                "{title}",
                str(data.get("title", "")),
            )
            .replace(
                "{game}",
                str(data.get("game", "")),
            )
            .replace(
                "{channel}",
                str(data.get("channel", "")),
            )
            .replace(
                "{url}",
                str(data.get("url", "")),
            )
        )

    # ==========================================================
    # Send announcement
    # ==========================================================

    async def _send_announcement(
        self,
        announcement: dict,
        data: dict | None = None,
    ) -> bool:
        """Send an announcement."""

        channel_id = announcement.get(
            "channel_id"
        )

        message = announcement.get(
            "message"
        )

        if not channel_id or not message:
            return False

        channel = self.bot.get_channel(
            int(channel_id)
        )

        if channel is None:
            return False

        if data is None:
            data = {}

        formatted_message = self._format_message(
            message,
            data,
        )

        try:
            await channel.send(
                formatted_message
            )
            return True

        except discord.Forbidden:
            logger.warning(
                "Missing permission to send "
                f"messages in channel {channel_id}."
            )
            return False

        except discord.HTTPException:
            logger.exception(
                "Failed to send announcement."
            )
            return False

    # ==========================================================
    # create_annonce
    # ==========================================================

    @commands.command(name="create_annonce")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def create_annonce(
        self,
        ctx,
    ):
        """Create a Twitch or YouTube announcement."""

        def check(
            message: discord.Message,
        ) -> bool:
            return (
                message.author.id
                == ctx.author.id
                and message.channel.id
                == ctx.channel.id
            )

        await ctx.send(
            "📢 **Create announcement**\n\n"
            "Send the Twitch or YouTube channel URL.\n"
            "You have **1 minute**."
        )

        try:
            response = await self.bot.wait_for(
                "message",
                timeout=60,
                check=check,
            )

        except TimeoutError:
            await ctx.send(
                "⏰ Time expired."
            )
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

        if platform == "twitch":
            if not self._extract_twitch_login(
                source_url
            ):
                await ctx.send(
                    "❌ Invalid Twitch channel URL."
                )
                return

        elif platform == "youtube":
            if not self._extract_youtube_identifier(
                source_url
            ):
                await ctx.send(
                    "❌ Invalid YouTube channel URL.\n"
                    "Supported formats:\n"
                    "`https://youtube.com/@channel`\n"
                    "`https://youtube.com/channel/UC...`"
                )
                return

        # ------------------------------------------------------
        # Message
        # ------------------------------------------------------

        if platform == "twitch":
            placeholders = (
                "`{streamer}` → Twitch username\n"
                "`{title}` → Stream title\n"
                "`{game}` → Stream category\n"
                "`{url}` → Twitch stream URL"
            )

        else:
            placeholders = (
                "`{channel}` → YouTube channel name\n"
                "`{title}` → Video title\n"
                "`{url}` → YouTube video URL"
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
                check=check,
            )

        except TimeoutError:
            await ctx.send(
                "⏰ Time expired."
            )
            return

        announcement_message = (
            response.content.strip()
        )

        if not announcement_message:
            await ctx.send(
                "❌ The announcement message "
                "cannot be empty."
            )
            return

        # ------------------------------------------------------
        # Discord channel
        # ------------------------------------------------------

        await ctx.send(
            "📢 **Mention the Discord channel "
            "where the announcement should be sent.**\n"
            "You have **1 minute**.\n\n"
            "Example: `#announcements`"
        )

        def channel_check(
            message: discord.Message,
        ) -> bool:
            return (
                message.author.id
                == ctx.author.id
                and message.channel.id
                == ctx.channel.id
                and bool(
                    message.channel_mentions
                )
            )

        try:
            response = await self.bot.wait_for(
                "message",
                timeout=60,
                check=channel_check,
            )

        except TimeoutError:
            await ctx.send(
                "⏰ Time expired."
            )
            return

        target_channel = (
            response.channel_mentions[0]
        )

        # ------------------------------------------------------
        # YouTube channel ID
        # ------------------------------------------------------

        youtube_channel_id = None

        if platform == "youtube":
            identifier = (
                self._extract_youtube_identifier(
                    source_url
                )
            )

            if identifier is None:
                await ctx.send(
                    "❌ Unable to identify "
                    "the YouTube channel."
                )
                return

            identifier_type, identifier_value = (
                identifier
            )

            async with aiohttp.ClientSession() as session:
                youtube_channel_id = (
                    await self._get_youtube_channel_id(
                        session,
                        identifier_type,
                        identifier_value,
                    )
                )

            if not youtube_channel_id:
                await ctx.send(
                    "❌ Unable to resolve the YouTube channel.\n"
                    "Check your YouTube API key and the channel URL."
                )
                return

        # ------------------------------------------------------
        # Save announcement
        # ------------------------------------------------------

        announcement_config = (
            self._load_config()
        )

        announcement_id = 1

        existing_ids = [
            announcement.get("id")
            for announcement in (
                announcement_config[
                    "announcements"
                ]
            )
            if isinstance(
                announcement.get("id"),
                int,
            )
        ]

        if existing_ids:
            announcement_id = (
                max(existing_ids) + 1
            )

        announcement = {
            "id": announcement_id,
            "type": platform,
            "source_url": source_url,
            "message": announcement_message,
            "channel_id": target_channel.id,
        }

        if platform == "twitch":
            announcement["was_live"] = False

        elif platform == "youtube":
            announcement[
                "youtube_channel_id"
            ] = youtube_channel_id

            announcement[
                "last_video_id"
            ] = None

        announcement_config[
            "announcements"
        ].append(announcement)

        if not self._save_config(
            announcement_config
        ):
            await ctx.send(
                "❌ Failed to save the announcement."
            )
            return

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
            name="Type",
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
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def annonces(
        self,
        ctx,
    ):
        """List all configured announcements."""

        announcement_config = (
            self._load_config()
        )

        announcements = (
            announcement_config.get(
                "announcements",
                [],
            )
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
            announcement_id = (
                announcement.get(
                    "id",
                    "?",
                )
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

            else:
                status = "🟢 Enabled"

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
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def test_annonce(
        self,
        ctx,
        announcement_id: int,
    ):
        """Test an announcement."""

        announcement_config = (
            self._load_config()
        )

        announcement = next(
            (
                item
                for item in (
                    announcement_config[
                        "announcements"
                    ]
                )
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

        data = {}

        if platform == "twitch":
            twitch_login = (
                self._extract_twitch_login(
                    announcement.get(
                        "source_url",
                        "",
                    )
                )
            )

            if twitch_login:
                data = {
                    "streamer": twitch_login,
                    "title": "Test stream",
                    "game": "Test category",
                    "url": (
                        f"https://www.twitch.tv/"
                        f"{twitch_login}"
                    ),
                }

        elif platform == "youtube":
            data = {
                "channel": "Test Channel",
                "title": "Test video",
                "url": (
                    "https://www.youtube.com/"
                    "watch?v=test"
                ),
            }

        success = await self._send_announcement(
            announcement,
            data,
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
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def delete_annonce(
        self,
        ctx,
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

    # ==========================================================
    # Background task
    # ==========================================================

    @tasks.loop(seconds=60)
    async def announcement_task(
        self,
    ):
        """
        Check all configured announcements.

        Twitch:
            Announces when the channel goes
            from offline to live.

        YouTube:
            Announces when a new video is detected.
        """

        announcement_config = (
            self._load_config()
        )

        announcements = (
            announcement_config.get(
                "announcements",
                [],
            )
        )

        if not announcements:
            return

        config_changed = False

        async with aiohttp.ClientSession() as session:

            for announcement in announcements:

                platform = announcement.get(
                    "type"
                )

                # ==================================================
                # Twitch
                # ==================================================

                if platform == "twitch":

                    source_url = announcement.get(
                        "source_url"
                    )

                    if not source_url:
                        continue

                    twitch_login = (
                        self._extract_twitch_login(
                            source_url
                        )
                    )

                    if not twitch_login:
                        continue

                    stream_data = (
                        await self._get_twitch_stream(
                            session,
                            twitch_login,
                        )
                    )

                    is_live = (
                        stream_data is not None
                    )

                    was_live = announcement.get(
                        "was_live",
                        False,
                    )

                    # Offline -> Live
                    if (
                        is_live
                        and not was_live
                    ):

                        success = (
                            await self._send_announcement(
                                announcement,
                                stream_data,
                            )
                        )

                        if success:
                            announcement[
                                "was_live"
                            ] = True

                            config_changed = True

                    # Live -> Offline
                    elif (
                        not is_live
                        and was_live
                    ):

                        announcement[
                            "was_live"
                        ] = False

                        config_changed = True

                # ==================================================
                # YouTube
                # ==================================================

                elif platform == "youtube":

                    channel_id = announcement.get(
                        "youtube_channel_id"
                    )

                    if not channel_id:
                        continue

                    video_data = (
                        await self._get_latest_youtube_video(
                            session,
                            channel_id,
                        )
                    )

                    if not video_data:
                        continue

                    latest_video_id = (
                        video_data.get(
                            "video_id"
                        )
                    )

                    last_video_id = (
                        announcement.get(
                            "last_video_id"
                        )
                    )

                    # First check:
                    # Store the current video without announcing it.
                    if last_video_id is None:

                        announcement[
                            "last_video_id"
                        ] = latest_video_id

                        config_changed = True

                    # New video detected
                    elif (
                        latest_video_id
                        != last_video_id
                    ):

                        success = (
                            await self._send_announcement(
                                announcement,
                                video_data,
                            )
                        )

                        if success:
                            announcement[
                                "last_video_id"
                            ] = latest_video_id

                            config_changed = True

        if config_changed:
            self._save_config(
                announcement_config
            )

    @announcement_task.before_loop
    async def before_announcement_task(
        self,
    ):
        """Wait until the Discord bot is ready."""

        await self.bot.wait_until_ready()


async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        AnnonceCog(bot)
    )
