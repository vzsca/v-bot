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
    Path(__file__).resolve().parent.parent
    / "annonce_config.json"
)

# YouTube Data API v3
YOUTUBE_API_KEY = config.YOUTUBE_API_KEY
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

        Supported formats:
        - /channel/UCxxxxxxxx
        - /@username
        - /c/channelname
        - /user/channelname

        Returns:
            ("channel_id", value)
            ("handle", value)
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

            # --------------------------------------------------
            # /user/channelname
            # --------------------------------------------------

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
    ) -> dict | None:
        """Send a GET request to the YouTube Data API."""

        if not YOUTUBE_API_KEY:
            logger.warning(
                "YouTube API key is missing. "
                "Set YOUTUBE_API_KEY in .env."
            )
            return None

        request_params = {
            **params,
            "key": YOUTUBE_API_KEY,
        }

        url = (
            f"{YOUTUBE_API_URL}/{endpoint}"
        )

        try:
            async with session.get(
                url,
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

        except Exception:
            logger.exception(
                "Unexpected error during "
                "YouTube API request."
            )

            return None

    # ==========================================================
    # Resolve channel ID
    # ==========================================================

    async def _resolve_channel_id(
        self,
        session: aiohttp.ClientSession,
        source_url: str,
    ) -> str | None:
        """
        Resolve a YouTube URL to a channel ID.

        This function is only called when the channel ID
        is not already stored in annonce_config.json.
        """

        identifier = (
            self._extract_youtube_identifier(
                source_url
            )
        )

        if not identifier:
            logger.warning(
                "Invalid YouTube channel URL: "
                f"{source_url}"
            )
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
                logger.warning(
                    "YouTube handle not found: "
                    f"{value}"
                )
                return None

            return items[0].get("id")

        # ------------------------------------------------------
        # Custom URL
        #
        # search.list is more expensive, so this is only used
        # once when the channel ID is not already cached.
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
                logger.warning(
                    "YouTube custom channel not found: "
                    f"{value}"
                )
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
        """
        Get channel information and the uploads playlist.

        This should normally only be called once per announcement,
        because uploads_playlist_id is cached in the config.
        """

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
            logger.warning(
                "YouTube channel not found: "
                f"{channel_id}"
            )
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
            logger.warning(
                "No uploads playlist found for "
                f"YouTube channel {channel_id}."
            )
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
        """
        Get the latest video from the uploads playlist.

        This is the only API call performed on every monitoring
        cycle once the channel information is cached.
        """

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
                f"https://www.youtube.com/watch?v={video_id}"
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
        """Send a YouTube announcement to Discord."""

        channel_id = announcement.get(
            "channel_id"
        )

        message = announcement.get(
            "message"
        )

        if not channel_id:
            logger.warning(
                "YouTube announcement has no "
                "Discord channel_id."
            )
            return False

        if not message:
            logger.warning(
                "YouTube announcement has no message."
            )
            return False

        try:
            channel_id_int = int(
                channel_id
            )
        except (
            TypeError,
            ValueError,
        ):
            logger.warning(
                "Invalid Discord channel ID: "
                f"{channel_id}"
            )
            return False

        channel = self.bot.get_channel(
            channel_id_int
        )

        if channel is None:
            logger.warning(
                "Discord channel "
                f"{channel_id} was not found."
            )
            return False

        formatted_message = (
            self._format_message(
                message,
                video_data,
            )
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

    @tasks.loop(seconds=60)
    async def youtube_task(self):
        """
        Check all YouTube announcements every 60 seconds.

        Channel information and the uploads playlist are cached
        in annonce_config.json.

        Once cached, only playlistItems.list is used to check
        for new videos.
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

        if not YOUTUBE_API_KEY:
            logger.warning(
                "YouTube monitoring disabled: "
                "YOUTUBE_API_KEY is missing."
            )
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
                    logger.warning(
                        "YouTube announcement has no "
                        "source_url."
                    )
                    continue

                # --------------------------------------------------
                # Channel ID
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
                        continue

                    announcement[
                        "youtube_channel_id"
                    ] = channel_id

                    config_changed = True

                # --------------------------------------------------
                # Uploads playlist
                # --------------------------------------------------

                uploads_playlist = (
                    announcement.get(
                        "uploads_playlist_id"
                    )
                )

                if not uploads_playlist:

                    channel_data = (
                        await self._get_channel_data(
                            session,
                            channel_id,
                        )
                    )

                    if not channel_data:
                        continue

                    uploads_playlist = (
                        channel_data[
                            "uploads_playlist"
                        ]
                    )

                    announcement[
                        "uploads_playlist_id"
                    ] = uploads_playlist

                    # Store channel name if available.
                    if channel_data.get(
                        "channel"
                    ):
                        announcement[
                            "youtube_channel_name"
                        ] = channel_data[
                            "channel"
                        ]

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

                if not video_data:
                    continue

                latest_video_id = (
                    video_data["video_id"]
                )

                last_video_id = (
                    announcement.get(
                        "last_video_id"
                    )
                )

                # --------------------------------------------------
                # First check
                #
                # Save the current video without announcing it.
                # --------------------------------------------------

                if not last_video_id:

                    announcement[
                        "last_video_id"
                    ] = latest_video_id

                    config_changed = True

                    logger.info(
                        "Initialized YouTube announcement "
                        f"for {source_url} with video "
                        f"{latest_video_id}."
                    )

                    continue

                # --------------------------------------------------
                # New video detected
                # --------------------------------------------------

                if latest_video_id != last_video_id:

                    logger.info(
                        "New YouTube video detected: "
                        f"{video_data['title']} "
                        f"({latest_video_id})"
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

                        logger.info(
                            "YouTube announcement sent "
                            f"for {latest_video_id}."
                        )

                    else:

                        logger.warning(
                            "YouTube announcement failed "
                            f"for {latest_video_id}. "
                            "It will be retried."
                        )

        # ----------------------------------------------------------
        # Save changes
        # ----------------------------------------------------------

        if config_changed:
            self._save_config(
                announcement_config
            )

    @youtube_task.before_loop
    async def before_youtube_task(self):
        """Wait until the Discord bot is ready."""

        await self.bot.wait_until_ready()


# ==============================================================
# Cog setup
# ==============================================================

async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        YouTubeCog(bot)
    )
