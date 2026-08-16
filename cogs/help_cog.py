"""v!help command, with public and owner embeds."""

import discord
from discord.ext import commands

import checks
import config


class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    @checks.kill_switch_required()
    async def help(self, ctx, category: str = None):
        is_owner = checks.is_owner_or_temp(ctx.author.id)

        general_embed = discord.Embed(
            title="📜 User Commands",
            description="List of commands available to everyone.\nAvailable as `/slash` commands or with the `v!` prefix.",
            color=discord.Color.blue(),
        )
        general_embed.add_field(name="🔇 `mute @user <minutes> [reason]`", value="Temporarily mutes a member.", inline=False)
        general_embed.add_field(name="🔊 `unmute @user`", value="Removes a member's mute.", inline=False)
        general_embed.add_field(name="🦵 `kick @user [reason]`", value="Kicks a member.", inline=False)
        general_embed.add_field(name="⛔ `ban @user [reason]`", value="Bans a member.", inline=False)
        general_embed.add_field(name="🔄 `unban <id>`", value="Unbans a user.", inline=False)
        general_embed.add_field(name="🎭 `give_role @user @role`", value="Gives a role to a member.", inline=False)
        general_embed.add_field(name="🗑️ `clear <amount>`", value="Deletes messages.", inline=False)
        general_embed.add_field(name="⏳ `slowmode <seconds>`", value="Configures slowmode.", inline=False)
        general_embed.add_field(name="🔒 `lock`", value="Locks the channel.", inline=False)
        general_embed.add_field(name="🔓 `unlock`", value="Unlocks the channel.", inline=False)
        general_embed.add_field(name="🖼️ `avatar <@user>`", value="Displays a user's avatar.", inline=False)
        general_embed.add_field(name="👤 `user_info`", value="Displays user information.", inline=False)
        general_embed.add_field(name="🏠 `server_info`", value="Displays server information.", inline=False)
        general_embed.add_field(name="💬 `snipe [index]`", value="Displays a deleted message.", inline=False)

        owner_embed = discord.Embed(
            title="👑 Owner Commands",
            description="Commands restricted to owners/authorized users.",
            color=discord.Color.gold(),
        )
        owner_embed.add_field(name="📌 `add_temp @user duration`", value="Grants temporary authorization.", inline=False)
        owner_embed.add_field(name="📄 `owner_list`", value="Lists the bot owners.", inline=False)
        owner_embed.add_field(name="⚙️ `servers`", value="Server panel (selection + actions).", inline=False)
        owner_embed.add_field(
            name="📩 « Invite » button (in `v!servers`)",
            value="Generates a temporary invite for the selected server.",
            inline=False,
        )
        owner_embed.add_field(name="🔁 `toggle_guild`", value="Enables/disables the bot on the current server.", inline=False)
        owner_embed.add_field(name="💬 `say <message>`", value="Makes the bot send a message.", inline=False)

        if config.DANGEROUS_COMMANDS_ENABLED:
            owner_embed.add_field(name="💣 `spam <amount> <message>`", value="Controlled message spam.", inline=False)
            owner_embed.add_field(name="📨 `dmall <message>`", value="DMs all members.", inline=False)
            owner_embed.add_field(name="⚔️ `raid <amount>`", value="Mass test creation.", inline=False)
            owner_embed.add_field(name="🔙 `remove_raid`", value="Cleans up raid elements.", inline=False)
            sensitive_status = "🟢 **ENABLED**"
        else:
            sensitive_status = "🔴 **DISABLED**"

        owner_embed.add_field(
            name="Sensitive commands (raid / remove_raid / dmall / spam)",
            value=(
                f"Status: {sensitive_status}\n"
                "Toggled through the `start_bot.bat` panel (`toggle_dangerous` command), "
                "not through a Discord command — requires a bot restart."
            ),
            inline=False,
        )
        owner_embed.add_field(
            name="🚨 `killswitch [true/false | on/off | 1/0]`",
            value=(
                "Enables or disables the bot's global security mode.\n\n"
                "✔ `v!killswitch true / on / 1` → enables command blocking\n"
                "✔ `v!killswitch false / off / 0` → disables command blocking\n"
                "✔ `v!killswitch` → displays the current status\n\n"
                "🔐 Restricted to **permanent owners only**"
            ),
            inline=False,
        )

        if category == "owner":
            if is_owner:
                await ctx.send(embed=owner_embed)
            else:
                await ctx.send("❌ You do not have permission to access Owner commands.")
        elif category == "all":
            if is_owner:
                await ctx.send(embed=general_embed)
                await ctx.send(embed=owner_embed)
            else:
                await ctx.send("❌ You do not have permission to display all commands.")
        else:
            await ctx.send(embed=general_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))"""Commande v!help, avec embed public et embed owner."""

import discord
from discord.ext import commands

import checks
import config


class HelpCog(commands.Cog, name="Aide"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    @checks.kill_switch_required()
    async def help(self, ctx, category: str = None):
        is_owner = checks.is_owner_or_temp(ctx.author.id)

        general_embed = discord.Embed(
            title="📜 Commandes Utilisateur",
            description="Liste des commandes accessibles à tous.\nDisponibles en `/slash` ou en préfixe `v!`.",
            color=discord.Color.blue(),
        )
        general_embed.add_field(name="🔇 `mute @user <minutes> [raison]`", value="Mute temporairement un membre.", inline=False)
        general_embed.add_field(name="🔊 `unmute @user`", value="Retire le mute d'un membre.", inline=False)
        general_embed.add_field(name="🦵 `kick @user [raison]`", value="Expulse un membre.", inline=False)
        general_embed.add_field(name="⛔ `ban @user [raison]`", value="Bannit un membre.", inline=False)
        general_embed.add_field(name="🔄 `unban <id>`", value="Débannit un utilisateur.", inline=False)
        general_embed.add_field(name="🎭 `give_role @user @role`", value="Donne un rôle à un membre.", inline=False)
        general_embed.add_field(name="🗑️ `clear <nombre>`", value="Supprime des messages.", inline=False)
        general_embed.add_field(name="⏳ `slowmode <secondes>`", value="Configure le mode lent.", inline=False)
        general_embed.add_field(name="🔒 `lock`", value="Verrouille le salon.", inline=False)
        general_embed.add_field(name="🔓 `unlock`", value="Déverrouille le salon.", inline=False)
        general_embed.add_field(name="🖼️ `avatar <@user>`", value="Affiche l'avatar.", inline=False)
        general_embed.add_field(name="👤 `user_info`", value="Informations utilisateur.", inline=False)
        general_embed.add_field(name="🏠 `server_info`", value="Informations serveur.", inline=False)
        general_embed.add_field(name="💬 `snipe [index]`", value="Affiche un message supprimé.", inline=False)

        owner_embed = discord.Embed(
            title="👑 Commandes Owner",
            description="Commandes réservées aux propriétaires/autorités.",
            color=discord.Color.gold(),
        )
        owner_embed.add_field(name="📌 `add_temp @user durée`", value="Autorisation temporaire.", inline=False)
        owner_embed.add_field(name="📄 `owner_list`", value="Liste des owners.", inline=False)
        owner_embed.add_field(name="⚙️ `servers`", value="Panel serveurs (sélection + actions).", inline=False)
        owner_embed.add_field(
            name="📩 Bouton « Invite » (dans `v!servers`)",
            value="Génère une invitation temporaire pour le serveur sélectionné.",
            inline=False,
        )
        owner_embed.add_field(name="🔁 `toggle_guild`", value="Active/désactive le bot sur le serveur actuel.", inline=False)
        owner_embed.add_field(name="💬 `say <message>`", value="Faire parler le bot.", inline=False)

        if config.DANGEROUS_COMMANDS_ENABLED:
            owner_embed.add_field(name="💣 `spam <nb> <message>`", value="Spam contrôlé.", inline=False)
            owner_embed.add_field(name="📨 `dmall <message>`", value="DM tous les membres.", inline=False)
            owner_embed.add_field(name="⚔️ `raid <nb>`", value="Création massive test.", inline=False)
            owner_embed.add_field(name="🔙 `remove_raid`", value="Nettoyage raid.", inline=False)
            sensitive_status = "🟢 **ACTIVÉES**"
        else:
            sensitive_status = "🔴 **DÉSACTIVÉES**"

        owner_embed.add_field(
            name="Commandes sensibles (raid / remove_raid / dmall / spam)",
            value=(
                f"Statut : {sensitive_status}\n"
                "Bascule via le panel `start_bot.bat` (commande `toggle_dangerous`), "
                "pas une commande Discord — nécessite un redémarrage du bot."
            ),
            inline=False,
        )
        owner_embed.add_field(
            name="🚨 `killswitch [true/false | on/off | 1/0]`",
            value=(
                "Active ou désactive le mode sécurité global du bot.\n\n"
                "✔ `v!killswitch true / on / 1` → active le blocage des commandes sensibles\n"
                "✔ `v!killswitch false / off / 0` → désactive le blocage\n"
                "✔ `v!killswitch` → affiche l'état actuel\n\n"
                "🔐 Réservé aux **owners permanents uniquement**"
            ),
            inline=False,
        )

        if category == "owner":
            if is_owner:
                await ctx.send(embed=owner_embed)
            else:
                await ctx.send("❌ Vous n'avez pas la permission d'accéder aux commandes Owner.")
        elif category == "all":
            if is_owner:
                await ctx.send(embed=general_embed)
                await ctx.send(embed=owner_embed)
            else:
                await ctx.send("❌ Vous n'avez pas la permission d'afficher toutes les commandes.")
        else:
            await ctx.send(embed=general_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
