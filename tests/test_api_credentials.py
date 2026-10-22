import api_credentials


def test_guild_credentials_are_isolated(tmp_path, monkeypatch):
    config_file = tmp_path / "api_credentials.json"
    monkeypatch.setattr(api_credentials, "CONFIG_FILE", config_file)
    api_credentials.set_credentials(1, "youtube", {"api_key": "server-one-key"})
    assert api_credentials.get(1, "youtube")["api_key"] == "server-one-key"
    assert api_credentials.get(2, "youtube") is None


def test_remove_credentials(tmp_path, monkeypatch):
    config_file = tmp_path / "api_credentials.json"
    monkeypatch.setattr(api_credentials, "CONFIG_FILE", config_file)
    api_credentials.set_credentials(1, "twitch", {"client_id": "client-id", "client_secret": "client-secret"})
    assert api_credentials.remove(1, "twitch")
    assert api_credentials.get(1, "twitch") is None



def test_credentials_file_is_private_on_posix(tmp_path, monkeypatch):
    import os
    import stat

    if os.name == "nt":
        return
    config_file = tmp_path / "api_credentials.json"
    monkeypatch.setattr(api_credentials, "CONFIG_FILE", config_file)
    api_credentials.set_credentials(1, "youtube", {"api_key": "test-key"})
    assert stat.S_IMODE(config_file.stat().st_mode) == 0o600


def test_existing_credentials_file_permissions_are_restricted(tmp_path, monkeypatch):
    import os
    import stat

    if os.name == "nt":
        return
    config_file = tmp_path / "api_credentials.json"
    config_file.write_text('{"1": {"youtube": {"api_key": "test-key"}}}', encoding="utf-8")
    config_file.chmod(0o644)
    monkeypatch.setattr(api_credentials, "CONFIG_FILE", config_file)
    assert api_credentials.get(1, "youtube")["api_key"] == "test-key"
    assert stat.S_IMODE(config_file.stat().st_mode) == 0o600
