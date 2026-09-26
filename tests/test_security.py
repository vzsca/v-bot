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
    first, _ = security.issue_action_code("raid")
    second, _ = security.issue_action_code("dmall")

    assert first != second
    assert security._consume_action_code(first, "raid")
    assert security._consume_action_code(second, "dmall")
    assert not security._consume_action_code(first, "raid")
    assert not security._consume_action_code(second, "dmall")


def test_action_code_cannot_be_used_for_another_action(tmp_path, monkeypatch):
    security = _security_module()
    monkeypatch.setattr(security, "_ACTION_CODE_FILE", tmp_path / "action_codes.json")
    code, _ = security.issue_action_code("raid")

    assert not security._consume_action_code(code, "dmall")
    assert security._consume_action_code(code, "raid")
    assert not security._consume_action_code(code, "raid")


def test_action_code_rejects_empty_action(tmp_path, monkeypatch):
    security = _security_module()
    monkeypatch.setattr(security, "_ACTION_CODE_FILE", tmp_path / "action_codes.json")
    code, _ = security.issue_action_code("raid")

    assert not security._consume_action_code(code, "")
    assert security._consume_action_code(code, "raid")


def test_expired_codes_are_removed(tmp_path, monkeypatch):
    security = _security_module()
    monkeypatch.setattr(security, "_ACTION_CODE_FILE", tmp_path / "action_codes.json")
    monkeypatch.setattr(security.config, "ACTION_CODE_TTL", -1)

    code, _ = security.issue_action_code("raid")

    assert not security._consume_action_code(code, "raid")
    assert security._load_codes() == []
