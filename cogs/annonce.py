"""Guild-isolated announcement management."""

import logging
from urllib.parse import urlparse

import discord
from discord.ext import commands

import announcement_store as store
import checks

logger = logging.getLogger("v-bot")


class AnnonceCog(commands.Cog, name="Announcements"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _detect_platform(url: str) -> str | None:
        try:
            parsed = urlparse(url.strip())
            if parsed.scheme not in {"http", "https"}:
                return None
            host = parsed.netloc.lower().split(":")[0]
            if host in {"twitch.tv", "www.twitch.tv"}:
                return "twitch"
            if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
                return "youtube"
        except ValueError:
            pass
        return None

    @staticmethod
    def _next_id(announcements: list[dict]) -> int:
        ids = [a.get("id") for a in announcements if isinstance(a.get("id"), int)]
        return max(ids, default=0) + 1

    @commands.command(name="create_annonce")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def create_annonce(self, ctx):
        def check(message: discord.Message) -> bool:
            return message.author.id == ctx.author.id and message.channel.id == ctx.channel.id

        await ctx.send("📢 Send the Twitch or YouTube channel URL. You have **1 minute**.")
        try:
            response = await self.bot.wait_for("message", timeout=60, check=check)
        except TimeoutError:
            return await ctx.send("⏰ Time expired.")
        source_url = response.content.strip()
        platform = self._detect_platform(source_url)
        if not platform:
            return await ctx.send("❌ Unsupported Twitch/YouTube URL.")

        placeholders = "`{streamer}` `{title}` `{game}` `{url}`" if platform == "twitch" else "`{channel}` `{title}` `{url}`"
        await ctx.send(f"💬 Send the announcement message. Available placeholders: {placeholders}\nYou have **1 minute**.")
        try:
            response = await self.bot.wait_for("message", timeout=60, check=check)
        except TimeoutError:
            return await ctx.send("⏰ Time expired.")
        message = response.content.strip()
        if not message:
            return await ctx.send("❌ The announcement message cannot be empty.")

        await ctx.send("📢 Mention the Discord target channel (for example `#announcements`). You have **1 minute**.")
        def channel_check(m: discord.Message) -> bool:
            return check(m) and bool(m.channel_mentions) and m.channel_mentions[0].guild.id == ctx.guild.id
        try:
            response = await self.bot.wait_for("message", timeout=60, check=channel_check)
        except TimeoutError:
            return await ctx.send("⏰ Time expired.")
        target = response.channel_mentions[0]
        if not target.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send("❌ I cannot send messages in that channel.")

        data = store.load()
        announcements = data["announcements"]
        announcement_id = self._next_id(announcements)
        announcement = {
            "id": announcement_id,
            "guild_id": ctx.guild.id,
            "type": platform,
            "source_url": source_url,
            "message": message,
            "channel_id": target.id,
            "was_live": False if platform == "twitch" else None,
            "last_video_id": None if platform == "youtube" else None,
        }
        announcements.append(announcement)
        if not store.save(data):
            return await ctx.send("❌ Failed to save the announcement.")
        await ctx.send(f"✅ Announcement `{announcement_id}` created for **{ctx.guild.name}** in {target.mention}.")

    @commands.command(name="annonces")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def annonces(self, ctx):
        announcements = store.for_guild(store.load(), ctx.guild.id)
        if not announcements:
            return await ctx.send("📭 No announcements are configured on this server.")
        embed = discord.Embed(title="📢 Announcements", description=f"**{len(announcements)}** configured.", color=discord.Color.purple())
        for a in announcements[:25]:
            channel = f"<#{a.get('channel_id')}>" if a.get("channel_id") else "Unknown"
            status = "🟢 LIVE" if a.get("type") == "twitch" and a.get("was_live") else "🟢 Enabled"
            embed.add_field(name=f"#{a.get('id', '?')} — {str(a.get('type', 'unknown')).capitalize()}", value=f"**Source:** {a.get('source_url', 'Unknown')}\n**Channel:** {channel}\n**Status:** {status}\n**Message:** {a.get('message', 'No message')}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="test_annonce")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def test_annonce(self, ctx, announcement_id: int):
        data = store.load()
        announcement = store.find(data, ctx.guild.id, announcement_id)
        if not announcement:
            return await ctx.send(f"❌ Announcement `{announcement_id}` not found on this server.")
        cog = self.bot.get_cog("Twitch" if announcement.get("type") == "twitch" else "YouTube")
        test = getattr(cog, "test_announcement", None) if cog else None
        if not test:
            return await ctx.send("❌ The required integration is not loaded.")
        try:
            success = await test(announcement)
        except Exception:
            logger.exception("Announcement test failed.")
            success = False
        await ctx.send("✅ Test announcement sent." if success else "❌ Unable to send the test announcement.")

    @commands.command(name="delete_annonce")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def delete_annonce(self, ctx, announcement_id: int):
        data = store.load()
        announcement = store.find(data, ctx.guild.id, announcement_id)
        if not announcement:
            return await ctx.send(f"❌ Announcement `{announcement_id}` not found on this server.")
        data["announcements"].remove(announcement)
        if not store.save(data):
            return await ctx.send("❌ Failed to save the configuration.")
        await ctx.send(f"🗑️ Announcement `{announcement_id}` deleted.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AnnonceCog(bot))
