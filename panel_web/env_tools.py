"""Safe .env read/write helpers shared by the web panel."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


def _read_lines() -> list[str]:
    if not ENV_PATH.exists():
        return []
    return ENV_PATH.read_text(encoding="utf-8").splitlines()


def set_env_value(key: str, value: str) -> None:
    if not key or "=" in key or "\n" in key or "\r" in key:
        raise ValueError("Invalid .env key.")
    if "\n" in value or "\r" in value:
        raise ValueError(".env values cannot contain newlines.")
    lines = _read_lines()
    prefix = f"{key}="
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = f"{key}={value}"
            replaced = True
            break
    if not replaced:
        lines.append(f"{key}={value}")
    content = "\n".join(lines) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=".env.", suffix=".tmp", dir=ROOT, text=True)
    temp_path = Path(temp_name)
    try:
        if os.name != "nt":
            os.chmod(temp_path, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, ENV_PATH)
        if os.name != "nt":
            os.chmod(ENV_PATH, 0o600)
    finally:
        temp_path.unlink(missing_ok=True)
