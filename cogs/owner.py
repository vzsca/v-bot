"""
Commands reserved for owners. All authorization checks go through
checks.py (no more scattered `if ctx.author.id not in AUTHORIZED_USER_ID`).
"""

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

    @commands.command(name="servers")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def servers(self, ctx):
        view = views.ServersMenu(self.bot.guilds)
        embed = discord.Embed(
            title="🌐 Server Panel",
            description=f"Select a server to manage the bot\n\n📊 **Number of servers:** `{len(self.bot.guilds)}`",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed, view=view)

    @commands.command(name="add_temp")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def add_temp(self, ctx, user: discord.User, duration: int):
        """Grants temporary authorization (permanent owners only)."""
        state.add_temp_owner(user.id, duration)
        security_log.log_security_event(
            f"Temporary owner granted to {user} ({user.id}) for {duration}s",
            actor=f"{ctx.author} ({ctx.author.id})",
        )
        await ctx.send(f"✅ {user.mention} is now authorized for {duration} seconds.")

    @commands.command(name="owner_list")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def owner_list(self, ctx):
        """Lists permanent and temporary owners."""
        now = time.time()
        authorized_ids = list(config.PERMANENT_OWNERS)
        authorized_ids += [uid for uid, expiry in state.temp_authorized_users.items() if expiry > now]

        if not authorized_ids:
            await ctx.send("⚠️ No users are currently authorized.")
            return

        description = ""
        for uid in authorized_ids:
            if uid in config.PERMANENT_OWNERS_SET:
                description += f"👑 <@{uid}> (Permanent Owner)\n"
            else:
                remaining = int(state.temp_authorized_users.get(uid, 0) - now)
                description += f"⏳ <@{uid}> ({remaining} seconds remaining)\n"

        embed = discord.Embed(
            title="📋 Authorized Users",
            description=description,
            color=discord.Color.green(),
        )
        footer_icon = ctx.author.avatar.url if getattr(ctx.author, "avatar", None) else None
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=footer_icon)
        await ctx.send(embed=embed)

    @commands.command(name="killswitch")
    @checks.permanent_owner_check()
    async def killswitch(self, ctx, mode: str = None):
        if mode is None:
            status = "🚨 ENABLED" if state.kill_switch else "🟢 DISABLED"
            await ctx.send(f"📊 Current kill switch status: **{status}**")
            return

        normalized = mode.lower()

        if normalized in ("true", "on", "1"):
            state.kill_switch = True
            security_log.log_security_event(
                "Kill switch ENABLED",
                actor=f"{ctx.author} ({ctx.author.id})",
            )
            await ctx.send("🚨 Kill switch ENABLED: all sensitive commands are blocked.")
            return

        if normalized in ("false", "off", "0"):
            state.kill_switch = False
            security_log.log_security_event(
                "Kill switch DISABLED",
                actor=f"{ctx.author} ({ctx.author.id})",
            )
            await ctx.send("🟢 Kill switch DISABLED: bot fully operational.")
            return

        await ctx.send(
            "❌ Invalid value.\n"
            "Usage: `v!killswitch true/false | on/off | 1/0` or no argument to display the current status."
        )

    @commands.command(name="toggle_guild")
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

    @commands.command(name="say")
    @checks.owner_check()
    @checks.kill_switch_required()
    async def say(self, ctx, *, message: str):
        """Makes the bot send a message and deletes the command."""
        try:
            await ctx.send(message)
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("I do not have permission to send messages here.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="embed")
    @checks.owner_check()
    @checks.kill_switch_required()
    async def embed(self, ctx, *, content: str):
        """Sends an embed with a title and description."""
        if "|" not in content:
            await ctx.send("❌ Usage: `v!embed title | description`")
            return
    
        title, description = content.split("|", 1)
        title = title.strip()
        description = description.strip()
    
        if not title or not description:
            await ctx.send("❌ The title and description cannot be empty.")
            return
    
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue(),
        )
    
        try:
            await ctx.send(embed=embed)
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to send messages here.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))
