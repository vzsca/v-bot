"""
Panel de contrôle interactif pour v-bot.
"""

import os
import subprocess
import time
from pathlib import Path

import psutil

import security_log
from deps import install_requirements

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
BOT_PID_FILE = ROOT / "bot.pid"
BOT_START_FILE = ROOT / "bot.start"
SERVERS_FILE = ROOT / "servers.txt"
LOG_FILE = ROOT / "bot.log"
SECURITY_LOG_FILE = ROOT / "security.log"
PYTHON_EXE = ROOT / "venv" / "Scripts" / "python.exe"


# --- Utilitaires .env ---

def _read_env_lines() -> list[str]:
    if not ENV_PATH.exists():
        return []
    return ENV_PATH.read_text(encoding="utf-8").splitlines()


def _write_env_lines(lines: list[str]) -> None:
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_env_value(key: str) -> str:
    prefix = f"{key}="
    for line in _read_env_lines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def set_env_value(key: str, value: str) -> None:
    lines = _read_env_lines()
    prefix = f"{key}="
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = f"{key}={value}"
            _write_env_lines(lines)
            return
    lines.append(f"{key}={value}")
    _write_env_lines(lines)


# --- Process du bot ---

def _get_bot_pid() -> int | None:
    if not BOT_PID_FILE.exists():
        return None
    try:
        pid = int(BOT_PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None
    if psutil.pid_exists(pid):
        return pid
    _clear_pid_files()  # PID périmé (le process a crashé/été fermé autrement)
    return None


def _clear_pid_files() -> None:
    BOT_PID_FILE.unlink(missing_ok=True)
    BOT_START_FILE.unlink(missing_ok=True)


def is_running() -> bool:
    return _get_bot_pid() is not None


def cmd_start() -> None:
    if is_running():
        print("Le bot tourne deja.")
        return

    print("Demarrage du bot...")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"  # encodage robuste cote bot, independant du chcp de la console

    process = subprocess.Popen(
        [str(PYTHON_EXE), "main.py"],
        cwd=str(ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        env=env,
    )

    BOT_PID_FILE.write_text(str(process.pid), encoding="utf-8")
    BOT_START_FILE.write_text(str(int(time.time())), encoding="utf-8")

    time.sleep(2)

    if is_running():
        print("Bot demarre.")
    else:
        print('Echec du demarrage. Tape "logs" pour voir pourquoi.')


def cmd_stop() -> None:
    pid = _get_bot_pid()
    if pid is None:
        print("Le bot n'est pas demarre.")
        return

    try:
        proc = psutil.Process(pid)
        for child in proc.children(recursive=True):
            child.kill()
        proc.kill()
    except psutil.NoSuchProcess:
        pass

    _clear_pid_files()
    print("Bot arrete.")


def cmd_restart() -> None:
    cmd_stop()
    time.sleep(2)
    cmd_start()


def cmd_status() -> None:
    print("Bot actif." if is_running() else "Bot inactif.")


def cmd_uptime() -> None:
    if not BOT_START_FILE.exists():
        print("Uptime inconnu.")
        return
    try:
        start_epoch = int(BOT_START_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        print("Uptime inconnu.")
        return

    elapsed = int(time.time()) - start_epoch
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"Le bot tourne depuis {hours}h {minutes}m {seconds}s.")


def cmd_update() -> None:
    print("Mise a jour des dependances :")
    install_requirements(upgrade=True)
    print("Mise a jour terminee.")


def cmd_logs() -> None:
    if not LOG_FILE.exists():
        print("bot.log n'existe pas encore.")
        return
    subprocess.Popen(["notepad.exe", str(LOG_FILE)])


def cmd_security_logs() -> None:
    if not SECURITY_LOG_FILE.exists():
        print("security.log n'existe pas encore (aucun evenement sensible enregistre).")
        return

    lines = SECURITY_LOG_FILE.read_text(encoding="utf-8").splitlines()
    last_lines = lines[-30:]

    print()
    print(f"--- security.log (dernieres {len(last_lines)} entrees sur {len(lines)}) ---")
    for line in last_lines:
        print(line)


def cmd_servers() -> None:
    if not SERVERS_FILE.exists():
        print("Liste indisponible : le bot n'a pas encore termine de se connecter.")
        return
    print()
    print(SERVERS_FILE.read_text(encoding="utf-8"))


def cmd_add_secondary_owner() -> None:
    new_id = input("ID Discord du nouvel owner secondaire : ").strip()

    if not new_id:
        print("[ERREUR] Aucun ID saisi.")
        return
    if not new_id.isdigit():
        print("[ERREUR] L'ID doit etre uniquement compose de chiffres.")
        return

    current = get_env_value("OWNERS_SECONDARY_IDS")
    existing_ids = [x for x in current.split(",") if x]

    if new_id in existing_ids:
        print("Cet ID est deja owner secondaire dans .env.")
        return

    existing_ids.append(new_id)
    set_env_value("OWNERS_SECONDARY_IDS", ",".join(existing_ids))
    security_log.log_security_event(f"Owner secondaire permanent ajoute : {new_id}", actor="panel")
    print(f"Owner secondaire {new_id} ajoute dans .env.")
    print("Le changement sera pris en compte au (re)demarrage du bot.")


def cmd_set_token() -> None:
    new_token = input("Nouveau token Discord : ").strip()

    if not new_token:
        print("[ERREUR] Aucun token saisi, rien n'a ete modifie.")
        return

    set_env_value("DISCORD_TOKEN", new_token)
    # On ne logue jamais la valeur du token, seulement le fait qu'il a change.
    security_log.log_security_event("Token Discord modifie", actor="panel")
    print("Token enregistre dans .env.")
    print("Le changement sera pris en compte au (re)demarrage du bot.")


def cmd_set_principal_owner() -> None:
    new_id = input("Colle l'ID Discord du proprietaire principal : ").strip()

    if not new_id:
        print("[ERREUR] Aucun ID saisi, rien n'a ete modifie.")
        return
    if not new_id.isdigit():
        print("[ERREUR] L'ID doit etre uniquement compose de chiffres, rien n'a ete modifie.")
        return

    set_env_value("OWNER_PRINCIPAL_ID", new_id)
    security_log.log_security_event(f"Owner principal defini : {new_id}", actor="panel")
    print("Owner principal enregistre dans .env.")
    print("Le changement sera pris en compte au (re)demarrage du bot.")


def _dangerous_commands_enabled() -> bool:
    return get_env_value("DANGEROUS_COMMANDS_ENABLED").strip().lower() in ("1", "true", "on", "yes")


def cmd_toggle_dangerous() -> None:
    """
    Active/desactive raid, remove_raid, dmall, spam. Quand c'est desactive
    (par defaut), ces commandes ne sont meme pas chargees dans le bot - pas
    juste bloquees, absentes de l'arbre de commandes. Necessite un
    redemarrage du bot pour prendre effet (le choix des cogs a charger se
    fait une seule fois, au demarrage de main.py).
    """
    if _dangerous_commands_enabled():
        set_env_value("DANGEROUS_COMMANDS_ENABLED", "false")
        security_log.log_security_event("Commandes sensibles DESACTIVEES (raid/remove_raid/dmall/spam)", actor="panel")
        print("Commandes sensibles (raid, remove_raid, dmall, spam) DESACTIVEES.")
        print("Le changement sera pris en compte au (re)demarrage du bot.")
        return

    print()
    print("Tu es sur le point d'ACTIVER les commandes sensibles : raid, remove_raid, dmall, spam.")
    print("Ce sont des commandes qui peuvent faire des degats serieux si le token ou un compte owner est compromis.")
    confirm = input('Tape ACTIVER (en majuscules) pour confirmer, ou autre chose pour annuler : ').strip()

    if confirm != "ACTIVER":
        print("Annule, rien n'a ete modifie.")
        return

    set_env_value("DANGEROUS_COMMANDS_ENABLED", "true")
    security_log.log_security_event("Commandes sensibles ACTIVEES (raid/remove_raid/dmall/spam)", actor="panel")
    print("Commandes sensibles ACTIVEES.")
    print("Le changement sera pris en compte au (re)demarrage du bot.")

def cmd_set_name() -> None:
    new_name = input("Nouveau nom du bot : ").strip()

    if not new_name:
        print("[ERREUR] Aucun nom saisi, rien n'a ete modifie.")
        return

    if len(new_name) > 32:
        print("[ERREUR] Le nom du bot ne peut pas depasser 32 caracteres.")
        return

    set_env_value("BOT_NAME", new_name)
    security_log.log_security_event(
        f"Nom du bot modifie : {new_name}",
        actor="panel",
    )

    print(f"Nom du bot enregistre dans .env : {new_name}")
    print("Le changement sera pris en compte au prochain redemarrage du bot.")

def cmd_set_prefix() -> None:
    new_prefix = input("Nouveau prefix : ").strip()

    if not new_prefix:
        print("[ERREUR] Aucun prefix saisi, rien n'a ete modifie.")
        return

    if len(new_prefix) > 10:
        print("[ERREUR] Le prefix ne peut pas depasser 10 caracteres.")
        return

    if any(char.isspace() for char in new_prefix):
        print("[ERREUR] Le prefix ne peut pas contenir d'espaces.")
        return

    set_env_value("BOT_PREFIX", new_prefix)
    security_log.log_security_event(
        f"Prefix du bot modifie : {new_prefix}",
        actor="panel",
    )

    print(f"Prefix enregistre dans .env : {new_prefix}")
    print("Le changement sera pris en compte au prochain redemarrage du bot.")


COMMANDS = [
    ("start", "demarrer le bot", cmd_start),
    ("stop", "arreter le bot", cmd_stop),
    ("restart", "redemarrer le bot", cmd_restart),
    ("status", "etat actuel du bot", cmd_status),
    ("uptime", "depuis combien de temps il tourne", cmd_uptime),
    ("update", "mettre a jour les dependances", cmd_update),
    ("logs", "ouvrir bot.log", cmd_logs),
    ("security_logs", "afficher security.log (kill switch, octroi d'owner, ...)", cmd_security_logs),
    ("servers", "lister les serveurs sur lesquels le bot est present", cmd_servers),
    ("add_secondary_owner", "ajouter un owner secondaire permanent dans .env", cmd_add_secondary_owner),
    ("set_token", "definir ou changer le token Discord dans .env", cmd_set_token),
    ("set_principal_owner", "definir ou changer l'owner principal dans .env", cmd_set_principal_owner),
    ("toggle_dangerous", "activer/desactiver raid, remove_raid, dmall, spam", cmd_toggle_dangerous),
    ("set_name", "definir ou changer le nom du bot dans .env", cmd_set_name),
    ("set_prefix", "definir ou changer le prefix dans .env", cmd_set_prefix),
]

COMMAND_MAP = {name: func for name, _, func in COMMANDS}


def cmd_help() -> None:
    print()
    print("===== v-bot =====")
    print()
    width = max(len(name) for name, _, _ in COMMANDS) + 2
    for name, desc, _ in COMMANDS:
        print(f"{name.ljust(width)}- {desc}")
    print(f"{'help'.ljust(width)}- reafficher cette liste")
    print(f"{'exit'.ljust(width)}- fermer ce panel (le bot continue de tourner)")
    print()


# --- Checks de démarrage (bloquants) ---

def check_principal_owner() -> None:
    if get_env_value("OWNER_PRINCIPAL_ID"):
        return
    print()
    print("Aucun owner principal n'est defini dans .env (OWNER_PRINCIPAL_ID).")
    print("Le bot ne pourra pas demarrer sans ca.")
    cmd_set_principal_owner()


def check_token() -> None:
    if get_env_value("DISCORD_TOKEN"):
        return
    print()
    print("Aucun token Discord n'est defini dans .env (DISCORD_TOKEN).")
    print("Le bot ne pourra pas se connecter sans ca.")
    cmd_set_token()


def main() -> None:
    if not ENV_PATH.exists():
        print()
        print("[ATTENTION] Fichier .env introuvable. Le bot va echouer au demarrage.")
        print()
    else:
        check_principal_owner()
        check_token()

    cmd_start()
    print('Tape "help" pour la liste des commandes du panel.')

    while True:
        print()
        try:
            cmd = input("v-bot> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if cmd == "exit":
            break
        elif cmd == "help":
            cmd_help()
        elif cmd in COMMAND_MAP:
            COMMAND_MAP[cmd]()
        elif cmd:
            print(f'Commande inconnue "{cmd}". Tape "help" pour la liste.')


if __name__ == "__main__":
    main()
