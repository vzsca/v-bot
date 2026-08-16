"""
All bot permission logic, centralized here.

A single source of truth for each type of check:

- is_permanent_owner / is_owner_or_temp: reusable low-level functions
  used everywhere (commands AND views/buttons).
- owner_check / permanent_owner_check / owner_or_permission / owner_or_guild_owner:
  ready-to-use decorators for commands.
- kill_switch_required: blocks a command if the Kill Switch is active.
- global_check: global check applied to all bot commands.

All functions below raise typed exceptions (exceptions.py) instead of generic
commands.CheckFailure exceptions with hardcoded messages -- see exceptions.py
for details on why.
"""

from discord.ext import commands

import config
import exceptions
from state import state


def is_permanent_owner(user_id: int) -> bool:
    """Returns True if the user is the principal owner or a permanent secondary owner."""
    return user_id in config.PERMANENT_OWNERS_SET


def is_owner_or_temp(user_id: int) -> bool:
    """Returns True if the user is a permanent owner OR has a valid temporary authorization."""
    if is_permanent_owner(user_id):
        return True
    return state.is_temp_authorized(user_id)


async def global_check(ctx) -> bool:
    """Global check applied to ALL commands (equivalent to the old @bot.check)."""
    if is_permanent_owner(ctx.author.id):
        return True
    if state.kill_switch:
        return False
    if ctx.guild and ctx.guild.id in state.disabled_guilds:
        return False
    return True


def owner_check():
    """Permanent owner OR valid temporary owner."""
    async def predicate(ctx):
        if is_owner_or_temp(ctx.author.id):
            return True
        raise exceptions.NotOwnerOrTemp()
    return commands.check(predicate)


def permanent_owner_check():
    """Strictly restricted to permanent owners (principal + secondary), not temporary owners."""
    async def predicate(ctx):
        if is_permanent_owner(ctx.author.id):
            return True
        raise exceptions.NotPermanentOwner()
    return commands.check(predicate)


def owner_or_permission(**perms):
    """Owner (permanent/temporary) OR a specific Discord permission on the server."""
    async def predicate(ctx):
        if is_owner_or_temp(ctx.author.id):
            return True
        for perm, value in perms.items():
            if getattr(ctx.author.guild_permissions, perm, False) == value:
                return True
        raise exceptions.NotOwnerOrTemp()
    return commands.check(predicate)


def owner_or_guild_owner():
    """Owner (permanent/temporary) OR the owner of the server where the command is used."""
    async def predicate(ctx):
        if is_owner_or_temp(ctx.author.id):
            return True
        if ctx.guild and ctx.author.id == ctx.guild.owner_id:
            return True
        raise exceptions.NotOwnerOrGuildOwner()
    return commands.check(predicate)


def kill_switch_required():
    """Blocks the command if the global Kill Switch is active."""
    async def predicate(ctx):
        if state.kill_switch:
            raise exceptions.KillSwitchEnabled()
        return True
    return commands.check(predicate)"""
Toute la logique de permission du bot, centralisée ici.

Une seule source de vérité par type de vérification :

- is_permanent_owner / is_owner_or_temp : fonctions de bas niveau réutilisables
  partout (commandes ET vues/boutons).
- owner_check / permanent_owner_check / owner_or_permission / owner_or_guild_owner :
  decorators prêts à l'emploi pour les commandes.
- kill_switch_required : bloque une commande si le kill switch est actif.
- global_check : check global appliqué à toutes les commandes du bot.

Toutes les fonctions ci-dessous lèvent des exceptions typées (exceptions.py)
plutôt que des commands.CheckFailure génériques avec un message en dur --
voir exceptions.py pour le détail de pourquoi.
"""

from discord.ext import commands

import config
import exceptions
from state import state


def is_permanent_owner(user_id: int) -> bool:
    """True si l'utilisateur est l'owner principal ou un owner secondaire (permanent)."""
    return user_id in config.PERMANENT_OWNERS_SET


def is_owner_or_temp(user_id: int) -> bool:
    """True si owner permanent OU autorisation temporaire encore valide."""
    if is_permanent_owner(user_id):
        return True
    return state.is_temp_authorized(user_id)


async def global_check(ctx) -> bool:
    """Check global appliqué à TOUTES les commandes (équivalent à l'ancien @bot.check)."""
    if is_permanent_owner(ctx.author.id):
        return True
    if state.kill_switch:
        return False
    if ctx.guild and ctx.guild.id in state.disabled_guilds:
        return False
    return True


def owner_check():
    """Owner permanent OU owner temporaire valide."""
    async def predicate(ctx):
        if is_owner_or_temp(ctx.author.id):
            return True
        raise exceptions.NotOwnerOrTemp()
    return commands.check(predicate)


def permanent_owner_check():
    """Réservé strictement aux owners permanents (principal + secondaires), pas aux temporaires."""
    async def predicate(ctx):
        if is_permanent_owner(ctx.author.id):
            return True
        raise exceptions.NotPermanentOwner()
    return commands.check(predicate)


def owner_or_permission(**perms):
    """Owner (permanent/temporaire) OU une permission Discord précise sur le serveur."""
    async def predicate(ctx):
        if is_owner_or_temp(ctx.author.id):
            return True
        for perm, value in perms.items():
            if getattr(ctx.author.guild_permissions, perm, False) == value:
                return True
        raise exceptions.NotOwnerOrTemp()
    return commands.check(predicate)


def owner_or_guild_owner():
    """Owner (permanent/temporaire) OU propriétaire du serveur où la commande est lancée."""
    async def predicate(ctx):
        if is_owner_or_temp(ctx.author.id):
            return True
        if ctx.guild and ctx.author.id == ctx.guild.owner_id:
            return True
        raise exceptions.NotOwnerOrGuildOwner()
    return commands.check(predicate)


def kill_switch_required():
    """Bloque la commande si le kill switch global est actif."""
    async def predicate(ctx):
        if state.kill_switch:
            raise exceptions.KillSwitchEnabled()
        return True
    return commands.check(predicate)
