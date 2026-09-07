"""Twitch integration with guild-safe credentials and bounded API caching."""

import asyncio
import logging
import time
from urllib.parse import urlparse

import aiohttp
import discord
from discord.ext import commands, tasks

import announcement_store as store
import integration_config

logger = logging.getLogger("v-bot")
CACHE_TTL = 300


class TwitchCog(commands.Cog, name="Twitch"):
    def __init__(self, bot):
        self.bot = bot
        self._tokens = {}
        self._stream_cache = {}
        self._backoff_until = {}
        self._session = None
        self.twitch_task.start()

    def cog_unload(self):
        self.twitch_task.cancel()
        if self._session and not self._session.closed:
            asyncio.create_task(self._session.close())
        self._session = None

    def _prune_caches(self):
        now = time.time()
        self._tokens = {k: v for k, v in self._tokens.items() if now < v[1]}
        self._stream_cache = {k: v for k, v in self._stream_cache.items() if now - v[1] < CACHE_TTL}
        self._backoff_until = {k: v for k, v in self._backoff_until.items() if now < v}

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    @staticmethod
    def _extract_twitch_login(url):
        try:
            parsed = urlparse(url.strip())
            host = parsed.netloc.lower().split(":")[0]
            if parsed.scheme not in {"http", "https"} or host not in {"twitch.tv", "www.twitch.tv"}:
                return None
            login = parsed.path.strip("/").split("/")[0].lower()
            if not login or login in {"directory", "downloads", "jobs", "p", "search", "settings", "subscriptions", "videos"}:
                return None
            return login
        except ValueError:
            return None

    async def _get_access_token(self, session, guild_id):
        credentials = integration_config.get_twitch_credentials(guild_id)
        if not credentials:
            return None
        client_id, client_secret = credentials
        key = (client_id, client_secret)
        cached = self._tokens.get(key)
        if cached and time.time() < cached[1]:
            return client_id, cached[0]
        try:
            async with session.post("https://id.twitch.tv/oauth2/token", params={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}) as response:
                if response.status != 200:
                    logger.warning("Twitch authentication failed (HTTP %s).", response.status)
                    return None
                data = await response.json()
                token = data.get("access_token")
                expires_in = int(data.get("expires_in", 0) or 0)
                if not token:
                    return None
                self._tokens[key] = (token, time.time() + max(30, expires_in - 60))
                return client_id, token
        except (aiohttp.ClientError, ValueError):
            logger.exception("Twitch authentication request failed.")
            return None

    async def _get_stream_data(self, session, guild_id, login):
        credentials = integration_config.get_twitch_credentials(guild_id)
        if not credentials:
            return None
        client_id, client_secret = credentials
        credential_key = (client_id, client_secret)
        if time.time() < self._backoff_until.get(credential_key, 0):
            return None
        cache_key = (client_id, login)
        cached = self._stream_cache.get(cache_key)
        if cached and time.time() - cached[1] < 60:
            return cached[0]
        auth = await self._get_access_token(session, guild_id)
        if not auth:
            return None
        client_id, token = auth
        try:
            async with session.get("https://api.twitch.tv/helix/streams", headers={"Client-Id": client_id, "Authorization": f"Bearer {token}"}, params={"user_login": login}) as response:
                if response.status == 401:
                    self._tokens.pop(credential_key, None)
                    return None
                if response.status == 429:
                    self._backoff_until[credential_key] = time.time() + 120
                    logger.warning("Twitch rate limit reached; backing off.")
                    return None
                if response.status != 200:
                    logger.warning("Twitch API returned HTTP %s.", response.status)
                    return None
                streams = (await response.json()).get("data", [])
                result = None
                if streams:
                    stream = streams[0]
                    result = {"streamer": login, "title": stream.get("title", ""), "game": stream.get("game_name", ""), "url": f"https://www.twitch.tv/{login}"}
                self._stream_cache[cache_key] = (result, time.time())
                return result
        except aiohttp.ClientError:
            logger.exception("Unable to check Twitch channel %s.", login)
            return None

    @staticmethod
    def _format_message(message, data):
        for key in ("streamer", "title", "game", "url"):
            message = message.replace("{" + key + "}", str(data.get(key, "")))
        return message[:2000]

    async def _send_announcement(self, announcement, stream_data):
        channel_id, guild_id, message = announcement.get("channel_id"), announcement.get("guild_id"), announcement.get("message")
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
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            logger.warning("Failed to send Twitch announcement for guild %s.", guild_id)
            return False

    async def test_announcement(self, announcement):
        login = self._extract_twitch_login(announcement.get("source_url", ""))
        if not login or not announcement.get("guild_id"):
            return False
        return await self._send_announcement(announcement, {"streamer": login, "title": "Test stream", "game": "Test category", "url": f"https://www.twitch.tv/{login}"})

    @tasks.loop(seconds=60)
    async def twitch_task(self):
        self._prune_caches()
        data = store.load()
        announcements = [a for a in data["announcements"] if a.get("type") == "twitch" and a.get("guild_id")]
        if not announcements:
            return
        session = await self._get_session()
        updates = {}
        cache = {}
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
            announcement_key = (guild_id, announcement.get("id"))
            if "was_live" not in announcement or announcement.get("was_live") is None:
                updates[announcement_key] = is_live
                continue
            was_live = bool(announcement.get("was_live", False))
            if is_live and not was_live and await self._send_announcement(announcement, stream):
                updates[announcement_key] = True
            elif not is_live and was_live:
                updates[announcement_key] = False
        if updates:
            def apply_updates(current):
                count = 0
                for item in current["announcements"]:
                    key = (item.get("guild_id"), item.get("id"))
                    if key in updates:
                        item["was_live"] = updates[key]
                        count += 1
                return count
            store.transaction(apply_updates)

    @twitch_task.before_loop
    async def before_twitch_task(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(TwitchCog(bot))
