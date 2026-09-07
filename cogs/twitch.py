"""Twitch integration with per-guild API credentials and announcements."""

import logging
import time
from urllib.parse import urlparse

import aiohttp
from discord.ext import commands, tasks

import announcement_store as store
import integration_config

logger = logging.getLogger("v-bot")


class TwitchCog(commands.Cog, name="Twitch"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # client_id, client_secret, access_token, expires_at — all keyed by guild.
        self._tokens: dict[int, tuple[str, str, str, float]] = {}
        self.twitch_task.start()

    def cog_unload(self):
        self.twitch_task.cancel()

    @staticmethod
    def _extract_twitch_login(url: str) -> str | None:
        try:
            parsed = urlparse(url.strip())
            if parsed.scheme not in {"http", "https"} or parsed.netloc.lower().split(":")[0] not in {"twitch.tv", "www.twitch.tv"}:
                return None
            login = parsed.path.strip("/").split("/")[0].lower()
            if not login or login in {"directory", "downloads", "jobs", "p", "search", "settings", "subscriptions", "videos"}:
                return None
            return login
        except ValueError:
            return None

    async def _get_access_token(self, session: aiohttp.ClientSession, guild_id: int) -> tuple[str, str] | None:
        credentials = integration_config.get_twitch_credentials(guild_id)
        if not credentials:
            return None
        client_id, client_secret = credentials
        cached = self._tokens.get(guild_id)
        if cached and cached[0] == client_id and cached[1] == client_secret and time.time() < cached[3]:
            return cached[0], cached[2]
        try:
            async with session.post(
                "https://id.twitch.tv/oauth2/token",
                params={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"},
            ) as response:
                if response.status != 200:
                    logger.error("Twitch authentication failed for guild %s (HTTP %s).", guild_id, response.status)
                    return None
                data = await response.json()
                token = data.get("access_token")
                expires_in = int(data.get("expires_in", 0) or 0)
                if not token:
                    return None
                self._tokens[guild_id] = (client_id, client_secret, token, time.time() + max(0, expires_in - 60))
                return client_id, token
        except (aiohttp.ClientError, ValueError):
            logger.exception("Twitch authentication request failed for guild %s.", guild_id)
            return None

    async def _get_stream_data(self, session: aiohttp.ClientSession, guild_id: int, login: str) -> dict | None:
        auth = await self._get_access_token(session, guild_id)
        if not auth:
            return None
        client_id, token = auth
        try:
            async with session.get(
                "https://api.twitch.tv/helix/streams",
                headers={"Client-Id": client_id, "Authorization": f"Bearer {token}"},
                params={"user_login": login},
            ) as response:
                if response.status == 401:
                    self._tokens.pop(guild_id, None)
                    return None
                if response.status == 429:
                    logger.warning("Twitch rate limit reached for guild %s.", guild_id)
                    return None
                if response.status != 200:
                    logger.warning("Twitch API returned HTTP %s for guild %s.", response.status, guild_id)
                    return None
                streams = (await response.json()).get("data", [])
                if not streams:
                    return None
                stream = streams[0]
                return {
                    "streamer": login,
                    "title": stream.get("title", ""),
                    "game": stream.get("game_name", ""),
                    "url": f"https://www.twitch.tv/{login}",
                }
        except aiohttp.ClientError:
            logger.exception("Unable to check Twitch channel %s for guild %s.", login, guild_id)
            return None

    @staticmethod
    def _format_message(message: str, data: dict) -> str:
        for key in ("streamer", "title", "game", "url"):
            message = message.replace("{" + key + "}", str(data.get(key, "")))
        return message

    async def _send_announcement(self, announcement: dict, stream_data: dict) -> bool:
        channel_id = announcement.get("channel_id")
        guild_id = announcement.get("guild_id")
        message = announcement.get("message")
        if not channel_id or not guild_id or not message:
            return False
        try:
            channel = self.bot.get_channel(int(channel_id))
        except (TypeError, ValueError):
            return False
        if channel is None or getattr(channel.guild, "id", None) != guild_id:
            logger.warning("Blocked Twitch announcement with mismatched guild/channel.")
            return False
        try:
            await channel.send(self._format_message(message, stream_data))
            return True
        except Exception:
            logger.exception("Failed to send Twitch announcement for guild %s.", guild_id)
            return False

    async def test_announcement(self, announcement: dict) -> bool:
        login = self._extract_twitch_login(announcement.get("source_url", ""))
        if not login or not announcement.get("guild_id"):
            return False
        return await self._send_announcement(announcement, {"streamer": login, "title": "Test stream", "game": "Test category", "url": f"https://www.twitch.tv/{login}"})

    @tasks.loop(seconds=60)
    async def twitch_task(self):
        data = store.load()
        announcements = [a for a in data["announcements"] if a.get("type") == "twitch" and a.get("guild_id")]
        if not announcements:
            return
        timeout = aiohttp.ClientTimeout(total=15)
        changed = False
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Cache is scoped by (guild, streamer): credentials never cross guild boundaries.
            cache: dict[tuple[int, str], dict | None] = {}
            for announcement in announcements:
                guild_id = int(announcement["guild_id"])
                login = self._extract_twitch_login(announcement.get("source_url", ""))
                if not login or not integration_config.get_twitch_credentials(guild_id):
                    continue
                key = (guild_id, login)
                if key not in cache:
                    cache[key] = await self._get_stream_data(session, guild_id, login)
                stream = cache[key]
                is_live = stream is not None
                was_live = bool(announcement.get("was_live", False))
                if is_live and not was_live and await self._send_announcement(announcement, stream):
                    announcement["was_live"] = True
                    changed = True
                elif not is_live and was_live:
                    announcement["was_live"] = False
                    changed = True
        if changed:
            store.save(data)

    @twitch_task.before_loop
    async def before_twitch_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(TwitchCog(bot))
