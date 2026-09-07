"""Fail-safe JSON persistence helpers."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger("v-bot")


class JsonStoreError(RuntimeError):
    """Raised when a JSON store cannot be safely read or written."""


def load_object(path: Path, default: object) -> object:
    """Load JSON without silently treating corruption as an empty store."""
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Unable to safely load JSON file %s: %s", path, exc)
        raise JsonStoreError(f"Unable to load JSON file: {path}") from exc


def atomic_write(path: Path, data: object, *, mode: int | None = None) -> None:
    """Write JSON atomically and preserve existing data on failure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
        if mode is not None:
            try:
                temp.chmod(mode)
            except OSError:
                logger.warning("Could not set permissions on temporary JSON file %s", temp)
        temp.replace(path)
        if mode is not None:
            try:
                path.chmod(mode)
            except OSError:
                logger.warning("Could not set permissions on JSON file %s", path)
    except OSError as exc:
        logger.error("Unable to safely save JSON file %s: %s", path, exc)
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass
        raise JsonStoreError(f"Unable to save JSON file: {path}") from exc
