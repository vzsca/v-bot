"""All bot permission logic, centralized here."""

from discord.ext import commands

import config
import exceptions
from state import state


def is_permanent_owner(user_id: int) -> bool:
    return user_id in config.PERMANENT_OWNERS_SET


def is_owner_or_temp(user_id: int, guild_id: int | None = None) -> bool:
    """Permanent owners are global; temporary authorization is guild-scoped."""
    return is_permanent_owner(user_id) or state.is_temp_authorized(guild_id, user_id)


async def global_check(ctx) -> bool:
    if is_permanent_owner(ctx.author.id):
        return True
    if state.kill_switch:
        return False
    if ctx.guild and ctx.guild.id in state.disabled_guilds:
        return False
    return True


def owner_check():
    async def predicate(ctx):
        if is_owner_or_temp(ctx.author.id, ctx.guild.id if ctx.guild else None):
            return True
        raise exceptions.NotOwnerOrTemp()
    return commands.check(predicate)


def permanent_owner_check():
    async def predicate(ctx):
        if is_permanent_owner(ctx.author.id):
            return True
        raise exceptions.NotPermanentOwner()
    return commands.check(predicate)


def owner_or_permission(**perms):
    async def predicate(ctx):
        if is_owner_or_temp(ctx.author.id, ctx.guild.id if ctx.guild else None):
            return True
        if not ctx.guild:
            raise exceptions.NotOwnerOrTemp()
        guild_permissions = ctx.author.guild_permissions
        if all(getattr(guild_permissions, perm, False) == value for perm, value in perms.items()):
            return True
        raise exceptions.NotOwnerOrTemp()
    return commands.check(predicate)


def owner_or_guild_owner():
    async def predicate(ctx):
        if is_owner_or_temp(ctx.author.id, ctx.guild.id if ctx.guild else None):
            return True
        if ctx.guild and ctx.author.id == ctx.guild.owner_id:
            return True
        raise exceptions.NotOwnerOrGuildOwner()
    return commands.check(predicate)


def kill_switch_required():
    async def predicate(ctx):
        if state.kill_switch:
            raise exceptions.KillSwitchEnabled()
        return True
    return commands.check(predicate)


def can_manage_member(ctx, target) -> bool:
    if not ctx.guild:
        return False
    if target.id == ctx.author.id or target.id == ctx.guild.owner_id:
        return False
    if ctx.author.id != ctx.guild.owner_id and target.top_role >= ctx.author.top_role:
        return False
    return True


def can_bot_manage_member(ctx, target) -> bool:
    me = ctx.guild.me if ctx.guild else None
    if me is None:
        return False
    if target.id == me.id:
        return False
    return target.top_role < me.top_role


def can_manage_role(ctx, role) -> bool:
    me = ctx.guild.me if ctx.guild else None
    if me is None:
        return False
    return role.is_assignable() and role < me.top_role
