"""
YouTube integration and automatic video announcements.

This cog handles:
- YouTube API authentication
- YouTube channel detection
- New video detection
- Automatic YouTube announcements
- YouTube announcement testing

Announcement management is handled by annonce.py.
"""

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
import discord
from discord.ext import commands, tasks

import config

logger = logging.getLogger("v-bot")

ANNOUNCE_CONFIG_FILE = (
    Path(__file__).resolve().parent.parent / "annonce_config.json"
)

# YouTube Data API v3 base URL
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeCog(commands.Cog, name="YouTube"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self._ensure_config_file()
        self.youtube_task.start()

    def cog_unload(self):
        self.youtube_task.cancel()

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
    # YouTube URL
    # ==========================================================

    @staticmethod
    def _extract_youtube_identifier(
        youtube_url: str,
    ) -> tuple[str, str] | None:
        """
        Extract the YouTube identifier from a channel URL.

        Returns:
            ("channel_id", value)
            or
            ("handle", value)
            or
            ("custom", value)
        """

        try:
            parsed = urlparse(
                youtube_url.strip()
            )

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

            if hostname not in {
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
            }:
                return None

            path = parsed.path.strip("/")

            if not path:
                return None

            # --------------------------------------------------
            # /channel/UCxxxxxxxx
            # --------------------------------------------------

            if path.startswith("channel/"):
                channel_id = path[
                    len("channel/"):
                ].split("/")[0]

                if channel_id.startswith("UC"):
                    return (
                        "channel_id",
                        channel_id,
                    )

                return None

            # --------------------------------------------------
            # /@username
            # --------------------------------------------------

            if path.startswith("@"):
                handle = path.split("/")[0]

                if len(handle) > 1:
                    return (
                        "handle",
                        handle,
                    )

                return None

            # --------------------------------------------------
            # /c/channelname
            # /user/channelname
            # --------------------------------------------------

            if path.startswith("c/"):
                name = path[
                    len("c/"):
                ].split("/")[0]

                if name:
                    return (
                        "custom",
                        name,
                    )

                return None

            if path.startswith("user/"):
                name = path[
                    len("user/"):
                ].split("/")[0]

                if name:
                    return (
                        "custom",
                        name,
                    )

                return None

            return None

        except Exception:
            return None

    # ==========================================================
    # YouTube API
    # ==========================================================

    async def _api_get(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        params: dict,
    ) -> dict | None:
        """Send a GET request to the YouTube Data API."""

        api_key = getattr(
            config,
            "YOUTUBE_API_KEY",
            None,
        )

        if not api_key:
            logger.warning(
                "YouTube API key is missing. "
                "Set YOUTUBE_API_KEY in .env."
            )
            return None

        request_params = {
            **params,
            "key": api_key,
        }

        try:
            async with session.get(
                f"{YOUTUBE_API_URL}/{endpoint}",
                params=request_params,
            ) as response:

                if response.status != 200:
                    body = await response.text()

                    logger.warning(
                        "YouTube API returned HTTP "
                        f"{response.status}: {body}"
                    )

                    return None

                return await response.json()

        except aiohttp.ClientError:
            logger.exception(
                "YouTube API request failed."
            )

            return None

    async def _resolve_channel_id(
        self,
        session: aiohttp.ClientSession,
        source_url: str,
    ) -> str | None:
        """Resolve a YouTube channel URL to a channel ID."""

        identifier = (
            self._extract_youtube_identifier(
                source_url
            )
        )

        if not identifier:
            return None

        identifier_type, value = identifier

        # ------------------------------------------------------
        # Direct channel ID
        # ------------------------------------------------------

        if identifier_type == "channel_id":
            return value

        # ------------------------------------------------------
        # @handle
        # ------------------------------------------------------

        if identifier_type == "handle":
            data = await self._api_get(
                session,
                "channels",
                {
                    "part": "id",
                    "forHandle": value,
                },
            )

            if not data:
                return None

            items = data.get(
                "items",
                [],
            )

            if not items:
                return None

            return items[0].get(
                "id"
            )

        # ------------------------------------------------------
        # Custom URL
        # ------------------------------------------------------

        if identifier_type == "custom":
            data = await self._api_get(
                session,
                "search",
                {
                    "part": "snippet",
                    "q": value,
                    "type": "channel",
                    "maxResults": 1,
                },
            )

            if not data:
                return None

            items = data.get(
                "items",
                [],
            )

            if not items:
                return None

            return (
                items[0]
                .get("snippet", {})
                .get("channelId")
            )

        return None

    # ==========================================================
    # Channel information
    # ==========================================================

    async def _get_channel_data(
        self,
        session: aiohttp.ClientSession,
        channel_id: str,
    ) -> dict | None:
        """Get basic YouTube channel information."""

        data = await self._api_get(
            session,
            "channels",
            {
                "part": "snippet,contentDetails",
                "id": channel_id,
            },
        )

        if not data:
            return None

        items = data.get(
            "items",
            [],
        )

        if not items:
            return None

        channel = items[0]

        snippet = channel.get(
            "snippet",
            {},
        )

        content_details = channel.get(
            "contentDetails",
            {},
        )

        related_playlists = (
            content_details.get(
                "relatedPlaylists",
                {},
            )
        )

        uploads_playlist = (
            related_playlists.get(
                "uploads"
            )
        )

        if not uploads_playlist:
            return None

        return {
            "channel_id": channel_id,
            "channel": snippet.get(
                "title",
                "",
            ),
            "uploads_playlist": uploads_playlist,
        }

    # ==========================================================
    # Latest video
    # ==========================================================

    async def _get_latest_video(
        self,
        session: aiohttp.ClientSession,
        uploads_playlist: str,
    ) -> dict | None:
        """Get the latest video uploaded to a channel."""

        data = await self._api_get(
            session,
            "playlistItems",
            {
                "part": "snippet,contentDetails",
                "playlistId": uploads_playlist,
                "maxResults": 1,
            },
        )

        if not data:
            return None

        items = data.get(
            "items",
            [],
        )

        if not items:
            return None

        item = items[0]

        snippet = item.get(
            "snippet",
            {},
        )

        content_details = item.get(
            "contentDetails",
            {},
        )

        video_id = content_details.get(
            "videoId"
        )

        if not video_id:
            return None

        return {
            "video_id": video_id,
            "channel": snippet.get(
                "channelTitle",
                "",
            ),
            "title": snippet.get(
                "title",
                "",
            ),
            "url": (
                f"https://www.youtube.com/watch?v="
                f"{video_id}"
            ),
        }

    # ==========================================================
    # Announcement helpers
    # ==========================================================

    @staticmethod
    def _format_message(
        message: str,
        video_data: dict,
    ) -> str:
        """Replace YouTube announcement placeholders."""

        return (
            message
            .replace(
                "{channel}",
                str(
                    video_data.get(
                        "channel",
                        "",
                    )
                ),
            )
            .replace(
                "{title}",
                str(
                    video_data.get(
                        "title",
                        "",
                    )
                ),
            )
            .replace(
                "{url}",
                str(
                    video_data.get(
                        "url",
                        "",
                    )
                ),
            )
        )

    async def _send_announcement(
        self,
        announcement: dict,
        video_data: dict,
    ) -> bool:
        """Send a YouTube announcement."""

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
            logger.warning(
                "Discord channel "
                f"{channel_id} was not found."
            )
            return False

        formatted_message = self._format_message(
            message,
            video_data,
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
                "Failed to send YouTube announcement."
            )

            return False

    # ==========================================================
    # Test announcement
    # ==========================================================

    async def test_announcement(
        self,
        announcement: dict,
    ) -> bool:
        """Send a test YouTube announcement."""

        source_url = announcement.get(
            "source_url"
        )

        if not source_url:
            return False

        identifier = (
            self._extract_youtube_identifier(
                source_url
            )
        )

        if not identifier:
            return False

        identifier_type, value = identifier

        if identifier_type == "channel_id":
            channel_name = value

        elif identifier_type == "handle":
            channel_name = value

        else:
            channel_name = value

        test_data = {
            "channel": channel_name,
            "title": "Test video",
            "url": source_url,
        }

        return await self._send_announcement(
            announcement,
            test_data,
        )

    # ==========================================================
    # YouTube background task
    # ==========================================================

    @tasks.loop(seconds=30)
    async def youtube_task(self):
        """
        Check all YouTube announcements every 30 seconds.

        A notification is sent when a new video is detected.
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

        youtube_announcements = [
            announcement
            for announcement in announcements
            if announcement.get("type")
            == "youtube"
        ]

        if not youtube_announcements:
            return

        if not getattr(
            config,
            "YOUTUBE_API_KEY",
            None,
        ):
            logger.warning(
                "YouTube announcements disabled: "
                "YOUTUBE_API_KEY is missing."
            )
            return

        config_changed = False

        async with aiohttp.ClientSession() as session:

            for announcement in youtube_announcements:

                source_url = announcement.get(
                    "source_url"
                )

                if not source_url:
                    continue

                # --------------------------------------------------
                # Resolve channel
                # --------------------------------------------------

                channel_id = announcement.get(
                    "youtube_channel_id"
                )

                if not channel_id:
                    channel_id = (
                        await self._resolve_channel_id(
                            session,
                            source_url,
                        )
                    )

                    if not channel_id:
                        logger.warning(
                            "Unable to resolve YouTube "
                            f"channel: {source_url}"
                        )
                        continue

                    announcement[
                        "youtube_channel_id"
                    ] = channel_id

                    config_changed = True

                # --------------------------------------------------
                # Get channel information
                # --------------------------------------------------

                channel_data = (
                    await self._get_channel_data(
                        session,
                        channel_id,
                    )
                )

                if not channel_data:
                    continue

                # --------------------------------------------------
                # Get latest video
                # --------------------------------------------------

                video_data = (
                    await self._get_latest_video(
                        session,
                        channel_data[
                            "uploads_playlist"
                        ],
                    )
                )

                if not video_data:
                    continue

                latest_video_id = (
                    video_data["video_id"]
                )

                last_video_id = announcement.get(
                    "last_video_id"
                )

                # --------------------------------------------------
                # First check
                #
                # Store the current video without announcing it.
                # This prevents an announcement when the bot starts.
                # --------------------------------------------------

                if not last_video_id:
                    announcement[
                        "last_video_id"
                    ] = latest_video_id

                    config_changed = True

                    continue

                # --------------------------------------------------
                # New video
                # --------------------------------------------------

                if latest_video_id != last_video_id:
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

    @youtube_task.before_loop
    async def before_youtube_task(self):
        """Wait until the Discord bot is ready."""

        await self.bot.wait_until_ready()


async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        YouTubeCog(bot)
    )
