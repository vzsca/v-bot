import json

import pytest

import warm_store
from safe_json import JsonStoreError


def _use_store(tmp_path, monkeypatch):
    path = tmp_path / "warm_reports.json"
    monkeypatch.setattr(warm_store, "STORE_FILE", path)
    return path


def test_add_persists_trimmed_report_and_returns_timestamp(tmp_path, monkeypatch):
    path = _use_store(tmp_path, monkeypatch)

    saved, report = warm_store.add(10, 20, 30, "  repeated spam  ")

    assert saved is True
    assert report is not None
    assert report["guild_id"] == 10
    assert report["target_id"] == 20
    assert report["reporter_id"] == 30
    assert report["reason"] == "repeated spam"
    assert report["created_at"].endswith("+00:00")
    assert json.loads(path.read_text(encoding="utf-8")) == {"reports": [report]}


def test_reports_are_isolated_by_guild_and_target(tmp_path, monkeypatch):
    _use_store(tmp_path, monkeypatch)
    warm_store.add(1, 100, 11, "guild one")
    warm_store.add(2, 100, 22, "guild two")
    warm_store.add(1, 200, 33, "different target")

    assert [r["reason"] for r in warm_store.for_target(1, 100)] == ["guild one"]
    assert [r["reason"] for r in warm_store.for_target(2, 100)] == ["guild two"]
    assert warm_store.for_target(1, 999) == []


def test_delete_uses_one_based_number_for_target_only(tmp_path, monkeypatch):
    _use_store(tmp_path, monkeypatch)
    warm_store.add(1, 100, 11, "first")
    warm_store.add(1, 200, 22, "other target")
    warm_store.add(1, 100, 33, "second")

    deleted, report = warm_store.delete_for_target(1, 100, 2)

    assert deleted is True
    assert report["reason"] == "second"
    assert [r["reason"] for r in warm_store.for_target(1, 100)] == ["first"]
    assert [r["reason"] for r in warm_store.for_target(1, 200)] == ["other target"]


@pytest.mark.parametrize("number", [0, -1])
def test_delete_rejects_non_positive_number_without_mutating_store(tmp_path, monkeypatch, number):
    path = _use_store(tmp_path, monkeypatch)
    warm_store.add(1, 100, 11, "keep")
    before = path.read_text(encoding="utf-8")

    assert warm_store.delete_for_target(1, 100, number) == (False, None)
    assert path.read_text(encoding="utf-8") == before


def test_delete_rejects_missing_report(tmp_path, monkeypatch):
    _use_store(tmp_path, monkeypatch)
    warm_store.add(1, 100, 11, "existing")

    assert warm_store.delete_for_target(1, 100, 2) == (False, None)
    assert warm_store.delete_for_target(2, 100, 1) == (False, None)


def test_add_enforces_per_guild_limit_only(tmp_path, monkeypatch):
    _use_store(tmp_path, monkeypatch)
    monkeypatch.setattr(warm_store, "MAX_REPORTS_PER_GUILD", 2)

    assert warm_store.add(1, 100, 11, "one")[0] is True
    assert warm_store.add(1, 100, 12, "two")[0] is True
    assert warm_store.add(1, 100, 13, "limit")[0] is False
    assert warm_store.add(2, 100, 14, "other guild")[0] is True
    assert len(warm_store.for_target(1, 100)) == 2


def test_corrupt_json_fails_closed_instead_of_overwriting(tmp_path, monkeypatch):
    path = _use_store(tmp_path, monkeypatch)
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(JsonStoreError):
        warm_store.for_target(1, 100)

    assert path.read_text(encoding="utf-8") == "{broken"


def test_normalization_discards_invalid_records_and_bounds_fields(tmp_path, monkeypatch):
    path = _use_store(tmp_path, monkeypatch)
    path.write_text(
        json.dumps(
            {
                "reports": [
                    {
                        "guild_id": 1,
                        "target_id": 2,
                        "reporter_id": 3,
                        "created_at": "x" * 60,
                        "reason": "r" * 1200,
                    },
                    {"guild_id": -1, "target_id": 2, "reporter_id": 3, "created_at": "now"},
                    "not a report",
                ]
            }
        ),
        encoding="utf-8",
    )

    reports = warm_store.for_target(1, 2)

    assert len(reports) == 1
    assert len(reports[0]["created_at"]) == 40
    assert len(reports[0]["reason"]) == 1000


def test_delete_multiple_reports_by_original_numbers_atomically(tmp_path, monkeypatch):
    _use_store(tmp_path, monkeypatch)
    warm_store.add(1, 100, 11, "first")
    warm_store.add(1, 100, 12, "second")
    warm_store.add(1, 100, 13, "third")
    warm_store.add(1, 200, 14, "other target")

    deleted, reports = warm_store.delete_reports_for_target(1, 100, [1, 3, 3])

    assert deleted is True
    assert [report["reason"] for report in reports] == ["first", "third"]
    assert [report["reason"] for report in warm_store.for_target(1, 100)] == ["second"]
    assert [report["reason"] for report in warm_store.for_target(1, 200)] == ["other target"]


def test_delete_all_reports_for_target_keeps_other_targets_and_guilds(tmp_path, monkeypatch):
    _use_store(tmp_path, monkeypatch)
    warm_store.add(1, 100, 11, "first")
    warm_store.add(1, 100, 12, "second")
    warm_store.add(1, 200, 13, "other target")
    warm_store.add(2, 100, 14, "other guild")

    deleted, reports = warm_store.delete_reports_for_target(1, 100, None)

    assert deleted is True
    assert [report["reason"] for report in reports] == ["first", "second"]
    assert warm_store.for_target(1, 100) == []
    assert [r["reason"] for r in warm_store.for_target(1, 200)] == ["other target"]
    assert [r["reason"] for r in warm_store.for_target(2, 100)] == ["other guild"]


def test_delete_multiple_rejects_missing_number_without_partial_deletion(tmp_path, monkeypatch):
    path = _use_store(tmp_path, monkeypatch)
    warm_store.add(1, 100, 11, "first")
    warm_store.add(1, 100, 12, "second")
    before = path.read_text(encoding="utf-8")

    assert warm_store.delete_reports_for_target(1, 100, [1, 3]) == (False, [])
    assert path.read_text(encoding="utf-8") == before
