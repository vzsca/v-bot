import json

import announcement_store as store


def test_guild_isolation(monkeypatch, tmp_path):
    config_file = tmp_path / "annonce_config.json"
    monkeypatch.setattr(store, "CONFIG_FILE", config_file)
    data = {"announcements": [
        {"id": 1, "guild_id": 10, "channel_id": 100},
        {"id": 2, "guild_id": 20, "channel_id": 200},
        {"id": 3, "channel_id": 300},
    ]}
    assert store.save(data)
    loaded = store.load()
    assert [a["id"] for a in store.for_guild(loaded, 10)] == [1]
    assert store.find(loaded, 20, 2)["channel_id"] == 200
    assert store.find(loaded, 10, 2) is None


def test_atomic_save_produces_valid_json(monkeypatch, tmp_path):
    config_file = tmp_path / "annonce_config.json"
    monkeypatch.setattr(store, "CONFIG_FILE", config_file)
    assert store.save({"announcements": [{"id": 1, "guild_id": 42}]})
    assert json.loads(config_file.read_text(encoding="utf-8"))["announcements"][0]["guild_id"] == 42
