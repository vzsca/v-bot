import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

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
