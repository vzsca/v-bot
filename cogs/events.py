"""
Événements globaux du bot + tâche de fond.
"""

import logging
import os

import discord
from discord.ext import commands, tasks

import checks
import config
import exceptions
from state import state

logger = logging.getLogger("v-bot")

# Fichier listant les serveurs connectés, à la racine du projet (lu par la
# commande "servers" du panel start_bot.bat). On ne logue plus cette liste
# dans bot.log/la console pour ne pas la polluer à chaque démarrage.
SERVERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "servers.txt")


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._intents_text: str | None = None  # calculé une seule fois (les intents ne changent pas)
        self.clean_expired_users.start()

    def cog_unload(self):
        self.clean_expired_users.cancel()

    # --- Tâche de fond ---
    @tasks.loop(seconds=config.TEMP_AUTH_CLEAN_INTERVAL)
    async def clean_expired_users(self):
        for uid in state.clean_expired():
            logger.info(f"🔴 Utilisateur {uid} retiré des autorisés temporaires.")

    def _write_servers_file(self):
        """Écrit la liste des serveurs connectés dans servers.txt (lu par le panel .bat)."""
        try:
            lines = [f"{g.name} (id: {g.id})" for g in self.bot.guilds]
            with open(SERVERS_FILE, "w", encoding="utf-8") as f:
                f.write(f"{len(lines)} serveur(s) connecté(s) :\n\n")
                f.write("\n".join(lines))
                f.write("\n")
        except OSError as e:
            logger.warning(f"Impossible d'écrire {SERVERS_FILE} : {e}")

    # --- Événements ---
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Connecté en tant que {self.bot.user} (ID: {self.bot.user.id})")
        if self.bot.user.name != config.BOT_NAME:
            try:
                await self.bot.user.edit(username=config.BOT_NAME)
                logger.info(f"Nom du bot modifié : {config.BOT_NAME}")
            except Exception as e:
                logger.warning(f"Impossible de modifier le nom du bot : {e}")
        try:
            synced = await self.bot.tree.sync()
            logger.info(f"Commandes synchronisées : {len(synced)}")
        except Exception as e:
            logger.warning(f"Erreur de synchronisation des commandes : {e}")

        try:
            await self.bot.change_presence(
                activity=discord.CustomActivity(name=f"Version {config.VERSION}")
            )
        except Exception as e:
            logger.warning(f"Impossible de définir le statut Discord : {e}")

        logger.info(f"Le bot est connecté à {len(self.bot.guilds)} serveurs.")
        self._write_servers_file()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self._write_servers_file()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self._write_servers_file()

    def _build_intents_text(self) -> str:
        # Les intents sont fixés au démarrage : on construit la chaîne une seule fois
        # au lieu de la reconstruire à chaque mention du bot.
        if self._intents_text is None:
            intents = self.bot.intents
            self._intents_text = "\n".join([
                f"• intents.guilds: **{intents.guilds}**",
                f"• intents.members: **{intents.members}**",
                f"• intents.message_content: **{intents.message_content}**",
                f"• intents.messages: **{intents.messages}**",
                f"• intents.reactions: **{intents.reactions}**",
            ])
        return self._intents_text

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        mention = f"<@{self.bot.user.id}>"
        mention_nick = f"<@!{self.bot.user.id}>"

        if not (message.content.startswith(mention) or message.content.startswith(mention_nick)):
            return

        # Owners (permanents/temporaires) -> embed détaillé (intents, kill switch, admin...).
        # Tout le monde d'autre -> message générique, pour ne pas exposer ces
        # informations opérationnelles à n'importe qui qui mentionne le bot.
        if checks.is_owner_or_temp(message.author.id):
            await message.channel.send(embed=self._build_owner_embed(message))
        else:
            await message.channel.send(embed=self._build_general_embed())

    def _build_owner_embed(self, message: discord.Message) -> discord.Embed:
        perms = message.guild.me.guild_permissions if message.guild else None
        has_admin = perms.administrator if perms else False
        kill_status = "🚨 ACTIVÉ" if state.kill_switch else "Désactivé"
        color = discord.Color.red() if state.kill_switch else discord.Color.blue()

        embed = discord.Embed(title=f"{self.bot.user.name} est opérationnel !", color=color)

        embed.add_field(
            name="Statut système",
            value=(
                f"• Administrateur : **{has_admin}**\n"
                f"• Kill Switch : **{kill_status}**\n"
                f"• Prefix : `{config.PREFIXES[0]}`"
            ),
            inline=False,
        )

        embed.add_field(
            name="Sécurité & accès",
            value="   ⚠️ certaines commandes peuvent être restreintes pour des raisons de sécurité.",
            inline=False,
        )

        embed.add_field(name="Intents activés", value=self._build_intents_text(), inline=False)

        embed.set_footer(
            text=f"Requête envoyée par {message.author}",
            icon_url=message.author.avatar.url if getattr(message.author, "avatar", None) else None,
        )
        return embed

    def _build_general_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"👋 Salut, je suis {self.bot.user.name} !",
            description=f"Utilise `{config.PREFIXES[0]}help` pour voir ce que je sais faire.",
            color=discord.Color.blue(),
        )
        return embed

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message or message.author.bot:
            return
        if not message.content and not message.attachments:
            return

        data = {
            "type": "delete",
            "content": message.content or "[contenu vide]",
            "author": str(message.author),
            "author_avatar": message.author.display_avatar.url,
            "time": message.created_at,
            "attachments": [a.url for a in message.attachments] if message.attachments else [],
        }
        state.add_sniped(message.channel.id, data, config.SNIPE_LIMIT)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Désolé, cette commande n'existe pas. Utilisez `v!help` pour voir la liste des commandes disponibles.")
        elif isinstance(error, commands.NoPrivateMessage):
            # Message par défaut de discord.py en anglais -> on le remplace
            # par un message en français, cohérent avec le reste du bot.
            await ctx.send("❌ Cette commande ne peut pas être utilisée en message privé.")
        elif isinstance(error, (exceptions.NotPermanentOwner, exceptions.NotOwnerOrTemp, exceptions.NotOwnerOrGuildOwner)):
            # Refus de permission : digne d'être tracé (qui a tenté quoi),
            # contrairement aux blocages routiniers (kill switch, déjà en
            # cours) qui sont juste le comportement normal du bot.
            logger.warning(f"Permission refusée pour '{ctx.command}' à {ctx.author} ({ctx.author.id}).")
            await ctx.send(str(error))
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))
        else:
            logger.exception("Erreur de commande :", exc_info=error)
            await ctx.send(f"Une erreur est survenue : `{error}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
