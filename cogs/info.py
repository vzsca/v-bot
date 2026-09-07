"""Information commands."""

from typing import Optional

import discord
from discord.ext import commands

import checks
from state import state

SNIPE_RETENTION_SECONDS = 15 * 60


class InfoCog(commands.Cog, name="Information"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="snipe", description="Displays a recently deleted message in this channel.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_messages=True)
    @checks.kill_switch_required()
    async def snipe(self, ctx, index: int = 1):
        if not 1 <= index <= 10:
            return await ctx.send("❌ Index must be between 1 and 10.")
        now = discord.utils.utcnow().timestamp()
        msgs = [m for m in state.sniped_messages.get(ctx.channel.id, []) if now - m.get("time", discord.utils.utcnow()).timestamp() <= SNIPE_RETENTION_SECONDS]
        if not msgs or index > len(msgs):
            return await ctx.send("❌ No deleted message found.")
        s = msgs[index - 1]
        embed = discord.Embed(title=f"🗑️ Deleted Message #{index}", description=s.get("content") or "*(no text)*", color=discord.Color.red(), timestamp=s.get("time"))
        avatar = s.get("author_avatar")
        if avatar:
            embed.set_author(name=s.get("author", "Unknown"), icon_url=avatar)
        else:
            embed.set_author(name=s.get("author", "Unknown"))
        attachments = s.get("attachments") or []
        if attachments:
            embed.add_field(name="📎 Attachments", value="\n".join(attachments[:10]), inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="user_info", description="Displays information about a member.")
    @commands.guild_only()
    @checks.kill_switch_required()
    async def user_info(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"Information about {member.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=(member.avatar.url if member.avatar else member.default_avatar.url))
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Username", value=member.name, inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="Account created on", value=member.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(name="Joined the server on", value=(member.joined_at.strftime("%d/%m/%Y %H:%M") if member.joined_at else "Unknown"), inline=True)
        roles = ", ".join(r.mention for r in member.roles if r != ctx.guild.default_role) or "None"
        embed.add_field(name="Roles", value=roles[:1024], inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="server_info", description="Displays information about the server.")
    @commands.guild_only()
    @checks.kill_switch_required()
    async def server_info(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"Information about {guild.name}", color=discord.Color.green())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Created on", value=guild.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(name="Number of channels", value=len(guild.text_channels) + len(guild.voice_channels), inline=True)
        embed.add_field(name="Number of roles", value=len(guild.roles), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", description="Displays a member's avatar.")
    @checks.kill_switch_required()
    async def avatar(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=discord.Color.purple())
        embed.set_image(url=(member.avatar.url if member.avatar else member.default_avatar.url))
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCog(bot))
