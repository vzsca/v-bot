import panel


def test_principal_youtube_channel_count_deduplicates_across_guilds(monkeypatch):
    monkeypatch.setattr(panel.api_access, "get_allowed_guilds", lambda: {100, 200, 300})
    monkeypatch.setattr(
        panel.announcement_store,
        "load",
        lambda: {
            "announcements": [
                {"guild_id": 100, "type": "youtube", "youtube_channel_id": "UC123"},
                {"guild_id": 200, "type": "youtube", "youtube_channel_id": "UC123"},
                {"guild_id": 300, "type": "youtube", "youtube_channel_id": "UC456"},
                {
                    "guild_id": 400,
                    "type": "youtube",
                    "youtube_channel_id": "UC789",
                },
                {"guild_id": 100, "type": "twitch", "channel_id": "streamer"},
            ]
        },
    )

    assert panel._principal_youtube_channel_count() == 2
