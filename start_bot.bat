@echo off
mode con: cols=120 lines=25
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "PYTHONUTF8=1"

echo ============================
echo   Starting v-bot
echo ============================

where uv >nul 2>&1
if errorlevel 1 (
    set "USE_UV=0"
) else (
    set "USE_UV=1"
    echo uv detected: using it for faster startup.
)

REM --- Virtual environment creation, with automatic fallback if a Python
REM     installation detected by the launcher turns out to be broken
REM     (an outdated registry entry from the "py" launcher pointing to an
REM     .exe that no longer exists on disk - a simple "py -3.13 -c exit(0)"
REM     may succeed while actual usage fails afterward). We therefore check
REM     the result on disk after each attempt instead of relying on a single
REM     preliminary test. ---
set "VENV_OK=0"

if exist venv\Scripts\python.exe set "VENV_OK=1"

if "!VENV_OK!"=="0" if "!USE_UV!"=="1" (
    echo Creating virtual environment...
    if exist venv rmdir /s /q venv >nul 2>&1
    uv venv --python 3.13 venv >nul 2>&1
    if exist venv\Scripts\python.exe set "VENV_OK=1"
)

if "!VENV_OK!"=="0" (
    for %%P in ("py -3.13" "py -3" "python") do (
        if "!VENV_OK!"=="0" (
            if exist venv rmdir /s /q venv >nul 2>&1
            echo Creating virtual environment with %%P...
            %%~P -m venv venv >nul 2>&1
            if exist venv\Scripts\python.exe (
                set "VENV_OK=1"
                echo Virtual environment created successfully ^(%%P^).
            )
        )
    )
)

if "!VENV_OK!"=="0" (
    echo.
    echo [ERROR] Unable to create the virtual environment: no usable Python installation was found.
    echo v-bot requires Python 3.10 or newer ^(3.13 recommended^).
    echo.
    echo Possible checks:
    echo   1. Run "py -0p" in a command prompt to see the known Python versions and their paths.
    echo   2. If Python 3.13 appears with a path that no longer exists, reinstall it ^(or Repair^) :
    echo      https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if not exist venv\.installed (
    if not exist bootstrap.py (
        echo [ERROR] bootstrap.py not found. The file may have been moved or deleted.
        pause
        exit /b 1
    )

    venv\Scripts\python.exe bootstrap.py

    if errorlevel 1 (
        echo [ERROR] Unable to install dependencies.
        pause
        exit /b 1
    )

    echo ok > venv\.installed
)

if not exist panel.py (
    echo [ERROR] panel.py not found. The file may have been moved or deleted.
    pause
    exit /b 1
)

REM All panel logic (start/stop/restart/uptime/.env/...) is handled by
REM panel.py: this .bat only prepares the environment and launches it.
venv\Scripts\python.exe panel.py

pause
