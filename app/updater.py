"""Git-based code update helpers that preserve local runtime data."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run_git(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )


def current_commit() -> str:
    result = _run_git("rev-parse", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else ""


def repository_status(fetch: bool = True) -> tuple[bool, int, int, str]:
    """Return (ok, behind, ahead, message) relative to origin/main."""
    if not (ROOT / ".git").exists():
        return False, 0, 0, "Not a Git repository."
    if fetch:
        result = _run_git("fetch", "--quiet", "origin", "main")
        if result.returncode != 0:
            return False, 0, 0, result.stderr.strip() or "Unable to contact origin/main."
    result = _run_git("rev-list", "--left-right", "--count", "HEAD...origin/main")
    if result.returncode != 0:
        return False, 0, 0, result.stderr.strip() or "Unable to compare local code with origin/main."
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        return False, 0, 0, "Unexpected Git comparison result."
    ahead, behind = int(parts[0]), int(parts[1])
    if behind:
        return True, behind, ahead, f"{behind} update(s) available from origin/main."
    if ahead:
        return True, 0, ahead, f"Local branch is {ahead} commit(s) ahead of origin/main."
    return True, 0, 0, "Up to date with origin/main."


def requirements_changed(old_commit: str, new_commit: str) -> bool:
    if not old_commit or not new_commit or old_commit == new_commit:
        return False
    result = _run_git("diff", "--name-only", old_commit, new_commit, "--", "requirements.txt")
    return result.returncode == 0 and bool(result.stdout.strip())


def update_code() -> tuple[bool, bool, str]:
    """Fast-forward local code only; never resets ignored runtime/config data."""
    status = _run_git("status", "--porcelain")
    if status.returncode != 0:
        return False, False, status.stderr.strip() or "Unable to inspect the Git working tree."
    tracked_changes = [line for line in status.stdout.splitlines() if line and not line.startswith("??")]
    if tracked_changes:
        return False, False, "Tracked local modifications detected; update aborted to avoid overwriting them."

    fetch = _run_git("fetch", "--quiet", "origin", "main")
    if fetch.returncode != 0:
        return False, False, fetch.stderr.strip() or "Unable to fetch origin/main."

    before = current_commit()
    compare = _run_git("rev-list", "--left-right", "--count", "HEAD...origin/main")
    if compare.returncode != 0:
        return False, False, compare.stderr.strip() or "Unable to compare local code with origin/main."
    parts = compare.stdout.strip().split()
    if len(parts) != 2:
        return False, False, "Unexpected Git comparison result."
    ahead, behind = int(parts[0]), int(parts[1])
    if behind == 0:
        return True, False, "No code updates available."
    if ahead != 0:
        return False, False, "Local branch has diverged from origin/main; automatic update aborted."

    pull = _run_git("merge", "--ff-only", "origin/main")
    if pull.returncode != 0:
        return False, False, pull.stderr.strip() or "Fast-forward update failed."
    after = current_commit()
    return True, after != before, f"Code updated from {before[:7]} to {after[:7]}."


def rollback_code(commit: str) -> tuple[bool, str]:
    """Rollback tracked source code to a known-good commit.

    Ignored runtime/configuration files such as .env and JSON stores are kept.
    """
    if not commit:
        return False, "No rollback commit is available."
    result = _run_git("reset", "--hard", commit)
    if result.returncode != 0:
        return False, result.stderr.strip() or "Unable to rollback source code."
    return True, f"Source code rolled back to {commit[:7]}."
