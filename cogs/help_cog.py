"""Discord help command."""

import discord
from discord.ext import commands

import checks
import config


class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    @checks.kill_switch_required()
    async def help(self, ctx, category: str | None = None):
        is_owner = checks.is_owner_or_temp(ctx.author.id, ctx.guild.id if ctx.guild else None)

        general = discord.Embed(
            title="📜  V-BOT • User Commands",
            description=(
                "Commands available to everyone.\n"
                "Use `/slash` commands or the `v!` prefix."
            ),
            color=discord.Color.blue(),
        )
        general.set_footer(text="v-bot • Help • Public commands")

        for name, description in (
            ("🔇 `mute @user <minutes> [reason]`", "Temporarily mute a member."),
            ("🔊 `unmute @user`", "Remove a mute."),
            ("🦵 `kick @user [reason]`", "Kick a member."),
            ("⛔ `ban @user [reason]`", "Ban a member."),
            ("🔄 `unban <id>`", "Unban a user."),
            ("🎭 `give_role @user @role`", "Give a role to a member."),
            ("🗑️ `clear <amount>`", "Delete messages."),
            ("⏳ `slowmode <seconds>`", "Configure slowmode."),
            ("🔒 `lock` / `unlock`", "Lock or unlock the channel."),
            ("🖼️ `avatar [@user]`", "Display a user's avatar."),
            ("👤 `user_info [@user]`", "Display user information."),
            ("🏠 `server_info`", "Display server information."),
            ("💬 `snipe [index]`", "Display a deleted message."),
        ):
            general.add_field(name=name, value=description, inline=False)

        api = discord.Embed(
            title="📡  API & Announcements",
            description="Server-specific configuration and automatic notifications.",
            color=discord.Color.blurple(),
        )
        api.add_field(name="🔑 `set_api twitch|yt`", value="Configure this server's own API credentials.", inline=False)
        api.add_field(name="📊 `api_status`", value="Show API mode/status without exposing secrets.", inline=False)
        api.add_field(name="🧹 `clear_api twitch|yt`", value="Remove this server's API credentials.", inline=False)
        api.add_field(name="📺 `create_annonce`", value="Create an automatic Twitch/YouTube announcement.", inline=False)
        api.add_field(name="📋 `annonces`", value="List configured announcements.", inline=False)
        api.add_field(name="🧪 `test_annonce <id>`", value="Test an announcement.", inline=False)
        api.add_field(name="🗑️ `delete_annonce <id>`", value="Delete an announcement.", inline=False)
        api.set_footer(text="API credentials are isolated per server.")

        owner = discord.Embed(
            title="👑  V-BOT • Owner Commands",
            description=(
                "Restricted administration commands.\n"
                "🔐 Owner access is required for this section."
            ),
            color=discord.Color.gold(),
        )
        for name, description in (
            ("📝 `embed <title> | <description>`", "Send a custom embed."),
            ("📌 `add_temp @user <duration>`", "Grant temporary authorization."),
            ("📄 `owner_list`", "List bot owners."),
            ("⚙️ `servers`", "Open server management."),
            ("🔁 `toggle_guild`", "Enable or disable the bot on the current server."),
            ("💬 `say <message>`", "Make the bot send a message."),
        ):
            owner.add_field(name=name, value=description, inline=False)

        sensitive = "🟢 **ENABLED**" if config.DANGEROUS_COMMANDS_ENABLED else "🔴 **DISABLED**"
        owner.add_field(
            name="🧨 Sensitive commands",
            value=(
                "`spam`, `dmall`, `raid`, `remove_raid`\n"
                f"Status: {sensitive}\n"
                "⚙️ Managed from the `start_bot.bat` panel → `toggle_dangerous`.\n"
                "🔄 Bot restart required after changing the setting."
            ),
            inline=False,
        )
        owner.add_field(
            name="🚨 `killswitch [true/false | on/off | 1/0]`",
            value=(
                "Global emergency security mode.\n"
                "✅ `true / on / 1` → block commands\n"
                "✅ `false / off / 0` → unblock commands\n"
                "ℹ️ No argument → display current status\n"
                "🔐 **Restricted to permanent owners only.**"
            ),
            inline=False,
        )
        owner.set_footer(text="v-bot • Owner controls • Keep sensitive commands disabled unless needed")

        if category == "owner":
            await ctx.send(embed=owner if is_owner else discord.Embed(
                title="🔒 Owner Commands",
                description="❌ You do not have permission to access Owner commands.",
                color=discord.Color.red(),
            ))
        elif category == "all":
            if is_owner:
                await ctx.send(embeds=[general, api, owner])
            else:
                await ctx.send(embed=discord.Embed(
                    title="🔒 Restricted",
                    description="❌ You do not have permission to display all commands.",
                    color=discord.Color.red(),
                ))
        else:
            await ctx.send(embeds=[general, api])


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
