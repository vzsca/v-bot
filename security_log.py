"""
Separate log for security events: Kill Switch toggles,
owner permission grants (temporary or permanent), sensitive command
activation/deactivation, and token changes.

Why use a separate module instead of the standard Python logger
(logging.getLogger): the bot (main.py) and the panel (panel.py) are two
separate processes that do not share Python objects -- a shared logger
between the two is not possible. This module writes directly to
security.log, which works equally well when called from the bot or the
panel, without depending on either process.

Intentionally minimal: no rotation, no levels, just an append-only text
file with timestamps. The purpose is auditing ("who did what and when"),
not general debugging (which remains in bot.log).
"""

from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / "security.log"


def log_security_event(message: str, actor: str | None = None) -> None:
    """
    Adds a timestamped line to security.log. Never raises an exception
    (best-effort) -- a logging write failure must never crash the command
    that triggered it.

    IMPORTANT: never pass a secret (token, etc.) in `message` --
    only events ("token changed", not the token value).
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    actor_part = f" [{actor}]" if actor else ""
    line = f"{timestamp}{actor_part} {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass
