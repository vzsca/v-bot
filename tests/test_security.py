import os

os.environ.setdefault("DISCORD_TOKEN", "ci-dummy-token")
os.environ.setdefault("OWNER_PRINCIPAL_ID", "1")
os.environ.setdefault("OWNERS_SECONDARY_IDS", "")
os.environ.setdefault("DANGEROUS_COMMANDS_ENABLED", "false")


def _security_module():
    import security

    return security


def test_multiple_action_codes_can_be_active(tmp_path, monkeypatch):
    security = _security_module()
    monkeypatch.setattr(security, "_ACTION_CODE_FILE", tmp_path / "action_codes.json")
    first, _ = security.issue_action_code()
    second, _ = security.issue_action_code()

    assert first != second
    assert security._consume_action_code(first, "raid")
    assert security._consume_action_code(second, "dmall")
    assert not security._consume_action_code(first, "raid")
    assert not security._consume_action_code(second, "dmall")


def test_expired_codes_are_removed(tmp_path, monkeypatch):
    security = _security_module()
    monkeypatch.setattr(security, "_ACTION_CODE_FILE", tmp_path / "action_codes.json")
    monkeypatch.setattr(security.config, "ACTION_CODE_TTL", -1)

    code, _ = security.issue_action_code()

    assert not security._consume_action_code(code, "raid")
    assert security._load_codes() == []
