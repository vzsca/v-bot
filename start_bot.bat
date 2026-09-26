@echo off
mode con: cols=100 lines=30
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "PYTHONUTF8=1"

echo ============================================
echo              v-bot Launcher
echo ============================================
echo.

where uv >nul 2>&1
if errorlevel 1 (
    set "USE_UV=0"
) else (
    set "USE_UV=1"
    echo uv detected: using it for faster startup.
)

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
    echo [ERROR] Unable to create the virtual environment.
    echo v-bot requires Python 3.10 or newer ^(3.13 recommended^).
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if not exist venv\.installed (
    if not exist bootstrap.py (
        echo [ERROR] bootstrap.py not found.
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

if not exist main.py (
    echo [ERROR] main.py not found.
    pause
    exit /b 1
)

if not exist panel_web\server.py (
    echo [ERROR] Web panel server not found.
    pause
    exit /b 1
)

echo.
echo [INFO] Starting web panel...
start "v-bot Web Panel" cmd /k "cd /d ""%~dp0"" && venv\Scripts\python.exe -m panel_web.server"

timeout /t 1 /nobreak >nul

echo [INFO] Starting v-bot...
echo.

venv\Scripts\python.exe main.py

echo.
echo v-bot has stopped.
pause
