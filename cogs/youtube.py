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

YOUTUBE_API_KEY = config.YOUTUBE_API_KEY
YOUTUBE_API_URL = "https://youtube.googleapis.com"


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

        except json.JSONDecodeError:
            logger.error(
                "Unable to load annonce_config.json: "
                "invalid JSON."
            )

            return {"announcements": []}

        except OSError:
            logger.exception(
                "Unable to read annonce_config.json."
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
        """Extract the YouTube channel identifier."""

        try:
            parsed = urlparse(
                youtube_url.strip()
            )

            if parsed.scheme not in {
                "http",
                "https",
            }:
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

            # /channel/UCxxxxxxxx

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

            # /@username

            if path.startswith("@"):
                handle = path.split("/")[0]

                if len(handle) > 1:
                    return (
                        "handle",
                        handle,
                    )

                return None

            # /c/channelname

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

            # /user/channelname

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
            logger.exception(
                "Failed to parse YouTube URL."
            )

            return None

    # ==========================================================
    # YouTube API
    # ==========================================================

    async def _api_get(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        params: dict,
    ) -> tuple[dict | None, int | None]:
        """
        Send a GET request to the YouTube Data API.

        Returns:
            (response_json, status_code)
        """

        if not YOUTUBE_API_KEY:
            logger.warning(
                "YouTube API key is missing. "
                "Set YOUTUBE_API_KEY in .env."
            )

            return None, None

        request_params = {
            **params,
            "key": YOUTUBE_API_KEY,
        }

        try:
            async with session.get(
                f"{YOUTUBE_API_URL}/{endpoint}",
                params=request_params,
            ) as response:

                status = response.status

                if status != 200:
                    body = await response.text()

                    return None, status

                return await response.json(), status

        except aiohttp.ClientError:
            logger.exception(
                "YouTube API request failed."
            )

            return None, None

        except ValueError:
            logger.exception(
                "YouTube API returned invalid JSON."
            )

            return None, None

    # ==========================================================
    # Resolve channel
    # ==========================================================

    async def _resolve_channel_id(
        self,
        session: aiohttp.ClientSession,
        source_url: str,
    ) -> str | None:
        """Resolve a YouTube URL to a channel ID."""

        identifier = (
            self._extract_youtube_identifier(
                source_url
            )
        )

        if not identifier:
            return None

        identifier_type, value = identifier

        # Direct channel ID

        if identifier_type == "channel_id":
            return value

        # @handle

        if identifier_type == "handle":

            data, status = await self._api_get(
                session,
                "youtube/v3/channels",
                {
                    "part": "id",
                    "forHandle": value,
                },
            )

            if status != 200 or not data:
                return None

            items = data.get(
                "items",
                [],
            )

            if not items:
                return None

            return items[0].get("id")

        # Custom URL

        if identifier_type == "custom":

            data, status = await self._api_get(
                session,
                "youtube/v3/search",
                {
                    "part": "snippet",
                    "q": value,
                    "type": "channel",
                    "maxResults": 1,
                },
            )

            if status != 200 or not data:
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
        """Get YouTube channel information."""

        data, status = await self._api_get(
            session,
            "youtube/v3/channels",
            {
                "part": "snippet,contentDetails",
                "id": channel_id,
            },
        )

        if status != 200 or not data:
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
            return {
                "channel_id": channel_id,
                "channel": snippet.get(
                    "title",
                    "",
                ),
                "uploads_playlist": None,
            }

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
        uploads_playlist: str | None,
    ) -> dict | None:
        """
        Get the latest video.

        A missing uploads playlist is treated as:
        channel currently has no videos.
        """

        if not uploads_playlist:
            return None

        data, status = await self._api_get(
            session,
            "youtube/v3/playlistItems",
            {
                "part": "snippet,contentDetails",
                "playlistId": uploads_playlist,
                "maxResults": 1,
            },
        )

        # ------------------------------------------------------
        # IMPORTANT:
        # A 404 playlistNotFound can happen when the channel
        # currently has no videos.
        #
        # This is NOT treated as an API error.
        # ------------------------------------------------------

        if status == 404:
            return None

        if status != 200 or not data:
            logger.warning(
                "Unable to retrieve latest YouTube video "
                f"from playlist {uploads_playlist}."
            )

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
                f"https://www.youtube.com/watch?v={video_id}"
            ),
        }

    # ==========================================================
    # Announcement formatting
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

    # ==========================================================
    # Send announcement
    # ==========================================================

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

        try:
            channel = self.bot.get_channel(
                int(channel_id)
            )

        except (TypeError, ValueError):
            logger.warning(
                f"Invalid Discord channel ID: {channel_id}"
            )

            return False

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

        _, value = identifier

        test_data = {
            "channel": value,
            "title": "Test video",
            "url": source_url,
        }

        return await self._send_announcement(
            announcement,
            test_data,
        )

    # ==========================================================
    # Background task
    # ==========================================================

    @tasks.loop(seconds=60)
    async def youtube_task(self):
        """
        Check all YouTube announcements every 60 seconds.

        The first video uploaded after an announcement has
        been configured IS announced.
        """

        announcement_config = self._load_config()

        announcements = announcement_config.get(
            "announcements",
            [],
        )

        youtube_announcements = [
            announcement
            for announcement in announcements
            if announcement.get("type") == "youtube"
        ]

        if not youtube_announcements:
            return

        if not YOUTUBE_API_KEY:
            return

        config_changed = False

        timeout = aiohttp.ClientTimeout(
            total=15
        )

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            for announcement in youtube_announcements:

                source_url = announcement.get(
                    "source_url"
                )

                if not source_url:
                    continue

                # --------------------------------------------------
                # Resolve channel ID
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
                # Get channel data
                # --------------------------------------------------

                channel_data = (
                    await self._get_channel_data(
                        session,
                        channel_id,
                    )
                )

                if not channel_data:
                    continue

                channel_name = channel_data.get(
                    "channel",
                    "Unknown",
                )

                uploads_playlist = (
                    channel_data.get(
                        "uploads_playlist"
                    )
                )

                # --------------------------------------------------
                # No uploads playlist
                # --------------------------------------------------

                if not uploads_playlist:
                    logger.info(
                        f"YouTube channel "
                        f"{channel_name} has no videos yet."
                    )

                    continue

                # Save playlist ID so we don't need to retrieve
                # it again from the API every minute.

                if announcement.get(
                    "youtube_uploads_playlist"
                ) != uploads_playlist:

                    announcement[
                        "youtube_uploads_playlist"
                    ] = uploads_playlist

                    config_changed = True

                # --------------------------------------------------
                # Get latest video
                # --------------------------------------------------

                video_data = (
                    await self._get_latest_video(
                        session,
                        uploads_playlist,
                    )
                )

                # --------------------------------------------------
                # No videos yet
                # --------------------------------------------------

                if video_data is None:

                    logger.info(
                        f"YouTube channel "
                        f"{channel_name} has no videos yet."
                    )

                    continue

                latest_video_id = (
                    video_data["video_id"]
                )

                last_video_id = announcement.get(
                    "last_video_id"
                )

                # --------------------------------------------------
                # IMPORTANT:
                #
                # If last_video_id is None, it means that NO video
                # has ever been announced.
                #
                # Therefore the first video MUST be announced.
                # --------------------------------------------------

                if not last_video_id:

                    logger.info(
                        f"New first video detected on "
                        f"YouTube channel {channel_name}: "
                        f"{video_data['title']}"
                    )

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

                    continue

                # --------------------------------------------------
                # New video
                # --------------------------------------------------

                if latest_video_id != last_video_id:

                    logger.info(
                        f"New YouTube video detected on "
                        f"{channel_name}: "
                        f"{video_data['title']}"
                    )

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

    # ==========================================================
    # Task startup
    # ==========================================================

    @youtube_task.before_loop
    async def before_youtube_task(self):
        """Wait until the Discord bot is ready."""

        await self.bot.wait_until_ready()


# ==============================================================
# Setup
# ==============================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(
        YouTubeCog(bot)
    )
