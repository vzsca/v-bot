@echo off
mode con: cols=120 lines=25
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "PYTHONUTF8=1"

echo ============================
echo   Demarrage de v-bot
echo ============================

where uv >nul 2>&1
if errorlevel 1 (
    set "USE_UV=0"
) else (
    set "USE_UV=1"
    echo uv detecte : utilisation pour un demarrage plus rapide.
)

REM --- Creation du venv, avec repli automatique si un Python "detecte" par
REM     le lanceur s'avere en realite casse (entree registre obsolete du
REM     lanceur "py" qui pointe vers un .exe qui n'existe plus sur le disque -
REM     un simple "py -3.13 -c exit(0)" peut reussir alors que l'usage reel
REM     echoue ensuite). On verifie donc le resultat sur disque a chaque
REM     tentative plutot que de faire confiance a un seul test prealable. ---
set "VENV_OK=0"

if exist venv\Scripts\python.exe set "VENV_OK=1"

if "!VENV_OK!"=="0" if "!USE_UV!"=="1" (
    echo Creation de l'environnement virtuel...
    if exist venv rmdir /s /q venv >nul 2>&1
    uv venv --python 3.13 venv >nul 2>&1
    if exist venv\Scripts\python.exe set "VENV_OK=1"
)

if "!VENV_OK!"=="0" (
    for %%P in ("py -3.13" "py -3" "python") do (
        if "!VENV_OK!"=="0" (
            if exist venv rmdir /s /q venv >nul 2>&1
            echo Creation de l'environnement virtuel avec %%P...
            %%~P -m venv venv >nul 2>&1
            if exist venv\Scripts\python.exe (
                set "VENV_OK=1"
                echo Environnement virtuel cree avec succes ^(%%P^).
            )
        )
    )
)

if "!VENV_OK!"=="0" (
    echo.
    echo [ERREUR] Impossible de creer l'environnement virtuel : aucune installation Python utilisable n'a ete trouvee.
    echo v-bot a besoin de Python 3.10 ou plus recent ^(3.13 recommande^).
    echo.
    echo Verifications possibles :
    echo   1. Tape "py -0p" dans une invite de commande pour voir les versions Python connues et leurs chemins.
    echo   2. Si Python 3.13 apparait avec un chemin qui n'existe plus, reinstalle-le ^(ou Repair^) :
    echo      https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if not exist venv\.installed (
    if not exist bootstrap.py (
        echo [ERREUR] bootstrap.py introuvable. Le fichier a peut-etre ete deplace ou supprime.
        pause
        exit /b 1
    )

    venv\Scripts\python.exe bootstrap.py

    if errorlevel 1 (
        echo [ERREUR] Installation des dependances impossible.
        pause
        exit /b 1
    )

    echo ok > venv\.installed
)

if not exist panel.py (
    echo [ERREUR] panel.py introuvable. Le fichier a peut-etre ete deplace ou supprime.
    pause
    exit /b 1
)

REM Toute la logique du panel (start/stop/restart/uptime/.env/...) vit dans
REM panel.py : ce .bat ne fait que preparer l'environnement et le lancer.
venv\Scripts\python.exe panel.py

pause
