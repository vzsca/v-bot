"""
All bot permission logic, centralized here.

A single source of truth for each type of check:

- is_permanent_owner / is_owner_or_temp: reusable low-level functions
  used everywhere (commands AND views/buttons).
- owner_check / permanent_owner_check / owner_or_permission / owner_or_guild_owner:
  ready-to-use decorators for commands.
- kill_switch_required: blocks a command if the Kill Switch is active.
- global_check: global check applied to all bot commands.
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
    return is_permanent_owner(user_id) or state.is_temp_authorized(user_id)


async def global_check(ctx) -> bool:
    """Global check applied to ALL commands."""
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
    """Strictly restricted to permanent owners, not temporary owners."""
    async def predicate(ctx):
        if is_permanent_owner(ctx.author.id):
            return True
        raise exceptions.NotPermanentOwner()
    return commands.check(predicate)


def owner_or_permission(**perms):
    """Owner (permanent/temporary) OR ALL requested Discord permissions."""
    async def predicate(ctx):
        if is_owner_or_temp(ctx.author.id):
            return True

        if not ctx.guild:
            raise exceptions.NotOwnerOrTemp()

        guild_permissions = ctx.author.guild_permissions
        if all(getattr(guild_permissions, perm, False) == value for perm, value in perms.items()):
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
    return commands.check(predicate)


def can_manage_member(ctx, target) -> bool:
    """Return whether the command author can moderate the target member."""
    if not ctx.guild:
        return False
    if target.id == ctx.author.id:
        return False
    if target.id == ctx.guild.owner_id:
        return False
    if ctx.author.id != ctx.guild.owner_id and target.top_role >= ctx.author.top_role:
        return False
    return True


def can_bot_manage_member(ctx, target) -> bool:
    """Return whether the bot can moderate the target member."""
    me = ctx.guild.me if ctx.guild else None
    if me is None:
        return False
    if target.id == me.id:
        return False
    return target.top_role < me.top_role


def can_manage_role(ctx, role) -> bool:
    """Return whether the bot's hierarchy allows managing the role."""
    me = ctx.guild.me if ctx.guild else None
    if me is None:
        return False
    return role.is_assignable() and role < me.top_role
