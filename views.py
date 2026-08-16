"""
UI components (dropdown menus, buttons) used by the
v!servers command. Kept separate to keep cogs/owner.py focused on commands.
"""

import discord
from discord.ui import View, Select

import checks
from state import state


class GuildActionsView(View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=120)
        self.guild = guild

    @discord.ui.button(label="📩 Invite", style=discord.ButtonStyle.green)
    async def invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not checks.is_permanent_owner(interaction.user.id):
            return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)

        for channel in self.guild.text_channels:
            if channel.permissions_for(self.guild.me).create_instant_invite:
                invite = await channel.create_invite(max_age=3600, max_uses=1)
                return await interaction.response.send_message(invite.url, ephemeral=True)

        await interaction.response.send_message("❌ Unable to create an invite", ephemeral=True)


class ServersMenu(View):
    def __init__(self, guilds):
        super().__init__(timeout=120)

        options = [
            discord.SelectOption(label=g.name[:100], value=str(g.id), description=f"ID: {g.id}")
            for g in guilds
        ]

        self.select = Select(placeholder="Choose a server", options=options)
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        guild_id = int(self.select.values[0])
        guild = interaction.client.get_guild(guild_id)

        if not guild:
            return await interaction.response.send_message("Server not found.", ephemeral=True)

        embed = discord.Embed(
            title=f"📌 {guild.name}",
            description=f"ID: {guild.id}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Actions", value="🟢 Use the buttons below", inline=False)

        await interaction.response.send_message(
            embed=embed,
            view=GuildActionsView(guild),
            ephemeral=True,
        )"""
Composants d'interface (menus déroulants, boutons) utilisés par la commande
v!servers. Séparés du reste pour garder cogs/owner.py centré sur les commandes.
"""

import discord
from discord.ui import View, Select

import checks
from state import state


class GuildActionsView(View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=120)
        self.guild = guild
    @discord.ui.button(label="📩 Invite", style=discord.ButtonStyle.green)
    async def invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not checks.is_permanent_owner(interaction.user.id):
            return await interaction.response.send_message("❌ Non autorisé", ephemeral=True)

        for channel in self.guild.text_channels:
            if channel.permissions_for(self.guild.me).create_instant_invite:
                invite = await channel.create_invite(max_age=3600, max_uses=1)
                return await interaction.response.send_message(invite.url, ephemeral=True)

        await interaction.response.send_message("❌ Impossible de créer une invite", ephemeral=True)


class ServersMenu(View):
    def __init__(self, guilds):
        super().__init__(timeout=120)

        options = [
            discord.SelectOption(label=g.name[:100], value=str(g.id), description=f"ID: {g.id}")
            for g in guilds
        ]

        self.select = Select(placeholder="Choisis un serveur", options=options)
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        guild_id = int(self.select.values[0])
        guild = interaction.client.get_guild(guild_id)

        if not guild:
            return await interaction.response.send_message("Serveur introuvable.", ephemeral=True)

        embed = discord.Embed(
            title=f"📌 {guild.name}",
            description=f"ID: {guild.id}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Actions", value="🟢 Utilise les boutons ci-dessous", inline=False)

        await interaction.response.send_message(
            embed=embed,
            view=GuildActionsView(guild),
            ephemeral=True,
        )
