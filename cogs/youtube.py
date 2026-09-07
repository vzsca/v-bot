"""YouTube integration and automatic guild-safe announcements."""

import logging
from urllib.parse import urlparse

import aiohttp
from discord.ext import commands, tasks

import announcement_store as store
import config

logger = logging.getLogger("v-bot")
YOUTUBE_API_URL = "https://youtube.googleapis.com"


class YouTubeCog(commands.Cog, name="YouTube"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._channel_cache: dict[str, tuple[str, str | None]] = {}
        self.youtube_task.start()

    def cog_unload(self):
        self.youtube_task.cancel()

    @staticmethod
    def _extract_identifier(url: str) -> tuple[str, str] | None:
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

    async def _api_get(self, session: aiohttp.ClientSession, endpoint: str, params: dict) -> tuple[dict | None, int | None]:
        if not config.YOUTUBE_API_KEY:
            return None, None
        try:
            async with session.get(f"{YOUTUBE_API_URL}/{endpoint}", params={**params, "key": config.YOUTUBE_API_KEY}) as response:
                if response.status != 200:
                    if response.status in {403, 429}:
                        logger.warning("YouTube API limit/error HTTP %s.", response.status)
                    return None, response.status
                return await response.json(), response.status
        except (aiohttp.ClientError, ValueError):
            logger.exception("YouTube API request failed.")
            return None, None

    async def _resolve_channel_id(self, session: aiohttp.ClientSession, source_url: str) -> str | None:
        identifier = self._extract_identifier(source_url)
        if not identifier:
            return None
        kind, value = identifier
        if kind == "channel_id":
            return value
        cached = self._channel_cache.get(f"{kind}:{value}")
        if cached:
            return cached[0]
        if kind == "handle":
            data, status = await self._api_get(session, "youtube/v3/channels", {"part": "id", "forHandle": value})
        else:
            data, status = await self._api_get(session, "youtube/v3/search", {"part": "snippet", "q": value, "type": "channel", "maxResults": 5})
        if status != 200 or not data:
            return None
        items = data.get("items", [])
        if not items:
            return None
        if kind == "handle":
            channel_id = items[0].get("id")
        else:
            # Custom URLs are ambiguous; only accept an exact title match when possible.
            exact = next((i for i in items if i.get("snippet", {}).get("title", "").casefold() == value.casefold()), items[0])
            channel_id = exact.get("snippet", {}).get("channelId")
        if channel_id:
            self._channel_cache[f"{kind}:{value}"] = (channel_id, None)
        return channel_id

    async def _get_latest_video(self, session: aiohttp.ClientSession, channel_id: str) -> dict | None:
        data, status = await self._api_get(session, "youtube/v3/search", {"part": "snippet", "channelId": channel_id, "order": "date", "type": "video", "maxResults": 1})
        if status != 200 or not data or not data.get("items"):
            return None
        item = data["items"][0]
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            return None
        snippet = item.get("snippet", {})
        return {"video_id": video_id, "channel": snippet.get("channelTitle", ""), "title": snippet.get("title", ""), "url": f"https://www.youtube.com/watch?v={video_id}"}

    @staticmethod
    def _format_message(message: str, data: dict) -> str:
        for key in ("channel", "title", "url"):
            message = message.replace("{" + key + "}", str(data.get(key, "")))
        return message

    async def _send_announcement(self, announcement: dict, video_data: dict) -> bool:
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
        except Exception:
            logger.exception("Failed to send YouTube announcement.")
            return False

    async def test_announcement(self, announcement: dict) -> bool:
        identifier = self._extract_identifier(announcement.get("source_url", ""))
        if not identifier:
            return False
        _, value = identifier
        return await self._send_announcement(announcement, {"channel": value, "title": "Test video", "url": announcement.get("source_url", "")})

    @tasks.loop(seconds=60)
    async def youtube_task(self):
        if not config.YOUTUBE_API_KEY:
            return
        data = store.load()
        announcements = [a for a in data["announcements"] if a.get("type") == "youtube" and a.get("guild_id")]
        if not announcements:
            return
        changed = False
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            channel_cache: dict[str, str | None] = {}
            latest_cache: dict[str, dict | None] = {}
            for announcement in announcements:
                source = announcement.get("source_url", "")
                if not source:
                    continue
                channel_id = announcement.get("youtube_channel_id")
                if not channel_id:
                    key = source.casefold()
                    if key not in channel_cache:
                        channel_cache[key] = await self._resolve_channel_id(session, source)
                    channel_id = channel_cache[key]
                    if not channel_id:
                        continue
                    announcement["youtube_channel_id"] = channel_id
                    changed = True
                if channel_id not in latest_cache:
                    latest_cache[channel_id] = await self._get_latest_video(session, channel_id)
                video = latest_cache[channel_id]
                if not video:
                    continue
                if announcement.get("last_video_id") != video["video_id"]:
                    if await self._send_announcement(announcement, video):
                        announcement["last_video_id"] = video["video_id"]
                        changed = True
        if changed:
            store.save(data)

    @youtube_task.before_loop
    async def before_youtube_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(YouTubeCog(bot))
