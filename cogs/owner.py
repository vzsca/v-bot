"""
Commandes réservées aux owners. Toute vérification d'autorisation passe par
checks.py (plus de `if ctx.author.id not in AUTHORIZED_USER_ID` dispersés).
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
            title="🌐 Panel Serveurs",
            description=f"Sélectionne un serveur pour gérer le bot\n\n📊 **Nombre de serveurs :** `{len(self.bot.guilds)}`",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed, view=view)

    @commands.command(name="add_temp")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def add_temp(self, ctx, user: discord.User, duration: int):
        """Donne une autorisation temporaire (seulement owner permanent)."""
        state.add_temp_owner(user.id, duration)
        security_log.log_security_event(
            f"Owner temporaire accordé à {user} ({user.id}) pour {duration}s",
            actor=f"{ctx.author} ({ctx.author.id})",
        )
        await ctx.send(f"✅ {user.mention} est maintenant autorisé pendant {duration} secondes.")

    @commands.command(name="owner_list")
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def owner_list(self, ctx):
        """Liste les propriétaires permanents + temporaires."""
        now = time.time()
        authorized_ids = list(config.PERMANENT_OWNERS)
        authorized_ids += [uid for uid, expiry in state.temp_authorized_users.items() if expiry > now]

        if not authorized_ids:
            await ctx.send("⚠️ Aucun utilisateur n'est actuellement autorisé.")
            return

        description = ""
        for uid in authorized_ids:
            if uid in config.PERMANENT_OWNERS_SET:
                description += f"👑 <@{uid}> (Owner permanent)\n"
            else:
                remaining = int(state.temp_authorized_users.get(uid, 0) - now)
                description += f"⏳ <@{uid}> (reste {remaining} secondes)\n"

        embed = discord.Embed(
            title="📋 Liste des utilisateurs autorisés",
            description=description,
            color=discord.Color.green(),
        )
        footer_icon = ctx.author.avatar.url if getattr(ctx.author, "avatar", None) else None
        embed.set_footer(text=f"Demandé par {ctx.author}", icon_url=footer_icon)
        await ctx.send(embed=embed)

    @commands.command(name="killswitch")
    @checks.permanent_owner_check()
    async def killswitch(self, ctx, mode: str = None):
        if mode is None:
            status = "🚨 ACTIVÉ" if state.kill_switch else "🟢 DÉSACTIVÉ"
            await ctx.send(f"📊 Kill switch actuel : **{status}**")
            return

        normalized = mode.lower()

        if normalized in ("true", "on", "1"):
            state.kill_switch = True
            security_log.log_security_event("Kill switch ACTIVÉ", actor=f"{ctx.author} ({ctx.author.id})")
            await ctx.send("🚨 Kill switch ACTIVÉ : toutes les commandes sensibles sont bloquées.")
            return

        if normalized in ("false", "off", "0"):
            state.kill_switch = False
            security_log.log_security_event("Kill switch DÉSACTIVÉ", actor=f"{ctx.author} ({ctx.author.id})")
            await ctx.send("🟢 Kill switch DÉSACTIVÉ : bot entièrement fonctionnel.")
            return

        await ctx.send(
            "❌ Valeur invalide.\n"
            "Utilisation : `v!killswitch true/false | on/off | 1/0` ou sans argument pour l’état."
        )

    @commands.command(name="toggle_guild")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def toggle_guild(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in state.disabled_guilds:
            state.disabled_guilds.discard(guild_id)
            await ctx.send("🟢 Bot réactivé sur ce serveur.")
        else:
            state.disabled_guilds.add(guild_id)
            await ctx.send("🔴 Bot désactivé sur ce serveur.")

    @commands.command(name="say")
    @checks.owner_check()
    @checks.kill_switch_required()
    async def say(self, ctx, *, message: str):
        """Fait dire un message par le bot et supprime la commande."""
        try:
            await ctx.send(message)
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("Je n'ai pas la permission d'envoyer des messages ici.")
        except Exception as e:
            await ctx.send(f"Une erreur s'est produite : {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))
