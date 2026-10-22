"""Guild API credential configuration commands."""

import discord
from discord.ext import commands

import api_access
import api_credentials
import checks
import integration_config


class TwitchAPIView(discord.ui.Modal, title="Configure Twitch"):
    client_id = discord.ui.TextInput(label="Client ID", min_length=8, max_length=512)
    client_secret = discord.ui.TextInput(label="Client Secret", min_length=8, max_length=512)

    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        client_id = str(self.client_id.value).strip()
        client_secret = str(self.client_secret.value).strip()
        if not client_id or not client_secret or "\x00" in client_id or "\x00" in client_secret:
            return await interaction.response.send_message("❌ Invalid Twitch credentials.", ephemeral=True)
        api_credentials.set_credentials(self.guild_id, "twitch", {"client_id": client_id, "client_secret": client_secret})
        await interaction.response.send_message("✅ Twitch API configured for this server.", ephemeral=True)


class YouTubeAPIView(discord.ui.Modal, title="Configure YouTube"):
    api_key = discord.ui.TextInput(label="API Key", min_length=8, max_length=512)

    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        key = str(self.api_key.value).strip()
        if not key or "\x00" in key:
            return await interaction.response.send_message("❌ Invalid YouTube API key.", ephemeral=True)
        api_credentials.set_credentials(self.guild_id, "youtube", {"api_key": key})
        await interaction.response.send_message("✅ YouTube API configured for this server.", ephemeral=True)


class InstagramAPIView(discord.ui.Modal, title="Configure Instagram"):
    access_token = discord.ui.TextInput(label="Instagram API Access Token", min_length=8, max_length=512)
    user_id = discord.ui.TextInput(label="Instagram Professional Account ID", min_length=1, max_length=64)

    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        token = str(self.access_token.value).strip()
        user_id = str(self.user_id.value).strip()
        if not token or "\x00" in token or not user_id.isdigit():
            return await interaction.response.send_message("❌ Invalid Instagram access token or account ID.", ephemeral=True)
        api_credentials.set_credentials(
            self.guild_id, "instagram", {"access_token": token, "user_id": user_id}
        )
        await interaction.response.send_message("✅ Instagram API configured for this server.", ephemeral=True)


class OpenAPIView(discord.ui.View):
    def __init__(self, author_id: int, modal: discord.ui.Modal):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.modal = modal

    @discord.ui.button(label="Configure", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ This button is not for you.", ephemeral=True)
        await interaction.response.send_modal(self.modal)


class APIConfigCog(commands.Cog, name="API Configuration"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="set_api", description="Configure the Twitch, YouTube, or Instagram API for this server.")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def set_api(self, ctx, platform: str):
        platform = platform.lower().strip()
        if platform not in {"twitch", "yt", "youtube", "instagram", "insta"}:
            return await ctx.send("❌ Usage: `v!set_api twitch`, `v!set_api yt` or `v!set_api instagram`.")
        if api_access.is_allowed(ctx.guild.id):
            return await ctx.send("ℹ️ This server uses the main API. No local API configuration is required.")

        if platform == "insta":
            platform = "instagram"
        modal = (
            TwitchAPIView(ctx.guild.id) if platform == "twitch"
            else InstagramAPIView(ctx.guild.id) if platform == "instagram"
            else YouTubeAPIView(ctx.guild.id)
        )
        await ctx.send(f"🔐 **{platform} configuration:** click the button and enter your API credentials in the form.", view=OpenAPIView(ctx.author.id, modal))

    @commands.hybrid_command(name="api_status", description="Show the API configuration status for this server.")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def api_status(self, ctx):
        guild_id = ctx.guild.id
        mode = "main" if api_access.is_allowed(guild_id) else "server"
        twitch = bool(integration_config.get_twitch_credentials(guild_id))
        youtube = bool(integration_config.get_youtube_api_key(guild_id))
        instagram = bool(integration_config.get_instagram_credentials(guild_id))
        await ctx.send(
            f"🔑 API **{mode}** — Twitch: {'🟢 configured' if twitch else '🔴 missing'} | "
            f"YouTube: {'🟢 configured' if youtube else '🔴 missing'} | "
            f"Instagram: {'🟢 configured' if instagram else '🔴 missing'}"
        )

    @commands.hybrid_command(name="clear_api", description="Remove the Twitch, YouTube, or Instagram API configuration for this server.")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def clear_api(self, ctx, platform: str):
        platform = platform.lower().strip()
        if platform == "yt":
            platform = "youtube"
        if platform == "insta":
            platform = "instagram"
        if platform not in {"twitch", "youtube", "instagram"}:
            return await ctx.send("❌ Usage: `v!clear_api twitch`, `v!clear_api yt` or `v!clear_api instagram`.")
        if api_access.is_allowed(ctx.guild.id):
            return await ctx.send("ℹ️ This server uses the main API.")
        removed = api_credentials.remove(ctx.guild.id, platform)
        await ctx.send("🗑️ API configuration removed." if removed else "ℹ️ No API configuration found.")


async def setup(bot: commands.Bot):
    await bot.add_cog(APIConfigCog(bot))
