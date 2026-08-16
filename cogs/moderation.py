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
    await bot.add_cog(ModerationCog(bot))"""
Commandes de modération. Toutes utilisent checks.owner_or_permission(...)
pour l'autorisation : owner (permanent/temporaire) OU permission Discord
adéquate sur le serveur.

Toutes ces commandes sont des "hybrid commands" : elles fonctionnent à la
fois en commande slash (/) et en commande prefix (v!), avec une seule
définition. checks.py reste inchangé : un check ajouté via commands.check()
s'applique de la même façon, peu importe comment la commande est invoquée.
"""

from datetime import timedelta

import discord
from discord.ext import commands

import checks


class ModerationCog(commands.Cog, name="Modération"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="mute", description="Mute temporairement un membre.")
    @commands.guild_only()
    @checks.owner_or_permission(moderate_members=True)
    @checks.kill_switch_required()
    async def mute(self, ctx, member: discord.Member, minutes: int, *, reason: str = "Aucune raison spécifiée"):
        try:
            await member.timeout(timedelta(minutes=minutes), reason=reason)

            await ctx.send(
                f"🔇 {member.mention} a été mute pendant {minutes} minute(s).\n"
                f"Raison : {reason}"
            )

            try:
                await member.send(
                    f"🔇 Vous avez été mute sur **{ctx.guild.name}** pendant {minutes} minute(s).\n"
                    f"Raison : {reason}"
                )
            except discord.Forbidden:
                pass

        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de mute ce membre.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur : {e}")

    @commands.hybrid_command(name="unmute", description="Retire le mute d'un membre.")
    @commands.guild_only()
    @checks.owner_or_permission(moderate_members=True)
    @checks.kill_switch_required()
    async def unmute(self, ctx, member: discord.Member):
        try:
            await member.timeout(None)
            await ctx.send(f"🔊 {member.mention} a été unmute.")
            try:
                await member.send(f"🔊 Vous avez été unmute sur le serveur **{ctx.guild.name}**.")
            except discord.Forbidden:
                await ctx.send(f"❌ Je n'ai pas pu envoyer de message privé à {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission d'unmute ce membre.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur : {e}")

    @commands.hybrid_command(name="kick", description="Expulse un membre du serveur.")
    @commands.guild_only()
    @checks.owner_or_permission(kick_members=True)
    @checks.kill_switch_required()
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Aucune raison spécifiée"):
        try:
            await member.kick(reason=reason)
            await ctx.send(f"👢 {member.mention} a été expulsé. Raison : {reason}")
            try:
                await member.send(f"👢 Vous avez été expulsé du serveur **{ctx.guild.name}**.\nRaison: {reason}")
            except discord.Forbidden:
                await ctx.send(f"❌ Je n'ai pas pu envoyer de message privé à {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission d'expulser ce membre.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur : {e}")

    @commands.hybrid_command(name="ban", description="Bannit un membre du serveur.")
    @commands.guild_only()
    @checks.owner_or_permission(ban_members=True)
    @checks.kill_switch_required()
    async def ban(self, ctx, member: discord.Member, *, reason: str = "Aucune raison spécifiée"):
        try:
            await member.ban(reason=reason)
            await ctx.send(f"⛔ {member.mention} a été banni. Raison : {reason}")
            try:
                await member.send(f"⛔ Vous avez été banni du serveur **{ctx.guild.name}**.\nRaison: {reason}")
            except discord.Forbidden:
                await ctx.send(f"❌ Je n'ai pas pu envoyer de message privé à {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de bannir ce membre.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur : {e}")

    @commands.hybrid_command(name="unban", description="Débannit un utilisateur via son ID.")
    @commands.guild_only()
    @checks.owner_or_permission(ban_members=True)
    @checks.kill_switch_required()
    async def unban(self, ctx, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"✅ {user.mention} a été débanni.")
            try:
                await user.send(f"✅ Vous avez été débanni du serveur **{ctx.guild.name}**.")
            except discord.Forbidden:
                await ctx.send(f"❌ Je n'ai pas pu envoyer de message privé à {user.mention}.")
        except discord.NotFound:
            await ctx.send("❌ L'utilisateur n'est pas banni ou l'ID est invalide.")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de unban ce membre.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur : {e}")

    @commands.hybrid_command(name="give_role", description="Donne un rôle à un membre.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_roles=True)
    @checks.kill_switch_required()
    async def give_role(self, ctx, member: discord.Member, role: discord.Role):
        if role in member.roles:
            await ctx.send(f"⚠️ {member.mention} a déjà le rôle {role.mention}.")
            return
        try:
            await member.add_roles(role, reason=f"Ajouté par {ctx.author}")
            await ctx.send(f"✅ Rôle {role.mention} donné à {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de donner ce rôle (vérifie la hiérarchie des rôles).")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur : {e}")

    @commands.hybrid_command(name="unlock", description="Déverrouille le salon (autorise l'envoi de messages).")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Salon déverrouillé.")

    @commands.hybrid_command(name="lock", description="Verrouille le salon (bloque l'envoi de messages).")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Salon verrouillé.")

    @commands.hybrid_command(name="slowmode", description="Configure le mode lent du salon.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_channels=True)
    @checks.kill_switch_required()
    async def slowmode(self, ctx, seconds: int):
        if seconds < 0:
            await ctx.send("Le nombre de secondes doit être positif.")
            return
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"⏳ Mode lent activé : {seconds} secondes.", delete_after=5)

    @commands.hybrid_command(name="clear", description="Supprime un nombre donné de messages dans le salon.")
    @commands.guild_only()
    @checks.owner_or_permission(manage_messages=True)
    @checks.kill_switch_required()
    async def clear(self, ctx, amount: int):
        if amount < 1:
            await ctx.send("Le nombre de messages à supprimer doit être ≥ 1.")
            return
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"✅ {amount} messages supprimés.", delete_after=5)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
