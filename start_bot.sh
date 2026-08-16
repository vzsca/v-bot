#!/bin/bash

# ============================================================
# v-bot Launcher
# Compatible with Linux and macOS
# ============================================================

set -e

# Move to the directory containing this script
cd "$(dirname "$0")"

echo "==================================="
echo "          v-bot Launcher"
echo "==================================="
echo

# ------------------------------------------------------------
# Check Python
# ------------------------------------------------------------

if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "[ERROR] Python 3 was not found."
    echo "Please install Python 3.13 or a compatible version."
    exit 1
fi

echo "[OK] Python found: $($PYTHON --version)"

# ------------------------------------------------------------
# Check / create virtual environment
# ------------------------------------------------------------

if [ ! -d "venv" ]; then
    echo
    echo "[INFO] Virtual environment not found."
    echo "[INFO] Creating virtual environment..."

    "$PYTHON" -m venv venv

    echo "[OK] Virtual environment created."
fi

VENV_PYTHON="venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] Virtual environment Python executable was not found."
    exit 1
fi

# ------------------------------------------------------------
# Upgrade pip
# ------------------------------------------------------------

echo
echo "[INFO] Checking pip..."

"$VENV_PYTHON" -m pip install --upgrade pip

# ------------------------------------------------------------
# Install dependencies
# ------------------------------------------------------------

if [ -f "requirements.txt" ]; then
    echo
    echo "[INFO] Installing dependencies..."

    "$VENV_PYTHON" -m pip install -r requirements.txt

    echo "[OK] Dependencies installed."
else
    echo
    echo "[WARNING] requirements.txt was not found."
fi

# ------------------------------------------------------------
# Launch panel
# ------------------------------------------------------------

echo
echo "[INFO] Starting v-bot control panel..."
echo

exec "$VENV_PYTHON" panel.py
