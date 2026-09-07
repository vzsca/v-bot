"""Discord help command with permission-based category embeds and buttons."""

import discord
from discord.ext import commands

import checks
import config


class HelpCategoryView(discord.ui.View):
    def __init__(self, cog: "HelpCog", author_id: int, categories: list[str]):
        super().__init__(timeout=180)
        self.cog = cog
        self.author_id = author_id
        self.categories = categories
        for category, label, emoji in (
            ("general", "General", "📜"),
            ("mod", "Moderation", "🛡️"),
            ("admin", "Admin", "⚙️"),
            ("owner", "Owner", "👑"),
        ):
            if category not in categories:
                continue
            self.add_item(self._make_category_button(category, label, emoji))

    def _make_category_button(self, category: str, label: str, emoji: str) -> discord.ui.Button:
        button = discord.ui.Button(label=label, emoji=emoji, style=discord.ButtonStyle.secondary)

        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("❌ Ce menu ne t'est pas destiné.", ephemeral=True)
                return
            embeds = self.cog.available_embeds(interaction)
            if category not in embeds:
                await interaction.response.send_message("🔒 Tu n'as pas accès à cette catégorie.", ephemeral=True)
                return
            await interaction.response.edit_message(embeds=[embeds[category]], view=HelpBackView(self))

        button.callback = callback
        return button


class HelpBackView(discord.ui.View):
    def __init__(self, parent: HelpCategoryView):
        super().__init__(timeout=180)
        self.parent_view = parent

    @discord.ui.button(label="Menu des catégories", emoji="📚", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.parent_view.author_id:
            await interaction.response.send_message("❌ Ce menu ne t'est pas destiné.", ephemeral=True)
            return
        await interaction.response.edit_message(
            embeds=[self.parent_view.cog.menu_embed(interaction)],
            view=HelpCategoryView(self.parent_view.cog, self.parent_view.author_id, self.parent_view.categories),
        )


class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def has_moderation_access(ctx) -> bool:
        if not ctx.guild:
            return False
        permissions = ctx.author.guild_permissions
        return any(
            getattr(permissions, permission, False)
            for permission in (
                "moderate_members",
                "kick_members",
                "ban_members",
                "manage_messages",
                "manage_channels",
                "manage_roles",
            )
        )

    @staticmethod
    def has_admin_access(ctx) -> bool:
        return bool(ctx.guild and ctx.author.guild_permissions.administrator)

    def category_order(self, ctx) -> list[str]:
        categories = ["general"]
        if self.has_moderation_access(ctx):
            categories.append("mod")
        if self.has_admin_access(ctx):
            categories.append("admin")
        if checks.is_owner_or_temp(ctx.author.id, ctx.guild.id if ctx.guild else None):
            categories.append("owner")
        return categories

    def general_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📜  V-BOT • General Commands",
            description=(
                "Commands available to everyone.\n"
                "Use `/slash` commands or the `v!` prefix."
            ),
            color=discord.Color.blue(),
        )
        for name, description in (
            ("🖼️ `avatar [@user]`", "Display a user's avatar."),
            ("👤 `user_info [@user]`", "Display user information."),
            ("🏠 `server_info`", "Display server information."),
            ("💬 `snipe [index]`", "Display a deleted message."),
        ):
            embed.add_field(name=name, value=description, inline=False)
        embed.set_footer(text="v-bot • Help • General commands")
        return embed

    def moderation_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🛡️  V-BOT • Moderation",
            description=(
                "Moderation tools for members with the required server permissions.\n"
                "Each command still checks its specific Discord permission."
            ),
            color=discord.Color.orange(),
        )
        for name, description in (
            ("🔇 `mute @user <minutes> [reason]`", "Requires **Moderate Members**."),
            ("🔊 `unmute @user`", "Requires **Moderate Members**."),
            ("🦵 `kick @user [reason]`", "Requires **Kick Members**."),
            ("⛔ `ban @user [reason]`", "Requires **Ban Members**."),
            ("🔄 `unban <id>`", "Requires **Ban Members**."),
            ("🎭 `give_role @user @role`", "Requires **Manage Roles**."),
            ("🗑️ `clear <amount>`", "Requires **Manage Messages**."),
            ("⏳ `slowmode <seconds>`", "Requires **Manage Channels**."),
            ("🔒 `lock` / `unlock`", "Requires **Manage Channels**."),
        ):
            embed.add_field(name=name, value=description, inline=False)
        embed.set_footer(text="v-bot • Help • Server moderation")
        return embed

    def admin_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="⚙️  V-BOT • Admin & Announcements",
            description=(
                "Server administration, API configuration and automatic announcements.\n"
                "🔐 These commands require the **Administrator** permission."
            ),
            color=discord.Color.blurple(),
        )
        for name, description in (
            ("🔑 `set_api twitch|yt`", "Configure this server's own Twitch/YouTube API credentials."),
            ("📊 `api_status`", "Show the server API mode/status without exposing secrets."),
            ("🧹 `clear_api twitch|yt`", "Remove this server's API credentials."),
            ("📺 `create_annonce`", "Create an automatic Twitch/YouTube announcement."),
            ("📋 `annonces`", "List configured announcements on this server."),
            ("🧪 `test_annonce <id>`", "Test a configured announcement."),
            ("🗑️ `delete_annonce <id>`", "Delete a configured announcement."),
        ):
            embed.add_field(name=name, value=description, inline=False)
        embed.set_footer(text="v-bot • Help • Server administration")
        return embed

    def owner_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="👑  V-BOT • Owner Commands",
            description=(
                "Global bot administration and security controls.\n"
                "🔐 Owner access is required for this section."
            ),
            color=discord.Color.gold(),
        )
        for name, description in (
            ("📝 `embed <title> | <description>`", "Send a custom embed."),
            ("📌 `add_temp @user <duration>`", "Grant temporary authorization."),
            ("📄 `owner_list`", "List bot owners."),
            ("⚙️ `servers`", "Open server management."),
            ("🔁 `toggle_guild`", "Enable or disable the bot on the current server."),
            ("💬 `say <message>`", "Make the bot send a message."),
        ):
            embed.add_field(name=name, value=description, inline=False)

        sensitive = "🟢 **ENABLED**" if config.DANGEROUS_COMMANDS_ENABLED else "🔴 **DISABLED**"
        embed.add_field(
            name="🧨 Sensitive commands",
            value=(
                "`spam`, `dmall`, `raid`, `remove_raid`\n"
                f"Status: {sensitive}\n"
                "⚙️ Managed from the `start_bot.bat` panel → `toggle_dangerous`.\n"
                "🔄 Bot restart required after changing the setting."
            ),
            inline=False,
        )
        embed.add_field(
            name="🚨 `killswitch [true/false | on/off | 1/0]`",
            value=(
                "Global emergency security mode.\n"
                "✅ `true / on / 1` → block commands\n"
                "✅ `false / off / 0` → unblock commands\n"
                "ℹ️ No argument → display current status\n"
                "🔐 **Restricted to permanent owners only.**"
            ),
            inline=False,
        )
        embed.set_footer(text="v-bot • Owner controls • Sensitive actions")
        return embed

    def available_embeds(self, ctx) -> dict[str, discord.Embed]:
        embeds = {"general": self.general_embed()}
        if self.has_moderation_access(ctx):
            embeds["mod"] = self.moderation_embed()
        if self.has_admin_access(ctx):
            embeds["admin"] = self.admin_embed()
        if checks.is_owner_or_temp(ctx.author.id, ctx.guild.id if ctx.guild else None):
            embeds["owner"] = self.owner_embed()
        return embeds

    def menu_embed(self, ctx) -> discord.Embed:
        categories = self.category_order(ctx)
        embed = discord.Embed(
            title="📚  V-BOT • Help",
            description="Voici les catégories auxquelles tu as accès. Utilise les boutons pour ouvrir une catégorie.",
            color=discord.Color.dark_blue(),
        )
        labels = {
            "general": ("📜 General", "Commandes disponibles à tous."),
            "mod": ("🛡️ Moderation", "Commandes de modération selon tes permissions serveur."),
            "admin": ("⚙️ Admin & Announcements", "Configuration API et annonces ; Administrateur requis."),
            "owner": ("👑 Owner", "Administration globale du bot et sécurité."),
        }
        for category in categories:
            title, description = labels[category]
            embed.add_field(name=title, value=description, inline=False)
        embed.set_footer(text="v-bot • Help • Access is based on your current permissions")
        return embed

    @commands.command(name="help")
    @checks.kill_switch_required()
    async def help(self, ctx, category: str | None = None):
        category = (category or "").strip().lower()
        category_aliases = {
            "general": "general",
            "user": "general",
            "mod": "mod",
            "modo": "mod",
            "moderation": "mod",
            "admin": "admin",
            "announcement": "admin",
            "announcements": "admin",
            "owner": "owner",
        }
        if category:
            category = category_aliases.get(category, category)
            embeds = self.available_embeds(ctx)
            if category not in embeds:
                if category in {"mod", "admin", "owner"}:
                    await ctx.send(
                        embed=discord.Embed(
                            title="🔒 Access denied",
                            description="❌ You do not have permission to access this help category.",
                            color=discord.Color.red(),
                        )
                    )
                    return
                await ctx.send("❌ Unknown help category. Use `v!help` to see your available categories.")
                return
            await ctx.send(embed=embeds[category])
            return

        categories = self.category_order(ctx)
        if len(categories) == 1:
            await ctx.send(embed=self.general_embed())
            return

        await ctx.send(
            embed=self.menu_embed(ctx),
            view=HelpCategoryView(self, ctx.author.id, categories),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
