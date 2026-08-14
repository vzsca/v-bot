"""
Journal séparé pour les événements de sécurité : bascule du kill switch,
octroi de droits owner (temporaire ou permanent), activation/désactivation
des commandes sensibles, changement de token.

Pourquoi un module à part plutôt que d'utiliser le logger Python habituel
(logging.getLogger) : le bot (main.py) et le panel (panel.py) sont deux
process séparés qui ne partagent pas d'objets Python -- pas de logger en
commun possible entre les deux. Ce module écrit directement dans
security.log, ce qui marche aussi bien appelé depuis le bot que depuis le
panel, sans dépendre de l'un ou l'autre process.

Volontairement minimal : pas de rotation, pas de niveaux, juste un fichier
texte append-only avec horodatage. Le but est l'audit ("qui a fait quoi
quand"), pas le débogage général (qui reste dans bot.log).
"""

from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / "security.log"


def log_security_event(message: str, actor: str | None = None) -> None:
    """
    Ajoute une ligne horodatée à security.log. Ne lève jamais d'exception
    (best-effort) -- un problème d'écriture de log ne doit jamais faire
    planter la commande qui l'a déclenché.

    IMPORTANT : ne jamais passer de secret (token, etc.) dans `message` --
    seulement des événements ("token changé", pas la valeur du token).
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    actor_part = f" [{actor}]" if actor else ""
    line = f"{timestamp}{actor_part} {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass
