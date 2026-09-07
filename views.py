"""Secure UI components used by the owner server panel."""

import discord
from discord.ui import View, Select

import checks


class _OwnerOnlyView(View):
    def __init__(self, owner_id: int, *, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not checks.is_permanent_owner(interaction.user.id):
            await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            return False
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ This panel belongs to another owner session.", ephemeral=True)
            return False
        return True


class GuildActionsView(_OwnerOnlyView):
    def __init__(self, guild: discord.Guild, owner_id: int):
        super().__init__(owner_id)
        self.guild = guild

    @discord.ui.button(label="📩 Invite", style=discord.ButtonStyle.green)
    async def invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        me = self.guild.me
        if me is None:
            return await interaction.response.send_message("❌ Bot member not found.", ephemeral=True)

        for channel in self.guild.text_channels:
            if channel.permissions_for(me).create_instant_invite:
                try:
                    invite = await channel.create_invite(max_age=3600, max_uses=1)
                except discord.Forbidden:
                    continue
                except discord.HTTPException:
                    continue
                return await interaction.response.send_message(invite.url, ephemeral=True)

        await interaction.response.send_message("❌ Unable to create an invite.", ephemeral=True)


class ServersMenu(_OwnerOnlyView):
    def __init__(self, guilds, owner_id: int):
        super().__init__(owner_id)
        guilds = list(guilds)
        options = [
            discord.SelectOption(label=g.name[:100], value=str(g.id), description=f"ID: {g.id}")
            for g in guilds[:25]
        ]
        self.select = Select(placeholder="Choose a server", options=options)
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        try:
            guild_id = int(self.select.values[0])
        except (ValueError, IndexError):
            return await interaction.response.send_message("❌ Invalid server selection.", ephemeral=True)

        guild = interaction.client.get_guild(guild_id)
        if not guild:
            return await interaction.response.send_message("❌ Server not found.", ephemeral=True)

        embed = discord.Embed(
            title=f"📌 {guild.name}",
            description=f"ID: {guild.id}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Actions", value="🟢 Use the buttons below", inline=False)
        await interaction.response.send_message(
            embed=embed,
            view=GuildActionsView(guild, self.owner_id),
            ephemeral=True,
        )
