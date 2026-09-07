"""Best-effort security audit log with bounded disk usage."""

from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / "security.log"
MAX_LOG_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5


def _rotate_if_needed() -> None:
    try:
        if not LOG_FILE.exists() or LOG_FILE.stat().st_size < MAX_LOG_BYTES:
            return
        oldest = LOG_FILE.with_name(f"{LOG_FILE.name}.{BACKUP_COUNT}")
        oldest.unlink(missing_ok=True)
        for index in range(BACKUP_COUNT - 1, 0, -1):
            src = LOG_FILE.with_name(f"{LOG_FILE.name}.{index}")
            dst = LOG_FILE.with_name(f"{LOG_FILE.name}.{index + 1}")
            if src.exists():
                src.replace(dst)
        LOG_FILE.replace(LOG_FILE.with_name(f"{LOG_FILE.name}.1"))
    except OSError:
        pass


def log_security_event(message: str, actor: str | None = None) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    actor_part = f" [{actor}]" if actor else ""
    line = f"{timestamp}{actor_part} {message}\n"
    try:
        _rotate_if_needed()
        with LOG_FILE.open("a", encoding="utf-8") as file:
            file.write(line)
    except OSError:
        pass
