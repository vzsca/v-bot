"""
Twitch integration and automatic stream announcements.

This cog handles:
- Twitch API authentication
- Twitch live detection
- Automatic Twitch announcements
- Twitch announcement testing

Announcement management is handled by annonce.py.
"""

import json
import logging
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands, tasks

import config

logger = logging.getLogger("v-bot")

ANNOUNCE_CONFIG_FILE = (
    Path(__file__).resolve().parent.parent / "annonce_config.json"
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
    # Twitch URL
    # ==========================================================

    @staticmethod
    def _extract_twitch_login(
        twitch_url: str,
    ) -> str | None:
        """Extract the Twitch username from a channel URL."""

        try:
            from urllib.parse import urlparse

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
        """Get a Twitch application access token."""

        if (
            not config.TWITCH_CLIENT_ID
            or not config.TWITCH_CLIENT_SECRET
        ):
            logger.warning(
                "Twitch API credentials are missing. "
                "Set TWITCH_CLIENT_ID and "
                "TWITCH_CLIENT_SECRET in .env."
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
                        "Unable to obtain Twitch access token "
                        f"(HTTP {response.status})."
                    )
                    return None

                data = await response.json()

                token = data.get(
                    "access_token"
                )

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
        """
        Return current Twitch stream data.

        Returns None when the channel is offline.
        """

        if not self.twitch_access_token:
            self.twitch_access_token = (
                await self._get_access_token(
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
                        f"{response.status} for channel "
                        f"{twitch_login}."
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
                "Unable to check Twitch channel: "
                f"{twitch_login}"
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
        """Replace Twitch announcement placeholders."""

        return (
            message
            .replace(
                "{streamer}",
                str(
                    stream_data.get(
                        "streamer",
                        "",
                    )
                ),
            )
            .replace(
                "{title}",
                str(
                    stream_data.get(
                        "title",
                        "",
                    )
                ),
            )
            .replace(
                "{game}",
                str(
                    stream_data.get(
                        "game",
                        "",
                    )
                ),
            )
            .replace(
                "{url}",
                str(
                    stream_data.get(
                        "url",
                        "",
                    )
                ),
            )
        )

    async def _send_announcement(
        self,
        announcement: dict,
        stream_data: dict,
    ) -> bool:
        """Send a Twitch announcement."""

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
            stream_data,
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
                "Failed to send Twitch announcement."
            )

            return False

    # ==========================================================
    # Test announcement
    # ==========================================================

    async def test_announcement(
        self,
        announcement: dict,
    ) -> bool:
        """Send a test Twitch announcement."""

        source_url = announcement.get(
            "source_url"
        )

        if not source_url:
            return False

        twitch_login = (
            self._extract_twitch_login(
                source_url
            )
        )

        if not twitch_login:
            return False

        test_data = {
            "streamer": twitch_login,
            "title": "Test stream",
            "game": "Test category",
            "url": (
                f"https://www.twitch.tv/"
                f"{twitch_login}"
            ),
        }

        return await self._send_announcement(
            announcement,
            test_data,
        )

    # ==========================================================
    # Twitch background task
    # ==========================================================

    @tasks.loop(seconds=60)
    async def twitch_task(self):
        """
        Check all Twitch announcements every 60 seconds.

        An announcement is sent only when a channel
        changes from offline to live.
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

        twitch_announcements = [
            announcement
            for announcement in announcements
            if announcement.get("type")
            == "twitch"
        ]

        if not twitch_announcements:
            return

        if (
            not config.TWITCH_CLIENT_ID
            or not config.TWITCH_CLIENT_SECRET
        ):
            return

        config_changed = False

        async with aiohttp.ClientSession() as session:

            for announcement in twitch_announcements:

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
                    logger.warning(
                        "Invalid Twitch URL: "
                        f"{source_url}"
                    )
                    continue

                stream_data = (
                    await self._get_stream_data(
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

                # --------------------------------------------------
                # Offline -> Live
                # --------------------------------------------------

                if is_live and not was_live:

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

                # --------------------------------------------------
                # Live -> Offline
                # --------------------------------------------------

                elif not is_live and was_live:

                    announcement[
                        "was_live"
                    ] = False

                    config_changed = True

        if config_changed:
            self._save_config(
                announcement_config
            )

    @twitch_task.before_loop
    async def before_twitch_task(self):
        """Wait until the Discord bot is ready."""

        await self.bot.wait_until_ready()


async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        TwitchCog(bot)
    )
