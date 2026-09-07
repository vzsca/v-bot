"""Defensive anti-spam and anti-raid detection."""

from __future__ import annotations

import time
from collections import defaultdict, deque

import discord
from discord.ext import commands, tasks

import config
import security_log


class SecurityCog(commands.Cog, name="Security"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._messages: dict[tuple[int, int], deque[float]] = defaultdict(deque)
        self._joins: dict[int, deque[float]] = defaultdict(deque)
        self._alerts: dict[tuple[int, int, str], float] = {}
        self.cleanup.start()

    def cog_unload(self):
        self.cleanup.cancel()

    def _alert_once(self, guild_id: int, user_id: int, kind: str, message: str) -> None:
        now = time.monotonic()
        key = (guild_id, user_id, kind)
        if self._alerts.get(key, 0) > now:
            return
        self._alerts[key] = now + config.SUSPICIOUS_ACTION_WINDOW
        security_log.log_security_event(message, actor=str(user_id))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        key = (message.guild.id, message.author.id)
        now = time.monotonic()
        bucket = self._messages[key]
        cutoff = now - config.ANTI_SPAM_WINDOW
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        bucket.append(now)
        if len(bucket) >= config.ANTI_SPAM_THRESHOLD:
            self._alert_once(
                message.guild.id,
                message.author.id,
                "spam",
                f"Anti-spam alert: guild={message.guild.id} user={message.author.id} "
                f"{len(bucket)} messages/{config.ANTI_SPAM_WINDOW:.0f}s",
            )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        now = time.monotonic()
        bucket = self._joins[member.guild.id]
        cutoff = now - config.ANTI_RAID_WINDOW
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        bucket.append(now)
        if len(bucket) >= config.ANTI_RAID_THRESHOLD:
            self._alert_once(
                member.guild.id,
                member.id,
                "raid",
                f"Anti-raid alert: guild={member.guild.id} {len(bucket)} joins/{config.ANTI_RAID_WINDOW:.0f}s",
            )

    @tasks.loop(seconds=60)
    async def cleanup(self):
        now = time.monotonic()
        message_cutoff = now - config.ANTI_SPAM_WINDOW
        join_cutoff = now - config.ANTI_RAID_WINDOW
        for key, bucket in list(self._messages.items()):
            while bucket and bucket[0] <= message_cutoff:
                bucket.popleft()
            if not bucket:
                self._messages.pop(key, None)
        for guild_id, bucket in list(self._joins.items()):
            while bucket and bucket[0] <= join_cutoff:
                bucket.popleft()
            if not bucket:
                self._joins.pop(guild_id, None)
        self._alerts = {key: expiry for key, expiry in self._alerts.items() if expiry > now}


async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityCog(bot))
