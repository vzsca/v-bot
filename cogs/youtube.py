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
POLL_INTERVAL_SECONDS = 120
CHANNEL_CACHE_TTL = 86400
LATEST_CACHE_TTL = 90
BACKOFF_SECONDS = 120


class YouTubeCog(commands.Cog, name="YouTube"):
    def __init__(self, bot):
        self.bot = bot
        # Cache channel/playlist resolution by API key so the same API project can
        # reuse the result across every guild using that key.
        self._channel_cache = {}
        # Cache the latest video by API key + channel ID so cross-guild
        # announcements never trigger one API request per guild.
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
        self._channel_cache = {
            key: value
            for key, value in self._channel_cache.items()
            if now - value[1] < CHANNEL_CACHE_TTL
        }
        self._latest_cache = {
            key: value
            for key, value in self._latest_cache.items()
            if now - value[1] < LATEST_CACHE_TTL
        }
        self._backoff_until = {key: value for key, value in self._backoff_until.items() if now < value}

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    @staticmethod
    def _extract_identifier(url):
        try:
            p = urlparse(url.strip())
            if p.scheme not in {"http", "https"} or p.netloc.lower().split(":")[0] not in {
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
            }:
                return None
            path = p.path.strip("/")
            if path.startswith("channel/"):
                value = path[8:].split("/")[0]
                return ("channel_id", value) if value.startswith("UC") else None
            if path.startswith("@"):
                value = path.split("/")[0]
                return ("handle", value) if len(value) > 1 else None
            if path.startswith(("c/", "user/")):
                value = path.split("/", 1)[1].split("/")[0]
                return ("custom", value) if value else None
        except ValueError:
            pass
        return None

    async def _api_get(self, session, api_key, endpoint, params):
        if not api_key:
            return None, None
        if time.time() < self._backoff_until.get(api_key, 0):
            return None, 429
        try:
            async with session.get(
                f"{YOUTUBE_API_URL}/{endpoint}",
                params={**params, "key": api_key},
            ) as response:
                if response.status != 200:
                    if response.status in {403, 429}:
                        self._backoff_until[api_key] = time.time() + BACKOFF_SECONDS
                        logger.warning("YouTube API limit/error HTTP %s; backing off.", response.status)
                    return None, response.status
                return await response.json(), 200
        except (aiohttp.ClientError, ValueError):
            logger.exception("YouTube API request failed.")
            return None, None

    async def _resolve_channel_id(self, session, api_key, source_url):
        identifier = self._extract_identifier(source_url)
        if not identifier:
            return None
        kind, value = identifier
        if kind == "channel_id":
            return value

        cache_key = (api_key, f"{kind}:{value}")
        cached = self._channel_cache.get(cache_key)
        if cached and time.time() - cached[1] < CHANNEL_CACHE_TTL:
            return cached[0]

        if kind == "handle":
            data, status = await self._api_get(
                session,
                api_key,
                "youtube/v3/channels",
                {"part": "id", "forHandle": value},
            )
        else:
            data, status = await self._api_get(
                session,
                api_key,
                "youtube/v3/search",
                {
                    "part": "snippet",
                    "q": value,
                    "type": "channel",
                    "maxResults": 5,
                },
            )
        if status != 200 or not data or not data.get("items"):
            return None

        items = data["items"]
        if kind == "handle":
            channel_id = items[0].get("id")
        else:
            exact = next(
                (
                    item
                    for item in items
                    if item.get("snippet", {}).get("title", "").casefold() == value.casefold()
                ),
                items[0],
            )
            channel_id = exact.get("snippet", {}).get("channelId")

        if channel_id:
            self._channel_cache[cache_key] = (channel_id, time.time())
        return channel_id

    async def _get_uploads_playlist(self, session, api_key, channel_id):
        cache_key = (api_key, "playlist:" + channel_id)
        cached = self._channel_cache.get(cache_key)
        if cached and time.time() - cached[1] < CHANNEL_CACHE_TTL:
            return cached[0]

        data, status = await self._api_get(
            session,
            api_key,
            "youtube/v3/channels",
            {"part": "contentDetails", "id": channel_id},
        )
        if status != 200 or not data or not data.get("items"):
            return None

        playlist_id = (
            data["items"][0]
            .get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )
        if playlist_id:
            self._channel_cache[cache_key] = (playlist_id, time.time())
        return playlist_id

    async def _get_latest_video(self, session, api_key, channel_id):
        cache_key = (api_key, channel_id)
        cached = self._latest_cache.get(cache_key)
        if cached and time.time() - cached[1] < LATEST_CACHE_TTL:
            return cached[0]

        playlist_id = await self._get_uploads_playlist(session, api_key, channel_id)
        if not playlist_id:
            return None

        data, status = await self._api_get(
            session,
            api_key,
            "youtube/v3/playlistItems",
            {
                "part": "snippet,contentDetails",
                "playlistId": playlist_id,
                "maxResults": 1,
            },
        )
        if status != 200 or not data or not data.get("items"):
            return None

        item = data["items"][0]
        video_id = item.get("contentDetails", {}).get("videoId")
        if not video_id:
            return None

        snippet = item.get("snippet", {})
        result = {
            "video_id": video_id,
            "channel": snippet.get("channelTitle", ""),
            "title": snippet.get("title", ""),
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
        self._latest_cache[cache_key] = (result, time.time())
        return result

    @staticmethod
    def _format_message(message, data):
        for key in ("channel", "title", "url"):
            message = message.replace("{" + key + "}", str(data.get(key, "")))
        return message[:2000]

    async def _send_announcement(self, announcement, video_data):
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
        return await self._send_announcement(
            announcement,
            {
                "channel": value,
                "title": "Test video",
                "url": announcement.get("source_url", ""),
            },
        )

    async def _poll_youtube_announcements(self):
        self._prune_caches()
        data = store.load()
        announcements = [
            announcement
            for announcement in data["announcements"]
            if announcement.get("type") == "youtube" and announcement.get("guild_id")
        ]
        if not announcements:
            return

        session = await self._get_session()
        updates = {}
        channel_checks = {}

        # First resolve each announcement to an API key + channel ID. This keeps
        # the API identity separate from the guild so the same channel can be
        # fetched once and reused by every guild using the same API key.
        for announcement in announcements:
            guild_id = int(announcement["guild_id"])
            api_key = integration_config.get_youtube_api_key(guild_id)
            if not api_key:
                continue

            source = announcement.get("source_url", "")
            if not source:
                continue

            channel_id = announcement.get("youtube_channel_id")
            if not channel_id:
                channel_id = await self._resolve_channel_id(session, api_key, source)
                if not channel_id:
                    continue
                announcement_key = (guild_id, announcement.get("id"))
                updates.setdefault(announcement_key, {})["youtube_channel_id"] = channel_id
                announcement["youtube_channel_id"] = channel_id

            cache_key = (api_key, channel_id)
            channel_checks.setdefault(cache_key, []).append(announcement)

        # One YouTube API lookup per unique API key + channel, no matter how
        # many guilds or announcements use that same channel.
        for (api_key, channel_id), grouped_announcements in channel_checks.items():
            video = await self._get_latest_video(session, api_key, channel_id)
            if not video:
                continue

            for announcement in grouped_announcements:
                announcement_key = (
                    int(announcement["guild_id"]),
                    announcement.get("id"),
                )
                if announcement.get("last_video_id") is None:
                    updates.setdefault(announcement_key, {})["last_video_id"] = video["video_id"]
                    continue

                if (
                    announcement.get("last_video_id") != video["video_id"]
                    and await self._send_announcement(announcement, video)
                ):
                    updates.setdefault(announcement_key, {})["last_video_id"] = video["video_id"]

        if updates:

            def apply_updates(current):
                count = 0
                for item in current["announcements"]:
                    key = (item.get("guild_id"), item.get("id"))
                    fields = updates.get(key)
                    if fields:
                        item.update(fields)
                        count += 1
                return count

            store.transaction(apply_updates)

    @tasks.loop(seconds=POLL_INTERVAL_SECONDS)
    async def youtube_task(self):
        await self._poll_youtube_announcements()

    @youtube_task.before_loop
    async def before_youtube_task(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(YouTubeCog(bot))
