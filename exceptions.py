"""
Exceptions personnalisées pour les checks de permission et la protection
anti-double-exécution.

Avant, toutes les erreurs de permission étaient des commands.CheckFailure
génériques avec juste un message texte -- pour réagir différemment selon le
type d'erreur, il aurait fallu faire du matching sur le texte du message
(`if "Kill Switch" in str(error)`), fragile et illisible. Avec des classes
dédiées, le handler d'erreur fait juste `isinstance(error, KillSwitchEnabled)`
-- plus robuste (changer le message ne casse plus rien) et plus simple à
étendre.

Chaque exception garde un message par défaut (donc `str(error)` continue de
fonctionner partout où on l'utilisait déjà), mais reste une classe à part
entière qu'on peut détecter précisément avec isinstance().
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
