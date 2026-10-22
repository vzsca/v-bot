"""Instagram video/Reel announcements via the official Instagram Graph API."""

import asyncio
import logging
import time
from urllib.parse import urlparse

import aiohttp
import discord
from discord.ext import commands, tasks

import announcement_store as store
import checks
import integration_config

logger = logging.getLogger("v-bot")
GRAPH_API_URL = "https://graph.facebook.com/v23.0"
POLL_INTERVAL_SECONDS = 120
BACKOFF_SECONDS = 120


class InstagramCog(commands.Cog, name="Instagram"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._session = None
        self._backoff_until = {}
        self.instagram_task.start()

    def cog_unload(self):
        self.instagram_task.cancel()
        if self._session and not self._session.closed:
            asyncio.create_task(self._session.close())
        self._session = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    @commands.command(name="create_instagram_annonce")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def create_instagram_annonce(self, ctx):
        """Create an Instagram-only video announcement."""
        if not integration_config.get_instagram_credentials(ctx.guild.id):
            return await ctx.send(
                "❌ Instagram Graph API is not configured. Set INSTAGRAM_ACCESS_TOKEN and "
                "INSTAGRAM_USER_ID in .env, then restart the bot."
            )

        def check(message):
            return message.author.id == ctx.author.id and message.channel.id == ctx.channel.id

        await ctx.send("📸 Send the Instagram account URL (example: https://www.instagram.com/username/).")
        try:
            response = await self.bot.wait_for("message", timeout=60, check=check)
        except TimeoutError:
            return await ctx.send("⏰ Time expired.")
        source_url = response.content.strip()
        username = self._username_from_url(source_url)
        if not username:
            return await ctx.send("❌ Invalid Instagram account URL.")
        token, user_id = integration_config.get_instagram_credentials(ctx.guild.id)
        configured_username = await self._configured_username(token, user_id)
        if not configured_username:
            return await ctx.send("❌ Unable to validate the configured Instagram account. Check the token and account ID.")
        if username.casefold() != configured_username:
            return await ctx.send(
                f"❌ The configured Instagram account is @{configured_username}. "
                "Update INSTAGRAM_USER_ID/token to monitor a different account."
            )
        await ctx.send("💬 Send the announcement text. Placeholders: {channel}, {title}, {url}.")
        try:
            response = await self.bot.wait_for("message", timeout=60, check=check)
        except TimeoutError:
            return await ctx.send("⏰ Time expired.")
        message = response.content.strip()
        if not message:
            return await ctx.send("❌ The announcement message cannot be empty.")
        await ctx.send("📢 Mention the target Discord channel (for example #announcements).")
        def channel_check(m):
            return check(m) and bool(m.channel_mentions) and m.channel_mentions[0].guild.id == ctx.guild.id
        try:
            response = await self.bot.wait_for("message", timeout=60, check=channel_check)
        except TimeoutError:
            return await ctx.send("⏰ Time expired.")
        target = response.channel_mentions[0]
        me = ctx.guild.me
        if me is None or not target.permissions_for(me).send_messages:
            return await ctx.send("❌ I cannot send messages in that channel.")

        def add_announcement(data):
            return store.add(data, {
                "guild_id": ctx.guild.id,
                "type": "instagram",
                "source_url": source_url,
                "message": message,
                "channel_id": target.id,
                "was_live": None,
                "last_video_id": None,
            })
        saved, announcement = store.transaction(add_announcement)
        if not saved or not announcement:
            return await ctx.send("❌ Failed to save the announcement.")
        await ctx.send(
            f"✅ Instagram video announcement #{announcement['id']} created in {target.mention}. "
            "Only video/Reel media will be announced; photos are ignored."
        )

    @staticmethod
    def _username_from_url(url: str) -> str | None:
        try:
            parsed = urlparse(url.strip())
            if parsed.scheme not in {"http", "https"} or parsed.netloc.lower().split(":")[0] not in {
                "instagram.com", "www.instagram.com",
            }:
                return None
            parts = [part for part in parsed.path.strip("/").split("/") if part]
            if len(parts) != 1 or parts[0].lower() in {"reel", "reels", "p", "stories", "explore"}:
                return None
            username = parts[0].lstrip("@")
            return username if username and all(c.isalnum() or c in "._" for c in username) else None
        except ValueError:
            return None

    async def _configured_username(self, token: str, user_id: str) -> str | None:
        session = await self._get_session()
        try:
            async with session.get(
                f"{GRAPH_API_URL}/{user_id}",
                params={"fields": "username", "access_token": token},
            ) as response:
                if response.status != 200:
                    logger.warning("Unable to resolve configured Instagram account (HTTP %s).", response.status)
                    return None
                payload = await response.json()
                username = payload.get("username")
                return username.casefold() if isinstance(username, str) else None
        except (aiohttp.ClientError, ValueError):
            logger.exception("Unable to resolve configured Instagram account.")
            return None

    async def _latest_video(self, token: str, user_id: str):
        credential_key = (token, user_id)
        if time.time() < self._backoff_until.get(credential_key, 0):
            return None
        session = await self._get_session()
        params = {
            "fields": "id,caption,media_type,media_product_type,permalink,timestamp,username",
            "limit": "10",
            "access_token": token,
        }
        try:
            async with session.get(f"{GRAPH_API_URL}/{user_id}/media", params=params) as response:
                if response.status in {400, 401, 403, 429}:
                    self._backoff_until[credential_key] = time.time() + BACKOFF_SECONDS
                    logger.warning("Instagram Graph API returned HTTP %s; backing off.", response.status)
                    return None
                if response.status != 200:
                    logger.warning("Instagram Graph API returned HTTP %s.", response.status)
                    return None
                payload = await response.json()
        except (aiohttp.ClientError, ValueError):
            logger.exception("Instagram Graph API request failed.")
            return None

        return self._select_latest_video(payload.get("data", []))

    @staticmethod
    def _select_latest_video(media):
        """Select the first valid video/Reel and ignore image-only posts."""
        if not isinstance(media, list):
            return None
        return next(
            (
                item for item in media
                if isinstance(item, dict)
                and item.get("media_type") == "VIDEO"
                and item.get("id")
                and item.get("permalink")
            ),
            None,
        )

    @staticmethod
    def _format_message(message: str, video: dict) -> str:
        values = {
            "channel": video.get("username", ""),
            "title": video.get("caption", "") or "Nouvelle vidéo Instagram",
            "url": video.get("permalink", ""),
        }
        for key, value in values.items():
            message = message.replace("{" + key + "}", str(value))
        return message[:2000]

    async def _send_announcement(self, announcement: dict, video: dict) -> bool:
        try:
            guild_id = int(announcement["guild_id"])
            channel_id = int(announcement["channel_id"])
        except (KeyError, TypeError, ValueError):
            return False
        channel = self.bot.get_channel(channel_id)
        if channel is None or getattr(getattr(channel, "guild", None), "id", None) != guild_id:
            logger.warning("Blocked Instagram announcement with mismatched guild/channel.")
            return False
        try:
            await channel.send(
                self._format_message(announcement.get("message", ""), video),
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return True
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            logger.warning("Failed to send Instagram announcement for guild %s.", guild_id)
            return False

    async def test_announcement(self, announcement: dict) -> bool:
        username = self._username_from_url(announcement.get("source_url", ""))
        if not username:
            return False
        return await self._send_announcement(announcement, {
            "username": username,
            "caption": "Test video Instagram (aucune publication réelle)",
            "permalink": announcement.get("source_url", ""),
        })

    async def _poll_instagram_announcements(self):
        data = store.load()
        announcements = [
            item for item in data["announcements"]
            if item.get("type") == "instagram" and item.get("guild_id")
        ]
        if not announcements:
            return

        # Credentials are resolved per guild; only identical credentials are grouped.
        groups = {}
        for announcement in announcements:
            try:
                guild_id = int(announcement["guild_id"])
            except (KeyError, TypeError, ValueError):
                continue
            credentials = integration_config.get_instagram_credentials(guild_id)
            if not credentials:
                continue
            groups.setdefault(credentials, []).append(announcement)

        updates = {}
        for (token, user_id), grouped_announcements in groups.items():
            video = await self._latest_video(token, user_id)
            if not video:
                continue

            for announcement in grouped_announcements:
                key = (announcement.get("guild_id"), announcement.get("id"))
                previous_id = announcement.get("last_video_id")
                if previous_id is None:
                    # First poll establishes a baseline; do not spam old posts.
                    updates[key] = video["id"]
                elif previous_id != video["id"] and await self._send_announcement(announcement, video):
                    updates[key] = video["id"]

        if updates:
            def apply_updates(current):
                for item in current["announcements"]:
                    key = (item.get("guild_id"), item.get("id"))
                    if key in updates:
                        item["last_video_id"] = updates[key]
            store.transaction(apply_updates)

    @tasks.loop(seconds=POLL_INTERVAL_SECONDS)
    async def instagram_task(self):
        await self._poll_instagram_announcements()

    @instagram_task.before_loop
    async def before_instagram_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(InstagramCog(bot))
