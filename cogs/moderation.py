"""
Moderation commands.

Commands use centralized permission checks and explicit Discord hierarchy
validation so the bot fails cleanly before attempting an operation it cannot
legally perform.
"""

from datetime import timedelta

import discord
from discord.ext import commands

import checks


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
        if minutes < 1:
            await ctx.send("❌ The mute duration must be at least 1 minute.")
            return

        error = self._target_error(ctx, member, "mute")
        if error:
            await ctx.send(error)
            return

        try:
            await member.timeout(timedelta(minutes=minutes), reason=reason)
            await ctx.send(
                f"🔇 {member.mention} has been muted for {minutes} minute(s).\n"
                f"Reason: {reason}"
            )
            try:
                await member.send(
                    f"🔇 You have been muted on **{ctx.guild.name}** for {minutes} minute(s).\n"
                    f"Reason: {reason}"
                )
            except discord.Forbidden:
                pass
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to mute this member.")
        except Exception:
            await ctx.send("⚠️ An internal error occurred.")

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
            try:
                await member.send(f"🔊 You have been unmuted on the server **{ctx.guild.name}**.")
            except discord.Forbidden:
                pass
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to unmute this member.")
        except Exception:
            await ctx.send("⚠️ An internal error occurred.")

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
            try:
                await member.send(f"👢 You have been kicked from the server **{ctx.guild.name}**.\nReason: {reason}")
            except discord.Forbidden:
                pass
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to kick this member.")
        except Exception:
            await ctx.send("⚠️ An internal error occurred.")

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
            try:
                await member.send(f"⛔ You have been banned from the server **{ctx.guild.name}**.\nReason: {reason}")
            except discord.Forbidden:
                pass
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to ban this member.")
        except Exception:
            await ctx.send("⚠️ An internal error occurred.")

    @commands.hybrid_command(name="unban", description="Unbans a user using their ID.")
    @commands.guild_only()
    @checks.owner_or_permission(ban_members=True)
    @checks.kill_switch_required()
    async def unban(self, ctx, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"✅ {user.mention} has been unbanned.")
            try:
                await user.send(f"✅ You have been unbanned from the server **{ctx.guild.name}**.")
            except discord.Forbidden:
                pass
        except discord.NotFound:
            await ctx.send("❌ The user is not banned or the ID is invalid.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to unban this user.")
        except Exception:
            await ctx.send("⚠️ An internal error occurred.")

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
        if not checks.can_manage_role(ctx, role):
            await ctx.send("❌ I cannot assign this role because it is above my highest role or otherwise not assignable.")
            return
        try:
            await member.add_roles(role, reason=f"Added by {ctx.author}")
            await ctx.send(f"✅ Role {role.mention} given to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to give this role.")
        except Exception:
            await ctx.send("⚠️ An internal error occurred.")

    @commands.hybrid_command(name="unlock", description="Unlocks the channel (allows messages to be sent).")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def unlock(self, ctx):
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await ctx.send("🔓 Channel unlocked.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to modify this channel.")

    @commands.hybrid_command(name="lock", description="Locks the channel (prevents messages from being sent).")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def lock(self, ctx):
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send("🔒 Channel locked.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to modify this channel.")

    @commands.hybrid_command(name="slowmode", description="Configures the channel's slowmode.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def slowmode(self, ctx, seconds: int):
        if seconds < 0:
            await ctx.send("The number of seconds must be positive.")
            return
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            await ctx.send(f"⏳ Slowmode enabled: {seconds} seconds.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to modify this channel.")

    @commands.hybrid_command(name="clear", description="Deletes a specified number of messages from the channel.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_messages=True)
    @checks.kill_switch_required()
    async def clear(self, ctx, amount: int):
        if amount < 1:
            await ctx.send("The number of messages to delete must be ≥ 1.")
            return
        try:
            await ctx.channel.purge(limit=amount + 1)
            await ctx.send(f"✅ {amount} messages deleted.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to delete messages here.")


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
