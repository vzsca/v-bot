"""
Installation des dépendances avec un affichage propre : juste le nom du
paquet et son statut (OK/ECHEC), au lieu du flot verbeux de pip/uv (résolution
de versions, téléchargement, etc.).

Utilisé par bootstrap.py (toute première installation, appelée une seule fois
par start_bot.bat) et par panel.py (commande "update").
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIREMENTS_FILE = ROOT / "requirements.txt"


def _package_name(requirement_line: str) -> str:
    """Extrait juste le nom du paquet d'une ligne requirements.txt (sans la contrainte de version)."""
    for sep in (">=", "==", "<=", "~=", "<", ">"):
        if sep in requirement_line:
            return requirement_line.split(sep)[0].strip()
    return requirement_line.strip()


def _has_uv() -> bool:
    return shutil.which("uv") is not None


def install_requirements(upgrade: bool = False) -> bool:
    """
    Installe chaque paquet de requirements.txt un par un, avec un statut clair
    par ligne plutôt que la sortie complète de pip/uv. Retourne True si tout
    s'est bien passé, False sinon (et affiche l'erreur du paquet en échec).
    """
    if not REQUIREMENTS_FILE.exists():
        print("[ERREUR] requirements.txt introuvable.")
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
            print("ECHEC")
            print(result.stderr.strip()[-800:])
            all_ok = False

    return all_ok
