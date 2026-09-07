"""Guild API credential configuration commands."""

import discord
from discord.ext import commands

import api_access
import api_credentials
import checks
import integration_config


class TwitchAPIView(discord.ui.Modal, title="Configurer Twitch"):
    client_id = discord.ui.TextInput(label="Client ID", min_length=8, max_length=512)
    client_secret = discord.ui.TextInput(label="Client Secret", min_length=8, max_length=512)

    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        client_id = str(self.client_id.value).strip()
        client_secret = str(self.client_secret.value).strip()
        if not client_id or not client_secret or "\x00" in client_id or "\x00" in client_secret:
            return await interaction.response.send_message("❌ Identifiants Twitch invalides.", ephemeral=True)
        api_credentials.set_credentials(self.guild_id, "twitch", {"client_id": client_id, "client_secret": client_secret})
        await interaction.response.send_message("✅ API Twitch configurée pour ce serveur.", ephemeral=True)


class YouTubeAPIView(discord.ui.Modal, title="Configurer YouTube"):
    api_key = discord.ui.TextInput(label="API Key", min_length=8, max_length=512)

    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        key = str(self.api_key.value).strip()
        if not key or "\x00" in key:
            return await interaction.response.send_message("❌ Clé YouTube invalide.", ephemeral=True)
        api_credentials.set_credentials(self.guild_id, "youtube", {"api_key": key})
        await interaction.response.send_message("✅ API YouTube configurée pour ce serveur.", ephemeral=True)


class OpenAPIView(discord.ui.View):
    def __init__(self, author_id: int, modal: discord.ui.Modal):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.modal = modal

    @discord.ui.button(label="Configurer", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Ce bouton ne t'est pas destiné.", ephemeral=True)
        await interaction.response.send_modal(self.modal)


class APIConfigCog(commands.Cog, name="API Configuration"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="set_api", description="Configure the Twitch or YouTube API for this server.")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def set_api(self, ctx, platform: str):
        platform = platform.lower().strip()
        if platform not in {"twitch", "yt", "youtube"}:
            return await ctx.send("❌ Utilisation : `v!set_api twitch` ou `v!set_api yt`.")
        if api_access.is_allowed(ctx.guild.id):
            return await ctx.send("ℹ️ Ce serveur utilise l'API principale. Aucune API locale n'est nécessaire.")

        modal = TwitchAPIView(ctx.guild.id) if platform == "twitch" else YouTubeAPIView(ctx.guild.id)
        await ctx.send(f"🔐 Configuration **{platform}** : clique sur le bouton puis renseigne ta clé dans le formulaire.", view=OpenAPIView(ctx.author.id, modal))

    @commands.hybrid_command(name="api_status", description="Show the API configuration status for this server.")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def api_status(self, ctx):
        guild_id = ctx.guild.id
        mode = "principale" if api_access.is_allowed(guild_id) else "serveur"
        twitch = bool(integration_config.get_twitch_credentials(guild_id))
        youtube = bool(integration_config.get_youtube_api_key(guild_id))
        await ctx.send(f"🔑 API **{mode}** — Twitch: {'🟢 configurée' if twitch else '🔴 absente'} | YouTube: {'🟢 configurée' if youtube else '🔴 absente'}")

    @commands.hybrid_command(name="clear_api", description="Remove the Twitch or YouTube API configuration for this server.")
    @commands.guild_only()
    @checks.owner_or_permission(administrator=True)
    @checks.kill_switch_required()
    async def clear_api(self, ctx, platform: str):
        platform = platform.lower().strip()
        if platform == "yt":
            platform = "youtube"
        if platform not in {"twitch", "youtube"}:
            return await ctx.send("❌ Utilisation : `v!clear_api twitch` ou `v!clear_api yt`.")
        if api_access.is_allowed(ctx.guild.id):
            return await ctx.send("ℹ️ Ce serveur utilise l'API principale.")
        removed = api_credentials.remove(ctx.guild.id, platform)
        await ctx.send("🗑️ Configuration API supprimée." if removed else "ℹ️ Aucune configuration trouvée.")


async def setup(bot: commands.Bot):
    await bot.add_cog(APIConfigCog(bot))
