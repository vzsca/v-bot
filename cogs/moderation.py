"""
Moderation commands. All commands use checks.owner_or_permission(...)
for authorization: owner (permanent/temporary) OR the appropriate Discord
permission on the server.

All these commands are "hybrid commands": they work both as
slash commands (/) and prefix commands (v!), with a single definition.
checks.py remains unchanged: a check added via commands.check()
applies the same way regardless of how the command is invoked.
"""

from datetime import timedelta

import discord
from discord.ext import commands

import checks


class ModerationCog(commands.Cog, name="Moderation"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="mute", description="Temporarily mutes a member.")
    @commands.guild_only()
    @checks.owner_or_permission(moderate_members=True)
    @checks.kill_switch_required()
    async def mute(self, ctx, member: discord.Member, minutes: int, *, reason: str = "No reason specified"):
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
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.hybrid_command(name="unmute", description="Removes a member's mute.")
    @commands.guild_only()
    @checks.owner_or_permission(moderate_members=True)
    @checks.kill_switch_required()
    async def unmute(self, ctx, member: discord.Member):
        try:
            await member.timeout(None)
            await ctx.send(f"🔊 {member.mention} has been unmuted.")
            try:
                await member.send(f"🔊 You have been unmuted on the server **{ctx.guild.name}**.")
            except discord.Forbidden:
                await ctx.send(f"❌ I could not send a private message to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to unmute this member.")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.hybrid_command(name="kick", description="Kicks a member from the server.")
    @commands.guild_only()
    @checks.owner_or_permission(kick_members=True)
    @checks.kill_switch_required()
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason specified"):
        try:
            await member.kick(reason=reason)
            await ctx.send(f"👢 {member.mention} has been kicked. Reason: {reason}")
            try:
                await member.send(f"👢 You have been kicked from the server **{ctx.guild.name}**.\nReason: {reason}")
            except discord.Forbidden:
                await ctx.send(f"❌ I could not send a private message to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to kick this member.")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.hybrid_command(name="ban", description="Bans a member from the server.")
    @commands.guild_only()
    @checks.owner_or_permission(ban_members=True)
    @checks.kill_switch_required()
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason specified"):
        try:
            await member.ban(reason=reason)
            await ctx.send(f"⛔ {member.mention} has been banned. Reason: {reason}")
            try:
                await member.send(f"⛔ You have been banned from the server **{ctx.guild.name}**.\nReason: {reason}")
            except discord.Forbidden:
                await ctx.send(f"❌ I could not send a private message to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to ban this member.")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

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
                await ctx.send(f"❌ I could not send a private message to {user.mention}.")
        except discord.NotFound:
            await ctx.send("❌ The user is not banned or the ID is invalid.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to unban this member.")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.hybrid_command(name="give_role", description="Gives a role to a member.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_roles=True)
    @checks.kill_switch_required()
    async def give_role(self, ctx, member: discord.Member, role: discord.Role):
        if role in member.roles:
            await ctx.send(f"⚠️ {member.mention} already has the role {role.mention}.")
            return
        try:
            await member.add_roles(role, reason=f"Added by {ctx.author}")
            await ctx.send(f"✅ Role {role.mention} given to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to give this role (check the role hierarchy).")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.hybrid_command(name="unlock", description="Unlocks the channel (allows messages to be sent).")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Channel unlocked.")

    @commands.hybrid_command(name="lock", description="Locks the channel (prevents messages from being sent).")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel locked.")

    @commands.hybrid_command(name="slowmode", description="Configures the channel's slowmode.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def slowmode(self, ctx, seconds: int):
        if seconds < 0:
            await ctx.send("The number of seconds must be positive.")
            return
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"⏳ Slowmode enabled: {seconds} seconds.", delete_after=5)

    @commands.hybrid_command(name="clear", description="Deletes a specified number of messages from the channel.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_messages=True)
    @checks.kill_switch_required()
    async def clear(self, ctx, amount: int):
        if amount < 1:
            await ctx.send("The number of messages to delete must be ≥ 1.")
            return
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"✅ {amount} messages deleted.", delete_after=5)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
