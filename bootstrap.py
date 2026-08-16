"""
Initial dependency installation. Called once by start_bot.bat (before the
venv\\.installed marker is created); subsequent launches skip this step.
"""

import sys

from deps import install_requirements


def main():
    print("Installing dependencies:")
    ok = install_requirements(upgrade=False)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
