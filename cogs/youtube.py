"""YouTube integration with guild-safe credentials and bounded API caching."""

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
YOUTUBE_API_URL = "https://youtube.googleapis.com"
CACHE_TTL = 300


class YouTubeCog(commands.Cog, name="YouTube"):
    def __init__(self, bot):
        self.bot = bot
        self._channel_cache = {}
        self._latest_cache = {}
        self._backoff_until = {}
        self._session = None
        self.youtube_task.start()

    def cog_unload(self):
        self.youtube_task.cancel()
        if self._session and not self._session.closed:
            asyncio.create_task(self._session.close())
        self._session = None

    def _prune_caches(self):
        now = time.time()
        self._channel_cache = {k: v for k, v in self._channel_cache.items() if now - v[1] < CACHE_TTL}
        self._latest_cache = {k: v for k, v in self._latest_cache.items() if now - v[1] < CACHE_TTL}
        self._backoff_until = {k: v for k, v in self._backoff_until.items() if now < v}

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    @staticmethod
    def _extract_identifier(url):
        try:
            p = urlparse(url.strip())
            if p.scheme not in {"http", "https"} or p.netloc.lower().split(":")[0] not in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
                return None
            path = p.path.strip("/")
            if path.startswith("channel/"):
                value = path[8:].split("/")[0]
                return ("channel_id", value) if value.startswith("UC") else None
            if path.startswith("@"):
                value = path.split("/")[0]
                return ("handle", value) if len(value) > 1 else None
            if path.startswith("c/") or path.startswith("user/"):
                value = path.split("/", 1)[1].split("/")[0]
                return ("custom", value) if value else None
        except ValueError:
            pass
        return None

    async def _api_get(self, session, guild_id, endpoint, params):
        api_key = integration_config.get_youtube_api_key(guild_id)
        if not api_key:
            return None, None
        credential_scope = api_key
        if time.time() < self._backoff_until.get(credential_scope, 0):
            return None, 429
        try:
            async with session.get(f"{YOUTUBE_API_URL}/{endpoint}", params={**params, "key": api_key}) as response:
                if response.status != 200:
                    if response.status in {403, 429}:
                        self._backoff_until[credential_scope] = time.time() + 120
                        logger.warning("YouTube API limit/error HTTP %s; backing off.", response.status)
                    return None, response.status
                return await response.json(), 200
        except (aiohttp.ClientError, ValueError):
            logger.exception("YouTube API request failed.")
            return None, None

    async def _resolve_channel_id(self, session, guild_id, source_url):
        identifier = self._extract_identifier(source_url)
        if not identifier:
            return None
        kind, value = identifier
        if kind == "channel_id":
            return value
        api_key = integration_config.get_youtube_api_key(guild_id)
        cache_key = (api_key, f"{kind}:{value}")
        cached = self._channel_cache.get(cache_key)
        if cached and time.time() - cached[1] < 60:
            return cached[0]
        if kind == "handle":
            data, status = await self._api_get(session, guild_id, "youtube/v3/channels", {"part": "id", "forHandle": value})
        else:
            data, status = await self._api_get(session, guild_id, "youtube/v3/search", {"part": "snippet", "q": value, "type": "channel", "maxResults": 5})
        if status != 200 or not data or not data.get("items"):
            return None
        items = data["items"]
        if kind == "handle":
            channel_id = items[0].get("id")
        else:
            exact = next((i for i in items if i.get("snippet", {}).get("title", "").casefold() == value.casefold()), items[0])
            channel_id = exact.get("snippet", {}).get("channelId")
        if channel_id:
            self._channel_cache[cache_key] = (channel_id, time.time())
        return channel_id

    async def _get_uploads_playlist(self, session, guild_id, channel_id):
        api_key = integration_config.get_youtube_api_key(guild_id)
        cache_key = (api_key, "playlist:" + channel_id)
        cached = self._channel_cache.get(cache_key)
        if cached and time.time() - cached[1] < 60:
            return cached[0]
        data, status = await self._api_get(session, guild_id, "youtube/v3/channels", {"part": "contentDetails", "id": channel_id})
        if status != 200 or not data or not data.get("items"):
            return None
        playlist_id = data["items"][0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        if playlist_id:
            self._channel_cache[cache_key] = (playlist_id, time.time())
        return playlist_id

    async def _get_latest_video(self, session, guild_id, channel_id):
        api_key = integration_config.get_youtube_api_key(guild_id)
        cache_key = (api_key, channel_id)
        cached = self._latest_cache.get(cache_key)
        if cached and time.time() - cached[1] < 60:
            return cached[0]
        playlist_id = await self._get_uploads_playlist(session, guild_id, channel_id)
        if not playlist_id:
            return None
        data, status = await self._api_get(session, guild_id, "youtube/v3/playlistItems", {"part": "snippet,contentDetails", "playlistId": playlist_id, "maxResults": 1})
        if status != 200 or not data or not data.get("items"):
            return None
        item = data["items"][0]
        video_id = item.get("contentDetails", {}).get("videoId")
        if not video_id:
            return None
        snippet = item.get("snippet", {})
        result = {"video_id": video_id, "channel": snippet.get("channelTitle", ""), "title": snippet.get("title", ""), "url": f"https://www.youtube.com/watch?v={video_id}"}
        self._latest_cache[cache_key] = (result, time.time())
        return result

    @staticmethod
    def _format_message(message, data):
        for key in ("channel", "title", "url"):
            message = message.replace("{" + key + "}", str(data.get(key, "")))
        return message[:2000]

    async def _send_announcement(self, announcement, video_data):
        channel_id, guild_id, message = announcement.get("channel_id"), announcement.get("guild_id"), announcement.get("message")
        if not channel_id or not guild_id or not message:
            return False
        try:
            channel = self.bot.get_channel(int(channel_id))
        except (TypeError, ValueError):
            return False
        if channel is None or getattr(channel.guild, "id", None) != guild_id:
            logger.warning("Blocked YouTube announcement with mismatched guild/channel.")
            return False
        try:
            await channel.send(self._format_message(message, video_data))
            return True
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            logger.warning("Failed to send YouTube announcement for guild %s.", guild_id)
            return False

    async def test_announcement(self, announcement):
        identifier = self._extract_identifier(announcement.get("source_url", ""))
        if not identifier:
            return False
        _, value = identifier
        return await self._send_announcement(announcement, {"channel": value, "title": "Test video", "url": announcement.get("source_url", "")})

    @tasks.loop(seconds=60)
    async def youtube_task(self):
        self._prune_caches()
        data = store.load()
        announcements = [a for a in data["announcements"] if a.get("type") == "youtube" and a.get("guild_id")]
        if not announcements:
            return
        session = await self._get_session()
        changed = False
        latest_cache = {}
        for announcement in announcements:
            guild_id = int(announcement["guild_id"])
            if not integration_config.get_youtube_api_key(guild_id):
                continue
            source = announcement.get("source_url", "")
            if not source:
                continue
            channel_id = announcement.get("youtube_channel_id")
            if not channel_id:
                channel_id = await self._resolve_channel_id(session, guild_id, source)
                if not channel_id:
                    continue
                announcement["youtube_channel_id"] = channel_id
                changed = True
            key = (guild_id, channel_id)
            if key not in latest_cache:
                latest_cache[key] = await self._get_latest_video(session, guild_id, channel_id)
            video = latest_cache[key]
            if not video:
                continue
            if announcement.get("last_video_id") is None:
                announcement["last_video_id"] = video["video_id"]
                changed = True
                continue
            if announcement.get("last_video_id") != video["video_id"] and await self._send_announcement(announcement, video):
                announcement["last_video_id"] = video["video_id"]
                changed = True
        if changed:
            store.save(data)

    @youtube_task.before_loop
    async def before_youtube_task(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(YouTubeCog(bot))
