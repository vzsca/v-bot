"""Bounded security audit log."""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / "security.log"
MAX_LOG_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5
logger = logging.getLogger("v-bot.security")
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]+")


def _clean(value: str) -> str:
    return _CONTROL_CHARS.sub(" ", str(value)).strip()


def _rotate_if_needed() -> None:
    try:
        if not LOG_FILE.exists() or LOG_FILE.stat().st_size < MAX_LOG_BYTES:
            return
        LOG_FILE.with_name(f"{LOG_FILE.name}.{BACKUP_COUNT}").unlink(missing_ok=True)
        for index in range(BACKUP_COUNT - 1, 0, -1):
            src = LOG_FILE.with_name(f"{LOG_FILE.name}.{index}")
            dst = LOG_FILE.with_name(f"{LOG_FILE.name}.{index + 1}")
            if src.exists():
                src.replace(dst)
        LOG_FILE.replace(LOG_FILE.with_name(f"{LOG_FILE.name}.1"))
    except OSError as exc:
        logger.warning("Security log rotation failed: %s", exc)


def log_security_event(message: str, actor: str | None = None) -> None:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    actor_part = f" [{_clean(actor)}]" if actor else ""
    line = f"{timestamp}{actor_part} {_clean(message)}\n"
    try:
        _rotate_if_needed()
        with LOG_FILE.open("a", encoding="utf-8") as file:
            file.write(line)
    except OSError as exc:
        logger.warning("Unable to write security log: %s", exc)
