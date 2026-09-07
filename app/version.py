"""Project version derived from Git, with a source-tree fallback."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FALLBACK_VERSION = "3.8.2"


def _git_version() -> str | None:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--match", "v[0-9]*", "--always", "--dirty"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    if not value:
        return None
    if value.startswith("v"):
        value = value[1:]
    return value


VERSION = _git_version() or FALLBACK_VERSION
