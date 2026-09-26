"""Fail-safe JSON persistence helpers."""

from __future__ import annotations

import json
import logging
import os
import tempfile
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


def _fsync_directory(directory: Path) -> None:
    """Persist a completed rename on POSIX filesystems."""
    if os.name != "posix":
        return
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        logger.warning("Could not fsync JSON store directory %s", directory)
    finally:
        os.close(fd)


def atomic_write(path: Path, data: object, *, mode: int | None = None) -> None:
    """Write JSON atomically, durably, and without sharing a fixed temp filename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temp_path = Path(temp_name)
        if mode is not None:
            try:
                os.fchmod(fd, mode)
            except OSError:
                logger.warning("Could not set permissions on temporary JSON file %s", temp_path)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
        temp_path = None
        if mode is not None:
            try:
                path.chmod(mode)
            except OSError:
                logger.warning("Could not set permissions on JSON file %s", path)
        _fsync_directory(path.parent)
    except (OSError, TypeError, ValueError) as exc:
        logger.error("Unable to safely save JSON file %s: %s", path, exc)
        raise JsonStoreError(f"Unable to save JSON file: {path}") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
