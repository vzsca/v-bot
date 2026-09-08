"""Safer sensitive commands used when DANGEROUS_COMMANDS_ENABLED is enabled."""

import asyncio
import logging

import discord
from discord.ext import commands

import checks
import config
import exceptions
import security
import security_log
from state import state

logger = logging.getLogger("v-bot")


class DangerousSafeCog(commands.Cog, name="Sensitive"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _running_key(ctx: commands.Context) -> tuple[str, int]:
        return (ctx.command.qualified_name, ctx.guild.id if ctx.guild else ctx.author.id)

    async def cog_before_invoke(self, ctx: commands.Context):
        key = self._running_key(ctx)
        if key in state.running_commands:
            raise exceptions.CommandAlreadyRunning()
        state.running_commands.add(key)

    async def cog_after_invoke(self, ctx: commands.Context):
        state.running_commands.discard(self._running_key(ctx))

    @commands.command(name="spam")
    @commands.guild_only()
    @checks.owner_or_guild_owner()
    @checks.kill_switch_required()
    async def spam(self, ctx, times: int, *, payload: str):
        parts = payload.strip().split(maxsplit=1)
        confirmation = ""
        message = payload.strip()
        if parts and parts[0].lower() == "confirm":
            confirmation = "confirm"
            message = parts[1].strip() if len(parts) == 2 else ""
        if not message:
            await ctx.send("❌ Empty message. Use `v!spam <amount> <message>` or confirm with `confirm` for multiple messages.")
            return
        if not 1 <= times <= config.MAX_SPAM:
            await ctx.send(f"❌ times must be between 1 and {config.MAX_SPAM}.")
            return
        if times > 1 and confirmation != "confirm":
            await ctx.send(f"⚠️ Confirm with `v!spam {times} confirm <message>` before sending multiple messages.")
            return
        if not await security.require_action_code(ctx, "spam"):
            return
        try:
            for _ in range(times):
                await ctx.send(message[:2000])
                await asyncio.sleep(0.5)
        except (discord.Forbidden, discord.HTTPException):
            logger.exception("Spam failed in guild %s", ctx.guild.id)

    @commands.command(name="dmall")
    @commands.guild_only()
    @checks.owner_or_guild_owner()
    @checks.kill_switch_required()
    async def dmall(self, ctx, *, payload: str):
        parts = payload.strip().split(maxsplit=1)
        confirmation = parts[0].lower() == "confirm" if parts else False
        message = parts[1].strip() if confirmation and len(parts) == 2 else payload.strip()
        members = [m for m in ctx.guild.members if not m.bot]
        if len(members) > config.MAX_DMALL_MEMBERS:
            await ctx.send(f"❌ Operation blocked: {len(members)} members exceeds the limit of {config.MAX_DMALL_MEMBERS}.")
            return
        if not confirmation:
            await ctx.send(f"⚠️ {len(members)} members would receive a DM. Use `v!dmall confirm <message>` to confirm.")
            return
        if not message:
            await ctx.send("❌ Empty message.")
            return
        if not await security.require_action_code(ctx, "dmall"):
            return
        await ctx.send("📨 Confirmed and controlled delivery started…")
        sent = failed = 0
        for member in members:
            try:
                await member.send(message[:2000])
                sent += 1
                await asyncio.sleep(1.2)
            except (discord.Forbidden, discord.HTTPException):
                failed += 1
            except Exception:
                failed += 1
                logger.exception("DM error for member %s", member.id)
        await ctx.send(f"✅ Messages sent: {sent}\n❌ Failures: {failed}")

    @commands.command(name="raid")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def raid(self, ctx, amount: int = 10, confirmation: str = ""):
        if not 1 <= amount <= config.MAX_RAID_AMOUNT:
            await ctx.send(f"❌ amount must be between 1 and {config.MAX_RAID_AMOUNT}.")
            return
        if confirmation.lower() != "confirm":
            await ctx.send(f"⚠️ Confirm with `v!raid {amount} confirm` before creating test resources.")
            return
        if not await security.require_action_code(ctx, "raid"):
            return
        guild_id = ctx.guild.id
        roles = channels = 0
        try:
            for i in range(amount):
                role = await ctx.guild.create_role(name=f"raid-test-{ctx.author.id}-{i}")
                state.add_raid_role(guild_id, role.id)
                security_log.log_security_event(
                    f"Tracked sensitive resource created: role={role.id} guild={guild_id}",
                    actor=f"{ctx.author} ({ctx.author.id})",
                )
                roles += 1
            for i in range(amount):
                channel = await ctx.guild.create_text_channel(name=f"raid-test-{ctx.author.id}-{i}")
                state.add_raid_channel(guild_id, channel.id)
                security_log.log_security_event(
                    f"Tracked sensitive resource created: channel={channel.id} guild={guild_id}",
                    actor=f"{ctx.author} ({ctx.author.id})",
                )
                channels += 1
                try:
                    await channel.send("🧪 test raid system active")
                except (discord.Forbidden, discord.HTTPException):
                    pass
            await ctx.send(f"✅ RAID TEST COMPLETED\n• Roles: {roles}\n• Channels: {channels}\n🧹 `v!remove_raid` to clean up")
        except discord.Forbidden:
            await ctx.send("❌ Insufficient permissions.")
        except discord.HTTPException:
            logger.exception("Raid Discord API error")
            await ctx.send("⚠️ Discord rejected part of the operation.")

    @commands.command(name="remove_raid")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def remove_raid(self, ctx):
        if not await security.require_action_code(ctx, "remove_raid"):
            return
        guild_id = ctx.guild.id
        deleted_channels = deleted_roles = deleted_messages = 0
        for channel_id in list(state.created_raid_channels.get(guild_id, set())):
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.delete()
                    deleted_channels += 1
                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                    logger.warning("Unable to delete raid channel %s", channel_id)
            state.discard_raid_channel(guild_id, channel_id)
        for role_id in list(state.created_raid_roles.get(guild_id, set())):
            role = ctx.guild.get_role(role_id)
            if role:
                try:
                    await role.delete()
                    deleted_roles += 1
                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                    logger.warning("Unable to delete raid role %s", role_id)
            state.discard_raid_role(guild_id, role_id)
        await ctx.send(f"🧹 Cleanup completed:\n• Channels: {deleted_channels}\n• Roles: {deleted_roles}\n• Messages: {deleted_messages}")


async def setup(bot: commands.Bot):
    await bot.add_cog(DangerousSafeCog(bot))
