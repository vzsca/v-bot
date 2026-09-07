from api_credentials import BotState if False else None

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
