import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import discord
from discord.ext import commands, tasks

import checks
from twitch_api import TwitchAPI


logger = logging.getLogger("v-bot")

CONFIG_FILE = Path(__file__).resolve().parent.parent / "twitch_config.json"


class TwitchCog(commands.Cog, name="Twitch"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.twitch = TwitchAPI()
        self.config = self._load_config()
        self.previous_states = {}

        self.check_streams.start()

    def cog_unload(self):
        self.check_streams.cancel()

    def _load_config(self):
        if not CONFIG_FILE.exists():
            return {}

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=4)

    @staticmethod
    def _extract_username(url: str):
        try:
            parsed = urlparse(url)

            if parsed.netloc.lower() not in (
                "twitch.tv",
                "www.twitch.tv",
            ):
                return None

            username = parsed.path.strip("/").split("/")[0]

            if not username:
                return None

            return username.lower()

        except Exception:
            return None

    @commands.command(name="twitch")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def twitch(self, ctx, url: str = None):
        """Configures Twitch live notifications for the current channel."""

        if not url:
            await ctx.send(
                "❌ Usage: `v!twitch https://twitch.tv/channel`"
            )
            return

        username = self._extract_username(url)

        if not username:
            await ctx.send(
                "❌ Invalid Twitch URL.\n"
                "Use: `https://twitch.tv/channel`"
            )
            return

        guild_id = str(ctx.guild.id)

        self.config[guild_id] = {
            "channel_id": ctx.channel.id,
            "twitch_username": username,
        }

        self._save_config()

        self.previous_states.pop(guild_id, None)

        await ctx.send(
            f"✅ Twitch notifications configured for **{username}**.\n"
            f"📢 Announcements will be sent in {ctx.channel.mention}."
        )

    @tasks.loop(seconds=60)
    async def check_streams(self):
        for guild_id, settings in list(self.config.items()):
            username = settings["twitch_username"]
            channel_id = settings["channel_id"]

            try:
                stream = await self.twitch.get_stream(username)
                is_live = stream is not None

                previous = self.previous_states.get(guild_id, False)

                self.previous_states[guild_id] = is_live

                # Only announce when going from offline -> online.
                if not previous and is_live:
                    guild = self.bot.get_guild(int(guild_id))

                    if not guild:
                        continue

                    channel = guild.get_channel(channel_id)

                    if not channel:
                        continue

                    await self._send_live_notification(
                        channel,
                        stream,
                    )

            except Exception:
                logger.exception(
                    f"Error checking Twitch channel '{username}'."
                )

    @check_streams.before_loop
    async def before_check_streams(self):
        await self.bot.wait_until_ready()

    async def _send_live_notification(self, channel, stream):
        username = stream["user_name"]
        title = stream["title"]
        game = stream.get("game_name") or "Unknown"

        embed = discord.Embed(
            title=f"🔴 {username} is now live!",
            description=title,
            url=f"https://twitch.tv/{username}",
            color=discord.Color.purple(),
        )

        embed.add_field(
            name="🎮 Category",
            value=game,
            inline=True,
        )

        embed.add_field(
            name="👀 Viewers",
            value=str(stream["viewer_count"]),
            inline=True,
        )

        thumbnail = stream.get("thumbnail_url")

        if thumbnail:
            thumbnail = thumbnail.replace("{width}", "1280")
            thumbnail = thumbnail.replace("{height}", "720")
            embed.set_image(url=thumbnail)

        embed.set_footer(text="Twitch")

        view = discord.ui.View()

        button = discord.ui.Button(
            label="Watch stream",
            style=discord.ButtonStyle.link,
            url=f"https://twitch.tv/{username}",
        )

        view.add_item(button)

        await channel.send(
            embed=embed,
            view=view,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(TwitchCog(bot))
