import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from cogs.twitch import TwitchCog


def test_twitch_format_message_uses_current_title():
    result = TwitchCog._format_message(
        "Now live: {streamer} - {title} ({game}) {url}",
        {
            "streamer": "streamer",
            "title": "New title",
            "game": "Game",
            "url": "https://www.twitch.tv/streamer",
        },
    )

    assert result == "Now live: streamer - New title (Game) https://www.twitch.tv/streamer"


def test_twitch_announcement_message_is_edited_when_title_changes():
    message = SimpleNamespace(edit=AsyncMock())
    channel = SimpleNamespace(
        guild=SimpleNamespace(id=123),
        fetch_message=AsyncMock(return_value=message),
    )
    bot = SimpleNamespace(get_channel=lambda channel_id: channel)

    cog = TwitchCog.__new__(TwitchCog)
    cog.bot = bot

    announcement = {
        "id": 1,
        "guild_id": 123,
        "channel_id": 456,
        "discord_message_id": 789,
        "message": "Live: {title}",
        "last_title": "Old title",
    }
    stream_data = {
        "streamer": "streamer",
        "title": "New title",
        "game": "Game",
        "url": "https://www.twitch.tv/streamer",
    }

    updated = asyncio.run(cog._update_announcement_message(announcement, stream_data))

    assert updated is True
    message.edit.assert_awaited_once_with(content="Live: New title")


def test_twitch_announcement_message_is_not_edited_without_title_placeholder():
    message = SimpleNamespace(edit=AsyncMock())
    channel = SimpleNamespace(
        guild=SimpleNamespace(id=123),
        fetch_message=AsyncMock(return_value=message),
    )
    bot = SimpleNamespace(get_channel=lambda channel_id: channel

)
    cog = TwitchCog.__new__(TwitchCog)
    cog.bot = bot

    announcement = {
        "id": 1,
        "guild_id": 123,
        "channel_id": 456,
        "discord_message_id": 789,
        "message": "Live now! {url}",
        "last_title": "Old title",
    }

    updated = asyncio.run(
        cog._update_announcement_message(
            announcement,
            {
                "streamer": "streamer",
                "title": "New title",
                "game": "Game",
                "url": "https://www.twitch.tv/streamer",
            },
        )
    )

    assert updated is False
    message.edit.assert_not_awaited()
