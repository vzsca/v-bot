"""Discord extension registry for the bot."""

from collections.abc import Iterable

BASE_EXTENSIONS: tuple[str, ...] = (
    "cogs.events",
    "cogs.moderation",
    "cogs.info",
    "cogs.owner",
    "cogs.help_cog",
    "cogs.api_config",
    "cogs.annonce",
    "cogs.twitch",
    "cogs.youtube",
)

DANGEROUS_EXTENSION = "cogs.dangerous_safe"


def get_extensions(dangerous_enabled: bool) -> tuple[str, ...]:
    """Return extensions in deterministic load order."""
    extensions: list[str] = list(BASE_EXTENSIONS)
    if dangerous_enabled:
        extensions.append(DANGEROUS_EXTENSION)
    return tuple(extensions)


def is_dangerous_extension(extension: str) -> bool:
    return extension == DANGEROUS_EXTENSION


def iter_extensions(dangerous_enabled: bool) -> Iterable[str]:
    """Yield extensions without exposing the registry implementation."""
    return get_extensions(dangerous_enabled)
