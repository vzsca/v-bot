import json

import pytest

from safe_json import JsonStoreError, atomic_write, load_object


def test_load_missing_file_returns_default(tmp_path):
    path = tmp_path / "store.json"
    assert load_object(path, {"ok": True}) == {"ok": True}


def test_load_corrupt_file_raises(tmp_path):
    path = tmp_path / "store.json"
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(JsonStoreError):
        load_object(path, {})


def test_atomic_write_round_trip(tmp_path):
    path = tmp_path / "store.json"
    atomic_write(path, {"value": 42})
    assert json.loads(path.read_text(encoding="utf-8")) == {"value": 42}
    assert not path.with_name(".store.json.tmp").exists()
