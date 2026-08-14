"""
Commandes sensibles : raid, remove_raid, dmall, spam.

Ce cog n'est volontairement PAS toujours chargé. main.py ne l'ajoute au bot
que si config.DANGEROUS_COMMANDS_ENABLED est vrai (lu depuis .env). Quand
c'est désactivé (par défaut), ces commandes n'existent tout simplement pas
dans l'arbre de commandes du bot — pas juste bloquées par un check, vraiment
absentes, impossibles à invoquer ou découvrir.

La bascule active/désactive se fait depuis le panel start_bot.bat (commande
toggle_dangerous), pas via une commande Discord, et nécessite un (re)démarrage
du bot pour prendre effet puisque le choix des cogs à charger se fait une
seule fois, au démarrage de main.py.
"""

import asyncio
import logging

import discord
from discord.ext import commands

import checks
import config
import exceptions
from state import state

logger = logging.getLogger("v-bot")


class DangerousCog(commands.Cog, name="Sensible"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _running_key(ctx: commands.Context) -> tuple[str, int]:
        # Une clé par (commande, serveur) -- ou par utilisateur si la commande
        # est lancée hors serveur (ne devrait pas arriver pour ces commandes,
        # mais on reste robuste plutôt que de planter).
        scope_id = ctx.guild.id if ctx.guild else ctx.author.id
        return (ctx.command.qualified_name, scope_id)

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """
        Protection anti-double-exécution : refuse de lancer une deuxième
        instance de la même commande sur le même serveur tant que la
        précédente n'est pas terminée (évite les doublons de salons/rôles,
        les DM envoyés deux fois, etc. si quelqu'un retape la commande trop
        vite ou que deux owners la lancent en même temps).
        """
        key = self._running_key(ctx)
        if key in state.running_commands:
            raise exceptions.CommandAlreadyRunning()
        state.running_commands.add(key)

    async def cog_after_invoke(self, ctx: commands.Context) -> None:
        # Appelé même si la commande a levé une exception (cf. discord.py,
        # hooked_wrapped_callback enveloppe l'appel dans un try/finally) --
        # donc le verrou est toujours relâché, succès ou échec.
        state.running_commands.discard(self._running_key(ctx))

    @commands.command(name="spam")
    @checks.owner_or_guild_owner()
    @checks.kill_switch_required()
    async def spam(self, ctx, times: int, *, message: str):
        """Envoi contrôlé de messages -- limité et protégé."""
        if times < 1 or times > config.MAX_SPAM:
            await ctx.send(f"Nombre invalide : times doit être entre 1 et {config.MAX_SPAM}.")
            return
        try:
            for _ in range(times):
                await ctx.send(message)
                await asyncio.sleep(0.5)
        except Exception as e:
            await ctx.send(f"Une erreur s'est produite : {e}")

    @commands.command(name="dmall")
    @commands.guild_only()
    @checks.owner_or_guild_owner()
    @checks.kill_switch_required()
    async def dmall(self, ctx, *, message: str):
        """DM tous les membres (danger : spam potentiel). Protections : pause et vérifs."""
        await ctx.send("📨 Envoi des messages en cours (opération contrôlée).")

        sent = 0
        failed = 0
        for member in ctx.guild.members:
            if member.bot:
                continue
            try:
                await member.send(message)
                sent += 1
                await asyncio.sleep(1.2)
            except discord.Forbidden:
                failed += 1
            except Exception as e:
                failed += 1
                logger.warning(f"Erreur DM {member.id}: {e}")

        await ctx.send(f"✅ Messages envoyés : {sent}\n❌ Échecs : {failed}")

    @commands.command(name="raid")
    @commands.guild_only()
    @checks.permanent_owner_check()
    @checks.kill_switch_required()
    async def raid(self, ctx, amount: int = 10):
        """
        Commande de test contrôlée :
        crée des rôles + salons et les enregistre pour remove_raid.
        """
        amount = max(1, min(amount, config.MAX_RAID_AMOUNT))
        created_roles = 0
        created_channels = 0

        try:
            for i in range(amount):
                role = await ctx.guild.create_role(name=f"raid-test-{ctx.author.id}-{i}")
                state.created_raid_roles.add(role.id)
                created_roles += 1

            for i in range(amount):
                channel = await ctx.guild.create_text_channel(name=f"raid-test-{ctx.author.id}-{i}")
                state.created_raid_channels.add(channel.id)
                created_channels += 1

                try:
                    await channel.send("🧪 test raid system actif")
                except Exception:
                    pass

            await ctx.send(
                f"✅ RAID TEST TERMINÉ\n"
                f"• Rôles créés : {created_roles}\n"
                f"• Salons créés : {created_channels}\n"
                f"🧹 Utilise `v!remove_raid` pour nettoyer"
            )

        except discord.Forbidden:
            await ctx.send("❌ Permissions insuffisantes.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur : {e}")

    @commands.command(name="remove_raid")
    @commands.guild_only()
    @checks.owner_check()
    @checks.kill_switch_required()
    async def remove_raid(self, ctx):
        """Nettoyage rapide et sécurisé des éléments créés par raid."""
        deleted_channels = 0
        deleted_roles = 0
        deleted_messages = 0

        for ch_id in list(state.created_raid_channels):
            channel = ctx.guild.get_channel(ch_id)
            if channel:
                try:
                    await channel.delete()
                    deleted_channels += 1
                except Exception:
                    pass
            state.created_raid_channels.discard(ch_id)

        for role_id in list(state.created_raid_roles):
            role = ctx.guild.get_role(role_id)
            if role:
                try:
                    await role.delete()
                    deleted_roles += 1
                except Exception:
                    pass
            state.created_raid_roles.discard(role_id)

        for channel in ctx.guild.text_channels[:10]:
            try:
                async for message in channel.history(limit=50):
                    if message.author == self.bot.user and message.content and "@everyone" in message.content:
                        try:
                            await message.delete()
                            deleted_messages += 1
                        except Exception:
                            pass
            except Exception:
                continue

        await ctx.send(
            f"🧹 Nettoyage terminé :\n"
            f"• Salons supprimés : {deleted_channels}\n"
            f"• Rôles supprimés : {deleted_roles}\n"
            f"• Messages supprimés : {deleted_messages}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(DangerousCog(bot))
