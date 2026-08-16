"""Information commands, accessible to everyone (no owner check).

All commands are hybrid commands: available as slash commands (/) and
prefix commands (v!).
"""

from typing import Optional

import discord
from discord.ext import commands

import checks
from state import state


class InfoCog(commands.Cog, name="Information"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="snipe", description="Displays a recently deleted message in this channel.")
    @checks.kill_switch_required()
    async def snipe(self, ctx, index: int = 1):
        msgs = state.sniped_messages.get(ctx.channel.id, [])

        if not msgs or index < 1 or index > len(msgs):
            return await ctx.send("❌ No deleted message found.")

        s = msgs[index - 1]

        embed = discord.Embed(
            title=f"🗑️ Deleted Message #{index}",
            description=s["content"],
            color=discord.Color.red(),
            timestamp=s["time"],
        )
        embed.set_author(name=s["author"], icon_url=s["author_avatar"])

        if s["attachments"]:
            embed.add_field(name="📎 Attachments", value="\n".join(s["attachments"]), inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="user_info", description="Displays information about a member.")
    @commands.guild_only()
    @checks.kill_switch_required()
    async def user_info(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"Information about {member.display_name}", color=discord.Color.blue())
        avatar_url = member.avatar.url if getattr(member, "avatar", None) else member.default_avatar.url
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Username", value=member.name, inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(
            name="Account created on",
            value=member.created_at.strftime("%d/%m/%Y %H:%M"),
            inline=True,
        )
        embed.add_field(
            name="Joined the server on",
            value=(member.joined_at.strftime("%d/%m/%Y %H:%M") if member.joined_at else "Unknown"),
            inline=True,
        )
        roles = ", ".join(r.mention for r in member.roles if r != ctx.guild.default_role) or "None"
        embed.add_field(name="Roles", value=roles, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="server_info", description="Displays information about the server.")
    @commands.guild_only()
    @checks.kill_switch_required()
    async def server_info(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"Information about {guild.name}", color=discord.Color.green())
        embed.set_thumbnail(url=guild.icon.url if getattr(guild, "icon", None) else None)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(
            name="Created on",
            value=guild.created_at.strftime("%d/%m/%Y %H:%M"),
            inline=True,
        )
        embed.add_field(
            name="Number of channels",
            value=len(guild.text_channels) + len(guild.voice_channels),
            inline=True,
        )
        embed.add_field(name="Number of roles", value=len(guild.roles), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", description="Displays a member's avatar.")
    @checks.kill_switch_required()
    async def avatar(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        avatar_url = member.avatar.url if getattr(member, "avatar", None) else member.default_avatar.url
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=discord.Color.purple())
        embed.set_image(url=avatar_url)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCog(bot))"""Commandes d'information, accessibles à tous (pas de check owner).

Toutes en hybrid commands : disponibles en slash (/) et en prefix (v!).
"""

from typing import Optional

import discord
from discord.ext import commands

import checks
from state import state


class InfoCog(commands.Cog, name="Informations"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="snipe", description="Affiche un message supprimé récemment dans ce salon.")
    @checks.kill_switch_required()
    async def snipe(self, ctx, index: int = 1):
        msgs = state.sniped_messages.get(ctx.channel.id, [])

        if not msgs or index < 1 or index > len(msgs):
            return await ctx.send("❌ Aucun message supprimé trouvé.")

        s = msgs[index - 1]

        embed = discord.Embed(
            title=f"🗑️ Message supprimé #{index}",
            description=s["content"],
            color=discord.Color.red(),
            timestamp=s["time"],
        )
        embed.set_author(name=s["author"], icon_url=s["author_avatar"])

        if s["attachments"]:
            embed.add_field(name="📎 Pièces jointes", value="\n".join(s["attachments"]), inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="user_info", description="Affiche les informations d'un membre.")
    @commands.guild_only()
    @checks.kill_switch_required()
    async def user_info(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"Informations sur {member.display_name}", color=discord.Color.blue())
        avatar_url = member.avatar.url if getattr(member, "avatar", None) else member.default_avatar.url
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Nom d'utilisateur", value=member.name, inline=True)
        embed.add_field(name="Surnom", value=member.nick or "Aucun", inline=True)
        embed.add_field(name="Compte créé le", value=member.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(
            name="A rejoint le serveur",
            value=(member.joined_at.strftime("%d/%m/%Y %H:%M") if member.joined_at else "Inconnu"),
            inline=True,
        )
        roles = ", ".join(r.mention for r in member.roles if r != ctx.guild.default_role) or "Aucun rôle"
        embed.add_field(name="Rôles", value=roles, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="server_info", description="Affiche les informations du serveur.")
    @commands.guild_only()
    @checks.kill_switch_required()
    async def server_info(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"Informations sur {guild.name}", color=discord.Color.green())
        embed.set_thumbnail(url=guild.icon.url if getattr(guild, "icon", None) else None)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Propriétaire", value=guild.owner.mention if guild.owner else "Inconnu", inline=True)
        embed.add_field(name="Membres", value=guild.member_count, inline=True)
        embed.add_field(name="Créé le", value=guild.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(name="Nombre de salons", value=len(guild.text_channels) + len(guild.voice_channels), inline=True)
        embed.add_field(name="Nombre de rôles", value=len(guild.roles), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", description="Affiche l'avatar d'un membre.")
    @checks.kill_switch_required()
    async def avatar(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        avatar_url = member.avatar.url if getattr(member, "avatar", None) else member.default_avatar.url
        embed = discord.Embed(title=f"Avatar de {member.display_name}", color=discord.Color.purple())
        embed.set_image(url=avatar_url)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCog(bot))
