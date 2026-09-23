"""Secure UI components used by the owner server panel."""

import discord
from discord.ui import Select, View

import api_access
import checks
import security_log


class _OwnerOnlyView(View):
    def __init__(self, owner_id: int, *, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not checks.is_permanent_owner(interaction.user.id) or interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            return False
        return True


class ConfirmLeaveView(_OwnerOnlyView):
    def __init__(self, guild, owner_id):
        super().__init__(owner_id)
        self.guild = guild

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        button.disabled = True
        self.confirm.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        button.disabled = True
        self.cancel.disabled = True
        await interaction.response.defer()

        try:
            await self.guild.leave()
        except discord.HTTPException:
            security_log.log_security_event(
                f"Failed to leave guild {self.guild.name} ({self.guild.id})",
                actor=f"{interaction.user} ({interaction.user.id})",
            )
            await interaction.edit_original_response(
                content="❌ Unable to remove v-bot from this server.",
                embed=None,
                view=None,
            )
            return

        security_log.log_security_event(
            f"Bot left guild {self.guild.name} ({self.guild.id})",
            actor=f"{interaction.user} ({interaction.user.id})",
        )
        embed = discord.Embed(
            title="Bot removed",
            description=f"v-bot has left **{self.guild.name}**.",
            color=discord.Color.red(),
        )
        await interaction.edit_original_response(content=None, embed=embed, view=None)


class GuildActionsView(_OwnerOnlyView):
    def __init__(self, guild, owner_id):
        super().__init__(owner_id)
        self.guild = guild

    @discord.ui.button(label="📩 Invite", style=discord.ButtonStyle.green)
    async def invite(self, interaction, button):
        me = self.guild.me
        if me is None:
            return await interaction.response.send_message("❌ Bot member not found.", ephemeral=True)
        for channel in self.guild.text_channels:
            if channel.permissions_for(me).create_instant_invite:
                try:
                    invite = await channel.create_invite(max_age=3600, max_uses=1)
                except (discord.Forbidden, discord.HTTPException):
                    continue
                return await interaction.response.send_message(invite.url, ephemeral=True)
        await interaction.response.send_message("❌ Unable to create an invite.", ephemeral=True)

    @discord.ui.button(label="🔑 API access", style=discord.ButtonStyle.blurple)
    async def api_access_toggle(self, interaction, button):
        allowed = api_access.is_allowed(self.guild.id)
        if api_access.set_allowed(self.guild.id, not allowed):
            text = f"{'🔒' if allowed else '🔓'} API configuration {'disabled' if allowed else 'enabled'} for **{self.guild.name}**."
        else:
            text = "❌ Unable to update API access."
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.danger)
    async def quit(self, interaction, button):
        embed = discord.Embed(
            title="Remove bot from server?",
            description=f"Are you sure you want v-bot to leave **{self.guild.name}**?",
            color=discord.Color.red(),
        )
        embed.set_footer(text="This action removes the bot from this server.")
        await interaction.response.send_message(
            embed=embed,
            view=ConfirmLeaveView(self.guild, self.owner_id),
            ephemeral=True,
        )


def _server_details_embed(guild):
    owner = guild.owner
    bot_member = guild.me

    owner_value = (
        f"{owner.mention} ({owner})"
        if owner is not None
        else f"Unknown (ID: {guild.owner_id})"
    )
    member_value = f"{guild.member_count:,}" if guild.member_count is not None else "Unknown"

    embed = discord.Embed(
        title=f"📌 {guild.name}",
        description=f"ID: {guild.id}",
        color=discord.Color.blue(),
    )
    embed.add_field(name="Owner", value=owner_value, inline=True)
    embed.add_field(name="Members", value=member_value, inline=True)
    if bot_member is not None and bot_member.joined_at is not None:
        added = bot_member.joined_at
        embed.add_field(
            name="Bot added",
            value=f"{discord.utils.format_dt(added, style='F')}\n{discord.utils.format_dt(added, style='R')}",
            inline=False,
        )
    else:
        embed.add_field(name="Bot added", value="Unknown", inline=False)
    embed.add_field(
        name="API configuration",
        value="🟢 Enabled" if api_access.is_allowed(guild.id) else "🔴 Disabled",
        inline=False,
    )
    return embed


class ServersMenu(_OwnerOnlyView):
    PAGE_SIZE = 25

    def __init__(self, guilds, owner_id, page=0):
        super().__init__(owner_id)
        self.guilds = sorted(guilds, key=lambda g: g.name.casefold())
        self.page = max(0, page)
        self._rebuild()

    def _rebuild(self):
        self.clear_items()
        start = self.page * self.PAGE_SIZE
        current = self.guilds[start:start + self.PAGE_SIZE]
        options = [discord.SelectOption(label=g.name[:100], value=str(g.id), description=f"ID: {g.id} | API: {'ON' if api_access.is_allowed(g.id) else 'OFF'}") for g in current]
        if options:
            select = Select(placeholder=f"Choose a server — page {self.page + 1}", options=options)
            select.callback = self.callback
            self.add_item(select)
        total_pages = max(1, (len(self.guilds) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self.page > 0:
            previous = discord.ui.Button(label="◀ Previous", style=discord.ButtonStyle.secondary)
            previous.callback = self.previous_page
            self.add_item(previous)
        if self.page + 1 < total_pages:
            nxt = discord.ui.Button(label="Next ▶", style=discord.ButtonStyle.secondary)
            nxt.callback = self.next_page
            self.add_item(nxt)

    async def previous_page(self, interaction):
        self.page -= 1
        self._rebuild()
        await interaction.response.edit_message(view=self)

    async def next_page(self, interaction):
        self.page += 1
        self._rebuild()
        await interaction.response.edit_message(view=self)

    async def callback(self, interaction):
        select = next((item for item in self.children if isinstance(item, Select)), None)
        try:
            guild_id = int(select.values[0])
        except (AttributeError, ValueError, IndexError):
            return await interaction.response.send_message("❌ Invalid server selection.", ephemeral=True)
        guild = interaction.client.get_guild(guild_id)
        if not guild:
            return await interaction.response.send_message("❌ Server not found.", ephemeral=True)
        embed = _server_details_embed(guild)
        await interaction.response.send_message(embed=embed, view=GuildActionsView(guild, self.owner_id), ephemeral=True)
