import os

os.environ.setdefault("DISCORD_TOKEN", "ci-dummy-token")
os.environ.setdefault("OWNER_PRINCIPAL_ID", "1")
os.environ.setdefault("OWNERS_SECONDARY_IDS", "")
os.environ.setdefault("DANGEROUS_COMMANDS_ENABLED", "false")

from security import _consume_action_code, issue_action_code
import security


def test_multiple_action_codes_can_be_active(tmp_path, monkeypatch):
    monkeypatch.setattr(security, "_ACTION_CODE_FILE", tmp_path / "action_codes.json")
    first, _ = issue_action_code()
    second, _ = issue_action_code()

    assert first != second
    assert _consume_action_code(first, "raid")
    assert _consume_action_code(second, "dmall")
    assert not _consume_action_code(first, "raid")
    assert not _consume_action_code(second, "dmall")


def test_expired_codes_are_removed(tmp_path, monkeypatch):
    monkeypatch.setattr(security, "_ACTION_CODE_FILE", tmp_path / "action_codes.json")
    monkeypatch.setattr(security.config, "ACTION_CODE_TTL", -1)

    code, _ = issue_action_code()

    assert not _consume_action_code(code, "raid")
    assert security._load_codes() == []
