from updater import current_commit, requirements_changed


def test_current_commit_is_a_sha_or_empty():
    commit = current_commit()
    assert commit == "" or (len(commit) == 40 and all(char in "0123456789abcdef" for char in commit))


def test_requirements_changed_returns_false_for_same_commit():
    assert requirements_changed("abc", "abc") is False
    assert requirements_changed("", "def") is False
    assert requirements_changed("abc", "") is False
