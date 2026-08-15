"""
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
