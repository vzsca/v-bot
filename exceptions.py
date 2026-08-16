"""
Custom exceptions for permission checks and
anti-double-execution protection.
"""

from discord.ext import commands


class KillSwitchEnabled(commands.CheckFailure):
    """The global Kill Switch is active: the command is blocked."""

    def __init__(self, message: str = "🚫 Bot disabled (Kill Switch active)."):
        super().__init__(message)


class NotPermanentOwner(commands.CheckFailure):
    """Restricted to permanent owners (principal + secondary), not temporary owners."""

    def __init__(self, message: str = "❌ This command is restricted to permanent owners."):
        super().__init__(message)


class NotOwnerOrTemp(commands.CheckFailure):
    """Neither a permanent nor valid temporary owner (and no sufficient Discord permission)."""

    def __init__(self, message: str = "❌ You do not have permission to use this command."):
        super().__init__(message)


class NotOwnerOrGuildOwner(commands.CheckFailure):
    """Neither an owner (permanent/temporary) nor the current server owner."""

    def __init__(
        self,
        message: str = "❌ Only the server owner or an authorized owner can use this command.",
    ):
        super().__init__(message)


class CommandAlreadyRunning(commands.CheckFailure):
    """An instance of this command is already running (anti-double-execution protection)."""

    def __init__(
        self,
        message: str = "⏳ This command is already running on this server. Please wait for it to finish.",
    ):
        super().__init__(message)"""
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
