"""
Exceptions personnalisées pour les checks de permission et la protection
anti-double-exécution.
"""

from discord.ext import commands


class KillSwitchEnabled(commands.CheckFailure):
    """Le kill switch global est actif : la commande est bloquée."""

    def __init__(self, message: str = "🚫 Bot désactivé (kill switch actif)."):
        super().__init__(message)


class NotPermanentOwner(commands.CheckFailure):
    """Réservé aux owners permanents (principal + secondaires), pas aux temporaires."""

    def __init__(self, message: str = "❌ Cette commande est réservée aux owners permanents."):
        super().__init__(message)


class NotOwnerOrTemp(commands.CheckFailure):
    """Ni owner permanent, ni owner temporaire valide (et aucune permission Discord suffisante)."""

    def __init__(self, message: str = "❌ Tu n'as pas la permission d'utiliser cette commande."):
        super().__init__(message)


class NotOwnerOrGuildOwner(commands.CheckFailure):
    """Ni owner (permanent/temporaire), ni propriétaire du serveur courant."""

    def __init__(
        self,
        message: str = "❌ Seul le propriétaire du serveur ou un owner autorisé peut utiliser cette commande.",
    ):
        super().__init__(message)


class CommandAlreadyRunning(commands.CheckFailure):
    """Une instance de cette commande tourne déjà (protection anti-double-exécution)."""

    def __init__(
        self,
        message: str = "⏳ Cette commande est déjà en cours d'exécution sur ce serveur, attends qu'elle se termine.",
    ):
        super().__init__(message)
