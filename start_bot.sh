#!/bin/bash

# ============================================================
# v-bot Launcher
# Linux / macOS
# Starts the Discord bot and the local web panel.
# ============================================================

set -e

cd "$(dirname "$0")"

echo "==================================="
echo "          v-bot Launcher"
echo "==================================="
echo

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

if [ ! -d "venv" ]; then
    echo
    echo "[INFO] Creating virtual environment..."
    "$PYTHON" -m venv venv
    echo "[OK] Virtual environment created."
fi

VENV_PYTHON="venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] Virtual environment Python executable was not found."
    exit 1
fi

echo
echo "[INFO] Checking dependencies..."
if [ ! -f "venv/.installed" ]; then
    if [ ! -f "bootstrap.py" ]; then
        echo "[ERROR] bootstrap.py was not found."
        exit 1
    fi
    "$VENV_PYTHON" bootstrap.py
    touch venv/.installed
else
    echo "[OK] Dependencies already installed."
fi

if [ ! -f "main.py" ]; then
    echo "[ERROR] main.py was not found."
    exit 1
fi

if [ ! -f "panel_web/server.py" ]; then
    echo "[ERROR] Web panel server was not found."
    exit 1
fi

echo
echo "[INFO] Starting web panel..."
"$VENV_PYTHON" -m panel_web.server &
WEB_PANEL_PID=$!

cleanup() {
    echo
    echo "[INFO] Stopping web panel..."
    kill "$WEB_PANEL_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 1

echo "[INFO] Starting v-bot..."
echo
exec "$VENV_PYTHON" main.py
