import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
for path in (ROOT, APP_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
