"""Initial dependency installation used by the launchers."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from deps import install_requirements


def main():
    print("Installing dependencies:")
    ok = install_requirements(upgrade=False)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
