"""
Dependency installation with clean output: only the package name and its
status (OK/FAILED), instead of pip/uv's verbose output (version resolution,
downloads, etc.).

Used by bootstrap.py (initial installation, called only once by
start_bot.bat) and by panel.py (the "update" command).
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIREMENTS_FILE = ROOT / "requirements.txt"


def _package_name(requirement_line: str) -> str:
    """Extracts only the package name from a requirements.txt line (without the version constraint)."""
    for sep in (">=", "==", "<=", "~=", "<", ">"):
        if sep in requirement_line:
            return requirement_line.split(sep)[0].strip()
    return requirement_line.strip()


def _has_uv() -> bool:
    return shutil.which("uv") is not None


def install_requirements(upgrade: bool = False) -> bool:
    """
    Installs each package from requirements.txt one by one, with a clear
    status for each line instead of the full pip/uv output. Returns True if
    everything succeeds, False otherwise (and displays the error from the
    failed package).
    """
    if not REQUIREMENTS_FILE.exists():
        print("[ERROR] requirements.txt not found.")
        return False

    requirements = [
        line.strip()
        for line in REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    use_uv = _has_uv()
    all_ok = True

    for requirement in requirements:
        name = _package_name(requirement)
        print(f"  - {name}...", end=" ", flush=True)

        cmd = ["uv", "pip", "install", "--python", sys.executable] if use_uv else [sys.executable, "-m", "pip", "install"]
        if upgrade:
            cmd.append("-U")
        cmd.append(requirement)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("OK")
        else:
            print("FAILED")
            print(result.stderr.strip()[-800:])
            all_ok = False

    return all_ok
