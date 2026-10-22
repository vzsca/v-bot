"""Moderation-only report logging commands."""

import logging
from datetime import datetime

import discord
from discord.ext import commands

import checks
import warm_store

logger = logging.getLogger("v-bot")


class WarmCog(commands.Cog, name="Reports"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="warm")
    @commands.guild_only()
    @checks.owner_or_permission(moderate_members=True)
    @checks.kill_switch_required()
    async def warm(self, ctx: commands.Context, member: discord.Member, *, reason: str = ""):
        """Record a moderation report for a member."""
        if member.id == ctx.author.id:
            await ctx.send("❌ You cannot report yourself.")
            return
        if member.bot:
            await ctx.send("❌ Bot accounts cannot be reported with this command.")
            return

        saved, report = warm_store.add(
            guild_id=ctx.guild.id,
            target_id=member.id,
            reporter_id=ctx.author.id,
            reason=reason,
        )
        if not saved or report is None:
            await ctx.send("❌ The report could not be saved. The storage limit may be reached or storage unavailable.")
            return

        embed = discord.Embed(
            title="📝 Warm enregistré",
            description=f"Un signalement concernant {member.mention} a été enregistré.",
            color=discord.Color.orange(),
            timestamp=datetime.fromisoformat(report["created_at"]),
        )
        embed.add_field(name="Raison", value=reason[:1000] if reason.strip() else "Aucune raison précisée.", inline=False)
        embed.set_footer(text=f"Signalé par {ctx.author} • ID: {member.id}")
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(name="lst_warm")
    @commands.guild_only()
    @checks.owner_or_permission(moderate_members=True)
    @checks.kill_switch_required()
    async def list_warm(self, ctx: commands.Context, member: discord.Member):
        """Show all stored reports for a member."""
        reports = warm_store.for_target(ctx.guild.id, member.id)
        if not reports:
            await ctx.send(f"ℹ️ Aucun warm enregistré pour {member.mention}.", allowed_mentions=discord.AllowedMentions.none())
            return

        for start in range(0, len(reports), 8):
            embed = discord.Embed(
                title=f"📋 WARM • {member}",
                description=f"{len(reports)} signalement(s) enregistré(s) sur ce serveur.",
                color=discord.Color.orange(),
            )
            for index, report in enumerate(reports[start:start + 8], start=start + 1):
                reporter = ctx.guild.get_member(report["reporter_id"])
                reporter_text = reporter.mention if reporter else f"ID {report['reporter_id']} (membre absent)"
                reason = report["reason"] or "Aucune raison précisée."
                embed.add_field(
                    name=f"#{index} • {report['created_at']}",
                    value=f"**Auteur :** {reporter_text}\n**Raison :** {reason[:1000]}",
                    inline=False,
                )
            embed.set_footer(text=f"Utilisateur ID : {member.id} • Page {start // 8 + 1}")
            await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


    @commands.command(name="delete_warm")
    @commands.guild_only()
    @checks.owner_or_permission(moderate_members=True)
    @checks.kill_switch_required()
    async def delete_warm(self, ctx: commands.Context, member: discord.Member, *, report_numbers: str):
        """Delete one, several, or all reports for a member."""
        tokens = report_numbers.split()
        if len(tokens) == 1 and tokens[0].lower() == "all":
            numbers = None
        else:
            if not tokens or any(token.lower() == "all" for token in tokens):
                await ctx.send(
                    "❌ Utilise `v!delete_warm @user #1 #2` ou `v!delete_warm @user all`."
                )
                return
            numbers = []
            for token in tokens:
                raw_number = token.removeprefix("#")
                if not raw_number.isdecimal() or int(raw_number) < 1:
                    await ctx.send(
                        "❌ Numéros invalides. Exemples : "
                        "`v!delete_warm @user #1 #2` ou `v!delete_warm @user all`."
                    )
                    return
                numbers.append(int(raw_number))
            numbers = sorted(set(numbers))

        deleted, reports = warm_store.delete_reports_for_target(
            guild_id=ctx.guild.id,
            target_id=member.id,
            report_numbers=numbers,
        )
        if not deleted:
            target = "tous les warms" if numbers is None else ", ".join(f"#{n}" for n in numbers)
            await ctx.send(
                f"❌ Aucun warm supprimé pour {member.mention}. Vérifie les numéros demandés : {target}.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        deleted_numbers = "tous" if numbers is None else ", ".join(f"#{n}" for n in numbers)
        embed = discord.Embed(
            title="🗑️ Warm(s) supprimé(s)",
            description=(
                f"{len(reports)} warm(s) supprimé(s) pour {member.mention} "
                f"(sélection : {deleted_numbers})."
            ),
            color=discord.Color.red(),
        )
        for index, report in enumerate(reports[:8], start=1):
            embed.add_field(
                name=f"Warm supprimé #{index} • {report['created_at']}",
                value=(report["reason"] or "Aucune raison précisée.")[:1000],
                inline=False,
            )
        if len(reports) > 8:
            embed.set_footer(text=f"{len(reports) - 8} autre(s) warm(s) supprimé(s).")
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())



async def setup(bot: commands.Bot):
    await bot.add_cog(WarmCog(bot))
