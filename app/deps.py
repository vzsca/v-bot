"""Dependency installation helpers."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_FILE = ROOT / "requirements.txt"


def _has_uv() -> bool:
    return shutil.which("uv") is not None


def install_requirements(upgrade: bool = False) -> bool:
    """Install the complete requirements file in one resolver transaction."""
    if not REQUIREMENTS_FILE.exists():
        print("[ERROR] requirements.txt not found.")
        return False
    python = sys.executable
    if _has_uv():
        cmd = ["uv", "pip", "install", "--python", python, "-r", str(REQUIREMENTS_FILE)]
    else:
        cmd = [python, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
    if upgrade:
        cmd.insert(3 if _has_uv() else 4, "--upgrade")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print("[ERROR] Dependency installation failed.")
        print(result.stderr.strip()[-1500:])
        return False
    print("[OK] Dependencies installed.")
    return True
