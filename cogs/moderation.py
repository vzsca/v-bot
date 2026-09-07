"""Moderation commands with centralized permission and Discord hierarchy checks."""

from datetime import timedelta

import discord
from discord.ext import commands

import checks

MAX_MUTE_MINUTES = 28 * 24 * 60
MAX_SLOWMODE_SECONDS = 6 * 60 * 60
MAX_CLEAR_AMOUNT = 100


class ModerationCog(commands.Cog, name="Moderation"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _target_error(self, ctx, member: discord.Member, action: str) -> str | None:
        if not checks.can_manage_member(ctx, member):
            return f"❌ You cannot {action} this member because of Discord's member hierarchy."
        if not checks.can_bot_manage_member(ctx, member):
            return f"❌ I cannot {action} this member because of my role hierarchy."
        return None

    @commands.hybrid_command(name="mute", description="Temporarily mutes a member.")
    @commands.guild_only()
    @checks.owner_or_permission(moderate_members=True)
    @checks.kill_switch_required()
    async def mute(self, ctx, member: discord.Member, minutes: int, *, reason: str = "No reason specified"):
        if not 1 <= minutes <= MAX_MUTE_MINUTES:
            await ctx.send(f"❌ Mute duration must be between 1 minute and {MAX_MUTE_MINUTES} minutes.")
            return
        error = self._target_error(ctx, member, "mute")
        if error:
            await ctx.send(error)
            return
        try:
            await member.timeout(timedelta(minutes=minutes), reason=reason)
            await ctx.send(f"🔇 {member.mention} has been muted for {minutes} minute(s).\nReason: {reason}")
            try:
                await member.send(f"🔇 You have been muted on **{ctx.guild.name}** for {minutes} minute(s).\nReason: {reason}")
            except discord.Forbidden:
                pass
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to mute this member.")
        except discord.HTTPException:
            await ctx.send("⚠️ Discord rejected the moderation request.")

    @commands.hybrid_command(name="unmute", description="Removes a member's mute.")
    @commands.guild_only()
    @checks.owner_or_permission(moderate_members=True)
    @checks.kill_switch_required()
    async def unmute(self, ctx, member: discord.Member):
        error = self._target_error(ctx, member, "unmute")
        if error:
            await ctx.send(error)
            return
        try:
            await member.timeout(None)
            await ctx.send(f"🔊 {member.mention} has been unmuted.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to unmute this member.")
        except discord.HTTPException:
            await ctx.send("⚠️ Discord rejected the moderation request.")

    @commands.hybrid_command(name="kick", description="Kicks a member from the server.")
    @commands.guild_only()
    @checks.owner_or_permission(kick_members=True)
    @checks.kill_switch_required()
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason specified"):
        error = self._target_error(ctx, member, "kick")
        if error:
            await ctx.send(error)
            return
        try:
            await member.kick(reason=reason)
            await ctx.send(f"👢 {member.mention} has been kicked. Reason: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to kick this member.")
        except discord.HTTPException:
            await ctx.send("⚠️ Discord rejected the moderation request.")

    @commands.hybrid_command(name="ban", description="Bans a member from the server.")
    @commands.guild_only()
    @checks.owner_or_permission(ban_members=True)
    @checks.kill_switch_required()
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason specified"):
        error = self._target_error(ctx, member, "ban")
        if error:
            await ctx.send(error)
            return
        try:
            await member.ban(reason=reason)
            await ctx.send(f"⛔ {member.mention} has been banned. Reason: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to ban this member.")
        except discord.HTTPException:
            await ctx.send("⚠️ Discord rejected the moderation request.")

    @commands.hybrid_command(name="unban", description="Unbans a user using their ID.")
    @commands.guild_only()
    @checks.owner_or_permission(ban_members=True)
    @checks.kill_switch_required()
    async def unban(self, ctx, user_id: int):
        if user_id <= 0:
            await ctx.send("❌ Invalid user ID.")
            return
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"✅ {user.mention} has been unbanned.")
        except discord.NotFound:
            await ctx.send("❌ The user is not banned or the ID is invalid.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to unban this user.")
        except discord.HTTPException:
            await ctx.send("⚠️ Discord rejected the moderation request.")

    @commands.hybrid_command(name="give_role", description="Gives a role to a member.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_roles=True)
    @checks.kill_switch_required()
    async def give_role(self, ctx, member: discord.Member, role: discord.Role):
        if role in member.roles:
            await ctx.send(f"⚠️ {member.mention} already has the role {role.mention}.")
            return
        if not checks.can_manage_member(ctx, member):
            await ctx.send("❌ You cannot modify this member because of Discord's member hierarchy.")
            return
        if ctx.author.id != ctx.guild.owner_id and role >= ctx.author.top_role:
            await ctx.send("❌ You cannot assign a role at or above your highest role.")
            return
        if not checks.can_manage_role(ctx, role):
            await ctx.send("❌ I cannot assign this role because it is not assignable by the bot.")
            return
        try:
            await member.add_roles(role, reason=f"Added by {ctx.author}")
            await ctx.send(f"✅ Role {role.mention} given to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to give this role.")
        except discord.HTTPException:
            await ctx.send("⚠️ Discord rejected the role change.")

    @commands.hybrid_command(name="unlock", description="Restores the channel's default message permission.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def unlock(self, ctx):
        try:
            # Remove only the bot's @everyone overwrite instead of forcing True.
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
            await ctx.send("🔓 Channel unlocked.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to modify this channel.")
        except discord.HTTPException:
            await ctx.send("⚠️ Discord rejected the channel change.")

    @commands.hybrid_command(name="lock", description="Locks the channel for @everyone.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def lock(self, ctx):
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send("🔒 Channel locked.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to modify this channel.")
        except discord.HTTPException:
            await ctx.send("⚠️ Discord rejected the channel change.")

    @commands.hybrid_command(name="slowmode", description="Configures the channel's slowmode.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def slowmode(self, ctx, seconds: int):
        if not 0 <= seconds <= MAX_SLOWMODE_SECONDS:
            await ctx.send(f"❌ Slowmode must be between 0 and {MAX_SLOWMODE_SECONDS} seconds.")
            return
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            await ctx.send(f"⏳ Slowmode set to {seconds} seconds.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to modify this channel.")
        except discord.HTTPException:
            await ctx.send("⚠️ Discord rejected the channel change.")

    @commands.hybrid_command(name="clear", description="Deletes 1 to 100 messages from the channel.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_messages=True)
    @checks.kill_switch_required()
    async def clear(self, ctx, amount: int):
        if not 1 <= amount <= MAX_CLEAR_AMOUNT:
            await ctx.send(f"❌ Amount must be between 1 and {MAX_CLEAR_AMOUNT}.")
            return
        try:
            await ctx.channel.purge(limit=amount + 1)
            await ctx.send(f"✅ Up to {amount} messages deleted.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to delete messages here.")
        except discord.HTTPException:
            await ctx.send("⚠️ Discord rejected the deletion request.")


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
