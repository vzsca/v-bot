import subprocess

import updater


def test_current_commit_is_a_sha_or_empty():
    commit = updater.current_commit()
    assert commit == "" or (len(commit) == 40 and all(char in "0123456789abcdef" for char in commit))


def test_requirements_changed_returns_false_for_same_commit():
    assert updater.requirements_changed("abc", "abc") is False
    assert updater.requirements_changed("", "def") is False
    assert updater.requirements_changed("abc", "") is False


def test_rollback_code_uses_hard_reset(monkeypatch):
    calls = []

    def fake_run_git(*args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args=["git", *args], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(updater, "_run_git", fake_run_git)
    ok, message = updater.rollback_code("a" * 40)
    assert ok is True
    assert "aaaaaaa" in message
    assert calls == [("reset", "--hard", "a" * 40)]
