import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord

from cogs.youtube import YouTubeCog


def test_latest_video_lookup_cache_is_shared_by_api_key_and_channel():
    cog = YouTubeCog.__new__(YouTubeCog)
    cog._channel_cache = {}
    cog._latest_cache = {}
    cog._backoff_until = {}

    cog._get_uploads_playlist = AsyncMock(return_value="UU123")
    cog._api_get = AsyncMock(
        return_value=(
            {
                "items": [
                    {
                        "contentDetails": {"videoId": "video123"},
                        "snippet": {"channelTitle": "Creator", "title": "Video"},
                    }
                ]
            },
            200,
        )
    )

    session = SimpleNamespace()
    first = asyncio.run(cog._get_latest_video(session, "API_KEY", "UC123"))
    second = asyncio.run(cog._get_latest_video(session, "API_KEY", "UC123"))

    assert first == second
    cog._get_uploads_playlist.assert_awaited_once_with(session, "API_KEY", "UC123")
    cog._api_get.assert_awaited_once()


def test_youtube_announcement_allows_template_mentions():
    channel = SimpleNamespace(
        guild=SimpleNamespace(id=123),
        send=AsyncMock(),
    )
    cog = YouTubeCog.__new__(YouTubeCog)
    cog.bot = SimpleNamespace(get_channel=lambda channel_id: channel)

    result = asyncio.run(
        cog._send_announcement(
            {
                "guild_id": 123,
                "channel_id": 456,
                "message": "New video: {title}",
            },
            {"title": "@everyone"},
        )
    )

    assert result is True
    channel.send.assert_awaited_once()
    assert channel.send.await_args.args == ("New video: @everyone",)
    assert channel.send.await_args.kwargs["allowed_mentions"].to_dict() == discord.AllowedMentions(everyone=True, roles=True, users=True).to_dict()


def test_youtube_poll_fetches_same_channel_once_for_multiple_guilds(monkeypatch):
    cog = YouTubeCog.__new__(YouTubeCog)
    cog._channel_cache = {}
    cog._latest_cache = {}
    cog._backoff_until = {}

    announcements = [
        {
            "id": 1,
            "guild_id": 100,
            "type": "youtube",
            "source_url": "https://www.youtube.com/@creator",
            "youtube_channel_id": "UC123",
            "last_video_id": "old",
            "channel_id": 1001,
            "message": "New: {title}",
        },
        {
            "id": 2,
            "guild_id": 200,
            "type": "youtube",
            "source_url": "https://www.youtube.com/@creator",
            "youtube_channel_id": "UC123",
            "last_video_id": "old",
            "channel_id": 2001,
            "message": "New: {title}",
        },
    ]

    session = SimpleNamespace()
    monkeypatch.setattr(
        "cogs.youtube.store.load",
        lambda: {"announcements": announcements},
    )
    monkeypatch.setattr(
        "cogs.youtube.integration_config.get_youtube_api_key",
        lambda guild_id: "API_KEY",
    )
    monkeypatch.setattr(cog, "_get_session", AsyncMock(return_value=session))
    monkeypatch.setattr(
        cog,
        "_get_latest_video",
        AsyncMock(
            return_value={
                "video_id": "new",
                "channel": "Creator",
                "title": "New video",
                "url": "https://www.youtube.com/watch?v=new",
            }
        ),
    )
    monkeypatch.setattr(cog, "_send_announcement", AsyncMock(return_value=True))
    monkeypatch.setattr(
        "cogs.youtube.store.transaction",
        lambda mutator: (True, mutator({"announcements": announcements})),
    )

    asyncio.run(cog._poll_youtube_announcements())

    cog._get_latest_video.assert_awaited_once_with(
        session,
        "API_KEY",
        "UC123",
    )
    assert cog._send_announcement.await_count == 2
