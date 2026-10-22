from cogs.instagram import InstagramCog


def test_instagram_url_parser_accepts_profile_urls_only():
    assert InstagramCog._username_from_url("https://www.instagram.com/example.user/") == "example.user"
    assert InstagramCog._username_from_url("https://instagram.com/example_user") == "example_user"
    assert InstagramCog._username_from_url("https://instagram.com/reel/ABC123/") is None
    assert InstagramCog._username_from_url("https://example.com/example_user") is None
    assert InstagramCog._username_from_url("javascript:alert(1)") is None


def test_instagram_video_filter_ignores_photos_and_invalid_items():
    photo = {"id": "photo", "media_type": "IMAGE", "permalink": "https://instagram.com/p/photo/"}
    video = {"id": "video", "media_type": "VIDEO", "permalink": "https://instagram.com/reel/video/"}
    invalid_video = {"id": "no-link", "media_type": "VIDEO"}

    assert InstagramCog._select_latest_video([photo, invalid_video, video]) == video
    assert InstagramCog._select_latest_video([photo, invalid_video]) is None
    assert InstagramCog._select_latest_video(None) is None


def test_instagram_message_format_uses_safe_defaults_and_truncates():
    message = InstagramCog._format_message(
        "{channel}: {title} {url}",
        {"username": "example", "caption": "", "permalink": "https://instagram.com/reel/123/"},
    )
    assert message == "example: Nouvelle vidéo Instagram https://instagram.com/reel/123/"
    assert len(InstagramCog._format_message("x" * 2100, {})) == 2000
