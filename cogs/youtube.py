"""YouTube integration with per-guild API credentials and announcements."""

import logging
from urllib.parse import urlparse

import aiohttp
from discord.ext import commands, tasks

import announcement_store as store
import integration_config

logger = logging.getLogger("v-bot")
YOUTUBE_API_URL = "https://youtube.googleapis.com"


class YouTubeCog(commands.Cog, name="YouTube"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._channel_cache: dict[tuple[int, str], str] = {}
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

    async def _api_get(self, session: aiohttp.ClientSession, guild_id: int, endpoint: str, params: dict) -> tuple[dict | None, int | None]:
        api_key = integration_config.get_youtube_api_key(guild_id)
        if not api_key:
            return None, None
        try:
            async with session.get(f"{YOUTUBE_API_URL}/{endpoint}", params={**params, "key": api_key}) as response:
                if response.status != 200:
                    if response.status in {403, 429}:
                        logger.warning("YouTube API limit/error HTTP %s for guild %s.", response.status, guild_id)
                    return None, response.status
                return await response.json(), response.status
        except (aiohttp.ClientError, ValueError):
            logger.exception("YouTube API request failed for guild %s.", guild_id)
            return None, None

    async def _resolve_channel_id(self, session: aiohttp.ClientSession, guild_id: int, source_url: str) -> str | None:
        identifier = self._extract_identifier(source_url)
        if not identifier:
            return None
        kind, value = identifier
        if kind == "channel_id":
            return value
        cache_key = (guild_id, f"{kind}:{value}")
        if cache_key in self._channel_cache:
            return self._channel_cache[cache_key]
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
            self._channel_cache[cache_key] = channel_id
        return channel_id

    async def _get_latest_video(self, session: aiohttp.ClientSession, guild_id: int, channel_id: str) -> dict | None:
        data, status = await self._api_get(session, guild_id, "youtube/v3/search", {"part": "snippet", "channelId": channel_id, "order": "date", "type": "video", "maxResults": 1})
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
            logger.exception("Failed to send YouTube announcement for guild %s.", guild_id)
            return False

    async def test_announcement(self, announcement: dict) -> bool:
        identifier = self._extract_identifier(announcement.get("source_url", ""))
        if not identifier:
            return False
        _, value = identifier
        return await self._send_announcement(announcement, {"channel": value, "title": "Test video", "url": announcement.get("source_url", "")})

    @tasks.loop(seconds=60)
    async def youtube_task(self):
        data = store.load()
        announcements = [a for a in data["announcements"] if a.get("type") == "youtube" and a.get("guild_id")]
        if not announcements:
            return
        changed = False
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            latest_cache: dict[tuple[int, str], dict | None] = {}
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
