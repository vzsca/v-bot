"""
Installation initiale des dépendances. Appelé une seule fois par
start_bot.bat (avant la création du marqueur venv\\.installed) ; les
lancements suivants sautent cette étape.
"""

import sys

from deps import install_requirements


def main():
    print("Installation des dependances :")
    ok = install_requirements(upgrade=False)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
