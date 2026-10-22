import integration_config


def test_instagram_credentials_use_guild_scoped_storage(monkeypatch):
    monkeypatch.setattr(integration_config.api_access, "is_allowed", lambda guild_id: False)
    credentials = {
        101: {"access_token": "token-for-guild-101", "user_id": "123456"},
        202: {"access_token": "token-for-guild-202", "user_id": "654321"},
    }
    monkeypatch.setattr(
        integration_config.api_credentials,
        "get",
        lambda guild_id, platform: credentials.get(guild_id) if platform == "instagram" else None,
    )

    assert integration_config.get_instagram_credentials(101) == ("token-for-guild-101", "123456")
    assert integration_config.get_instagram_credentials(202) == ("token-for-guild-202", "654321")
    assert integration_config.get_instagram_credentials(303) is None


def test_instagram_credentials_use_primary_api_for_allowed_guild(monkeypatch):
    monkeypatch.setattr(integration_config.api_access, "is_allowed", lambda guild_id: guild_id == 101)
    monkeypatch.setattr(
        integration_config,
        "_env",
        lambda: {"INSTAGRAM_ACCESS_TOKEN": "primary-token-value", "INSTAGRAM_USER_ID": "123456"},
    )
    monkeypatch.setattr(
        integration_config.api_credentials,
        "get",
        lambda guild_id, platform: {"access_token": "other-token-value", "user_id": "654321"},
    )

    assert integration_config.get_instagram_credentials(101) == ("primary-token-value", "123456")
    assert integration_config.get_instagram_credentials(202) == ("other-token-value", "654321")


def test_instagram_credentials_reject_invalid_account_id(monkeypatch):
    monkeypatch.setattr(integration_config.api_access, "is_allowed", lambda guild_id: False)
    monkeypatch.setattr(
        integration_config.api_credentials,
        "get",
        lambda guild_id, platform: {"access_token": "valid-token-value", "user_id": "not-numeric"},
    )

    assert integration_config.get_instagram_credentials(101) is None
    assert not integration_config.is_configured(101, "instagram")
