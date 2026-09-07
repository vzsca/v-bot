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
        general = discord.Embed(title="📜 User Commands", description="Available with the `v!` prefix.", color=discord.Color.blue())
        for name, description in (
            ("mute @user <minutes> [reason]", "Temporarily mute a member."),
            ("unmute @user", "Remove a mute."),
            ("kick @user [reason]", "Kick a member."),
            ("ban @user [reason]", "Ban a member."),
            ("unban <id>", "Unban a user."),
            ("give_role @user @role", "Give a role."),
            ("clear <amount>", "Delete messages."),
            ("slowmode <seconds>", "Configure slowmode."),
            ("lock / unlock", "Lock or unlock the channel."),
            ("avatar [@user]", "Display an avatar."),
            ("user_info [@user]", "Display user information."),
            ("server_info", "Display server information."),
            ("snipe [index]", "Display a deleted message."),
            ("set_api twitch|yt", "Configure this server's own API credentials."),
            ("api_status", "Show API mode/status without exposing secrets."),
            ("clear_api twitch|yt", "Remove this server's API credentials."),
            ("create_annonce", "Create an automatic Twitch/YouTube announcement."),
            ("annonces", "List configured announcements."),
            ("test_annonce <id>", "Test an announcement."),
            ("delete_annonce <id>", "Delete an announcement."),
        ):
            general.add_field(name=f"`{name}`", value=description, inline=False)

        owner = discord.Embed(title="👑 Owner Commands", description="Restricted administration commands.", color=discord.Color.gold())
        for name, description in (
            ("embed <title> | <description>", "Send a custom embed."),
            ("add_temp @user <duration>", "Grant temporary authorization."),
            ("owner_list", "List bot owners."),
            ("servers", "Open server management."),
            ("toggle_guild", "Enable/disable the bot on the current server."),
            ("say <message>", "Make the bot send a message."),
            ("killswitch [on/off]", "Toggle the global security mode."),
        ):
            owner.add_field(name=f"`{name}`", value=description, inline=False)
        sensitive = "🟢 ENABLED" if config.DANGEROUS_COMMANDS_ENABLED else "🔴 DISABLED"
        owner.add_field(name="Sensitive commands", value=f"`spam`, `dmall`, `raid`, `remove_raid` — {sensitive}", inline=False)

        if category == "owner":
            await ctx.send(embed=owner if is_owner else discord.Embed(description="❌ Owner commands are restricted."))
        elif category == "all":
            if is_owner:
                await ctx.send(embeds=[general, owner])
            else:
                await ctx.send("❌ Owner commands are restricted.")
        else:
            await ctx.send(embed=general)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
