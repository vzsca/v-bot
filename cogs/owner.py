"""Commands reserved for bot owners."""

import logging
import time

import discord
from discord.ext import commands

import checks
import config
import security_log
import views
from state import state

logger = logging.getLogger("v-bot")


class OwnerCog(commands.Cog, name="Owner"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="servers", description="Open the owner server management panel.")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def servers(self, ctx):
        view = views.ServersMenu(self.bot.guilds, ctx.author.id)
        embed = discord.Embed(title="🌐 Server Panel", description=f"Select a server to manage the bot\n\n📊 **Number of servers:** `{len(self.bot.guilds)}`", color=discord.Color.gold())
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="add_temp", description="Authorize a user temporarily on this server.")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def add_temp(self, ctx, user: discord.User, duration: int):
        if duration < 1 or duration > 7 * 24 * 60 * 60:
            await ctx.send("❌ Duration must be between 1 second and 7 days.")
            return
        try:
            state.add_temp_owner(ctx.guild.id, user.id, duration)
        except ValueError:
            await ctx.send("❌ Invalid temporary owner duration.")
            return
        security_log.log_security_event(f"Temporary owner granted to {user} ({user.id}) in guild {ctx.guild.id} for {duration}s", actor=f"{ctx.author} ({ctx.author.id})")
        await ctx.send(f"✅ {user.mention} is now authorized on **this server** for {duration} seconds.")

    @commands.hybrid_command(name="owner_list", description="Show authorized owners for this server.")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def owner_list(self, ctx):
        state.clean_expired()
        now = time.time()
        entries = []
        for (guild_id, uid), expiry in state.temp_authorized_users.items():
            if guild_id == ctx.guild.id and expiry > now:
                entries.append((uid, expiry))
        description = "\n".join(f"👑 <@{uid}> (Permanent Owner)" for uid in config.PERMANENT_OWNERS)
        if entries:
            description += "\n" + "\n".join(f"⏳ <@{uid}> ({max(0, int(expiry-now))} seconds remaining)" for uid, expiry in entries)
        embed = discord.Embed(title="📋 Authorized Users", description=description or "⚠️ No users are currently authorized.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="killswitch", description="Enable, disable, or inspect the bot kill switch.")
    @checks.permanent_owner_check()
    async def killswitch(self, ctx, mode: str | None = None):
        if mode is None:
            status = "🚨 ENABLED" if state.kill_switch else "🟢 DISABLED"
            await ctx.send(f"📊 Current kill switch status: **{status}**")
            return
        normalized = mode.lower()
        if normalized in ("true", "on", "1"):
            state.kill_switch = True
            security_log.log_security_event("Kill switch ENABLED", actor=f"{ctx.author} ({ctx.author.id})")
            await ctx.send("🚨 Kill switch ENABLED: all sensitive commands are blocked.")
            return
        if normalized in ("false", "off", "0"):
            state.kill_switch = False
            security_log.log_security_event("Kill switch DISABLED", actor=f"{ctx.author} ({ctx.author.id})")
            await ctx.send("🟢 Kill switch DISABLED: bot fully operational.")
            return
        await ctx.send("❌ Invalid value. Usage: `/killswitch true/false` or `v!killswitch true/false`.")

    @commands.hybrid_command(name="toggle_guild", description="Enable or disable the bot on this server.")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def toggle_guild(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in state.disabled_guilds:
            state.disabled_guilds.discard(guild_id)
            await ctx.send("🟢 Bot re-enabled on this server.")
        else:
            state.disabled_guilds.add(guild_id)
            await ctx.send("🔴 Bot disabled on this server.")

    @commands.hybrid_command(name="say", description="Send a message as the bot.")
    @checks.owner_check()
    @checks.kill_switch_required()
    async def say(self, ctx, *, message: str):
        try:
            await ctx.send(message)
            if ctx.message:
                await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to send or delete messages here.")
        except discord.HTTPException:
            logger.exception("Owner say command failed.")
            await ctx.send("❌ Unable to complete the command.")

    @commands.hybrid_command(name="embed", description="Send an embed from a title and description.")
    @checks.owner_check()
    @checks.kill_switch_required()
    async def embed(self, ctx, *, content: str):
        if "|" not in content:
            await ctx.send("❌ Usage: `v!embed title | description`")
            return
        title, description = content.split("|", 1)
        title, description = title.strip(), description.strip()
        if not title or not description:
            await ctx.send("❌ The title and description cannot be empty.")
            return
        embed = discord.Embed(title=title[:256], description=description[:4096], color=discord.Color.blue())
        try:
            await ctx.send(embed=embed)
            if ctx.message:
                await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to send or delete messages here.")
        except discord.HTTPException:
            logger.exception("Owner embed command failed.")
            await ctx.send("❌ Unable to complete the command.")


async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))
