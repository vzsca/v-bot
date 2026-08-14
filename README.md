# v-bot

## Structure du projet

```
v-bot/
├── main.py            # Point d'entrée du BOT : crée le bot, charge les cogs, démarre la connexion
├── panel.py           # Panel de contrôle interactif (start/stop/restart/uptime/.env/...)
├── deps.py            # Installation des dépendances avec affichage propre (nom + statut)
├── bootstrap.py       # Première installation des dépendances, appelé une fois par start_bot.bat
├── config.py          # Chargement de la config (.env) : token, owners, limites, version
├── state.py           # État en mémoire centralisé (kill switch, snipe, owners temp, commandes en cours...)
├── checks.py          # Toute la logique de permission (owner permanent/temp, kill switch...)
├── exceptions.py      # Exceptions typées pour les checks (KillSwitchEnabled, NotPermanentOwner...)
├── views.py           # Composants UI (menu serveurs, boutons)
├── requirements.txt
├── start_bot.bat       # Prépare l'environnement (venv + install) puis lance panel.py
├── .env                # Token + IDs owner (NE JAMAIS PARTAGER CE FICHIER)
├── .env.example        # Modèle vide pour partager le projet sans données sensibles
└── cogs/
    ├── events.py        # on_ready, on_message (mention), on_message_delete (snipe), erreurs, tâche de fond
    ├── moderation.py    # mute, unmute, kick, ban, unban, give_role, lock, unlock, slowmode, clear
    ├── info.py          # user_info, server_info, avatar, snipe
    ├── owner.py         # servers, add_temp, owner_list, killswitch, toggle_guild, say
    ├── dangerous.py     # spam, dmall, raid, remove_raid (chargé seulement si DANGEROUS_COMMANDS_ENABLED=true)
    └── help_cog.py       # v!help
```

### Pourquoi panel.py plutôt que tout en .bat ?

Le `.bat` ne fait plus que créer le venv, installer les dépendances une fois, puis lancer `panel.py` — toute la logique (gérer le process du bot, éditer `.env`, calculer l'uptime...) vit en Python. Concrètement : pas de jonglage de guillemets/carets fragile, pas de relancer un process PowerShell à chaque commande (le panel reste en mémoire, donc `uptime` est instantané), et un vrai suivi de process via `psutil` au lieu de parser la sortie texte de `tasklist`/`taskkill`. L'interface (les commandes que tu tapes) reste strictement identique.

## Ce qui a changé par rapport au script original

- **Code éclaté en modules** : chaque thème (modération, info, owner, événements, aide) a son propre fichier, et les commandes sont organisées en `Cog` discord.py au lieu d'un seul script de 600+ lignes.
- **Permissions centralisées** (`checks.py`) : il n'y a plus de `if ctx.author.id not in AUTHORIZED_USER_ID` recopié à la main dans chaque commande (`servers`, `add_temp`, `killswitch`, `toggle_guild`, `raid`, `spam`, `dmall`...). Tout passe maintenant par une poignée de décorateurs réutilisables :
  - `checks.owner_check()` → owner permanent ou temporaire
  - `checks.permanent_owner_check()` → owner permanent uniquement
  - `checks.owner_or_permission(...)` → owner ou permission Discord précise
  - `checks.owner_or_guild_owner()` → owner ou propriétaire du serveur (utilisé par `spam`/`dmall`)
  - `checks.kill_switch_required()` → bloque si le kill switch est actif
- **IDs owner sortis du code source** : `OWNER_PRINCIPAL_ID` (1 seul ID) et `OWNERS_SECONDARY_IDS` (liste séparée par des virgules) vivent dans `.env`, pas dans `config.py`. Le `.env` est dans `.gitignore` : si tu partages ou versionnes le projet, ces IDs ne sont jamais exposés. `config.PERMANENT_OWNERS` reconstruit la liste complète (principal en premier) pour `owner_list`, qui affiche exactement comme avant.
- **État centralisé** (`state.py`) : `KILL_SWITCH`, `sniped_messages`, `temp_authorized_users`, `disabled_guilds`, `created_raid_channels/roles`, `running_commands` (protection anti-double-exécution) sont maintenant des attributs d'une seule instance `state`, au lieu de variables globales éparpillées.
- **Petites optimisations** :
  - IDs owner stockés dans un `frozenset` → vérification en O(1) au lieu d'un parcours de liste.
  - Le texte des intents (affiché quand on mentionne le bot) est calculé une seule fois et mis en cache, au lieu d'être reconstruit à chaque mention.
  - Suppression d'un appel `bot.fetch_user()` inutile dans `owner_list` (le résultat n'était jamais utilisé) — ça évite une requête HTTP superflue à chaque appel de la commande.
  - Les listeners (`on_message`, `on_message_delete`, `on_command_error`, `on_ready`) sont maintenant des listeners de Cog plutôt que des `@bot.event` : `process_commands` reste géré automatiquement par discord.py, sans code dupliqué.

⚠️ Une petite différence de comportement assumée par la centralisation : certains messages d'erreur "non autorisé" qui étaient légèrement différents d'une commande à l'autre (`"❌ Non autorisé."`, `"❌ Tu n'as pas la permission d'utiliser cette commande !"`, etc.) sont maintenant unifiés selon le type de check utilisé. Le comportement (qui peut faire quoi) reste identique.

## Commandes sensibles (raid, remove_raid, dmall, spam)

Isolées dans `cogs/dangerous.py`, qui n'est chargé par `main.py` **que si** `DANGEROUS_COMMANDS_ENABLED=true` dans `.env` (faux par défaut). Quand c'est désactivé, ces commandes n'existent tout simplement pas dans l'arbre de commandes du bot — pas juste bloquées par un check, vraiment absentes, impossibles à invoquer ou découvrir même en testant à l'aveugle.

Bascule via le panel `start_bot.bat`, commande `toggle_dangerous` :
- **Désactivation** : immédiate, pas de confirmation nécessaire (sens "sûr").
- **Activation** : demande de taper `ACTIVER` en majuscules pour confirmer, avec un rappel du risque (token/compte owner compromis = dégâts possibles).
- Dans les deux cas : nécessite un **redémarrage du bot** pour prendre effet (le choix des cogs à charger se fait une seule fois, au démarrage de `main.py` — pas de rechargement à chaud).

`v!help owner` affiche l'état actuel (🟢 ACTIVÉES / 🔴 DÉSACTIVÉES) et n'affiche les 4 commandes elles-mêmes que si elles sont actives.

### Journal de sécurité (security.log)

Fichier séparé de `bot.log`, dédié uniquement aux événements sensibles : bascule du kill switch, octroi d'un owner temporaire (`add_temp`), ajout d'un owner secondaire permanent, changement d'owner principal, activation/désactivation des commandes sensibles, changement de token (sans jamais logger sa valeur — seulement l'événement "token modifié"). Chaque ligne est horodatée avec l'auteur de l'action (`utilisateur (id)` côté bot, `panel` côté `.bat`).

Implémenté dans `security_log.py`, un module minimal sans dépendance au logger Python standard : comme `main.py` (le bot) et `panel.py` tournent dans deux process séparés, ils ne peuvent pas partager un objet logger — `security_log.log_security_event()` écrit directement dans le fichier, ce qui marche pareil des deux côtés.

Consultable via la commande `security_logs` du panel (affiche les 30 dernières lignes directement dans le terminal, pas besoin d'ouvrir Notepad).

### Exceptions personnalisées

`exceptions.py` définit des classes dédiées (`KillSwitchEnabled`, `NotPermanentOwner`, `NotOwnerOrTemp`, `NotOwnerOrGuildOwner`, `CommandAlreadyRunning`) au lieu de `commands.CheckFailure` générique avec un message en dur. Toutes restent des `CheckFailure` (donc `on_command_error` continue de fonctionner pour les cas génériques), mais permettent un traitement différencié sans avoir à analyser le texte du message : `on_command_error` loggue maintenant les refus de permission en warning (qui a tenté quoi), sans loguer les blocages routiniers (kill switch, commande déjà en cours).

### Centralisation complète des erreurs

`on_command_error` (dans `cogs/events.py`) couvre déjà toutes les erreurs de **commandes**. Mais discord.py a un cas spécial pour les erreurs qui se produisent ailleurs : une exception levée dans `on_message`, `on_guild_join`, ou n'importe quel autre event handler ne passe **pas** par `on_command_error`, et plus surprenant, ne passe même pas par le système normal de `@commands.Cog.listener()` non plus — `on_error` est appelé directement par discord.py en interne (`self.on_error(...)`), pas via `dispatch()`. Un `@commands.Cog.listener()` pour `on_error` ne se déclencherait donc jamais (vérifié dans le code source de discord.py).

`main.py` surcharge `bot.on_error` directement sur l'instance (sans avoir besoin de subclasser `commands.Bot`) pour combler ce trou : toute exception dans un event handler est maintenant capturée avec son traceback complet dans `bot.log`, exactement comme les erreurs de commandes. Testé avec un event handler cassé volontairement pour confirmer que le traceback complet remonte bien.

### Protection anti-double-exécution

`raid`, `remove_raid`, `dmall`, `spam` (dans `cogs/dangerous.py`) refusent désormais d'être lancées une deuxième fois sur le même serveur tant qu'une instance précédente n'est pas terminée — évite les salons/rôles dupliqués ou les DM envoyés deux fois si la commande est retapée trop vite ou lancée par deux owners en même temps. Implémenté via `cog_before_invoke`/`cog_after_invoke` (hooks natifs de discord.py, appelés respectivement avant et après chaque commande du cog, y compris en cas d'erreur). Le verrou est par `(commande, serveur)` : un `raid` sur un serveur n'empêche pas un `raid` sur un autre.

### `@commands.guild_only()`

Ajouté sur toutes les commandes qui touchent directement à un serveur (`ctx.guild.xxx`) et qui plantaient auparavant avec une erreur peu claire si invoquées en message privé : `mute`, `unmute`, `kick`, `ban`, `unban`, `give_role`, `lock`, `unlock`, `slowmode`, `clear`, `user_info`, `server_info`, `toggle_guild`, `raid`, `remove_raid`, `dmall`. Le message d'erreur par défaut de discord.py étant en anglais, `on_command_error` le remplace par `"❌ Cette commande ne peut pas être utilisée en message privé."`. Pas ajouté sur `avatar`/`snipe`/`say`/`spam` (fonctionnent légitimement sans serveur) ni sur les commandes du panel (`servers`, `add_temp`, `owner_list`, `killswitch`) qui n'en ont pas besoin.

### Vérifications de robustesse dans start_bot.bat

- **Version de Python** : le script essaie de créer le venv avec `py -3.13` en premier (recommandé), puis replie automatiquement sur `py -3` puis `python` si la tentative précédente échoue **réellement** (vérifié en regardant si `venv\Scripts\python.exe` existe vraiment après coup, pas juste en faisant confiance au code de sortie — le lanceur `py` de Windows peut garder une entrée enregistrée pour une version dont l'exécutable a été supprimé du disque, auquel cas un simple test préalable peut sembler réussir puis échouer à l'usage). Si aucune des trois tentatives n'aboutit, message clair avec la marche à suivre (`py -0p` pour lister les Python installés et leurs chemins réels, lien vers python.org pour réinstaller).
- **`bootstrap.py` et `panel.py`** : vérifiés avant d'être exécutés (`if not exist ...`), pour éviter un crash incompréhensible si l'un de ces fichiers a été déplacé ou supprimé par erreur.



## Gestion des owners

- **`v!owner_list`** est réservée aux owners permanents (principal + secondaires). Avant, n'importe qui pouvait l'utiliser.
- **Ajouter un owner secondaire** ne se fait pas par une commande Discord, mais via le panel `start_bot.bat` (commande `add_secondary_owner`, voir plus bas) : elle demande l'ID Discord du nouvel owner et l'ajoute à `OWNERS_SECONDARY_IDS` dans `.env`. Il faut ensuite taper `restart` pour que le bot recharge la config et en tienne compte (le bot ne lit `.env` qu'au démarrage).
- Pas de commande de suppression pour l'instant (retrait manuel de l'ID dans `.env` puis `restart`) — je peux ajouter une commande `remove_secondary_owner` côté `.bat` sur le même principe si besoin.

## Accélérer le démarrage

La création du venv + l'installation des dépendances ne se fait qu'**une seule fois** (grâce au marqueur `venv\.installed`) — les lancements suivants sautent direct au démarrage du bot. Si c'est lent à *chaque* lancement (pas juste le premier), c'est anormal, dis-le-moi.

Pour ce premier lancement (et pour `update`), deux pistes :

1. **[`uv`](https://docs.astral.sh/uv/)** — un remplaçant de `venv`/`pip` écrit en Rust, nettement plus rapide (création de venv quasi instantanée, installs parallélisés). Le script le détecte automatiquement (`where uv`) et l'utilise s'il est présent, sinon il retombe sur `venv`+`pip` comme avant — aucune installation requise pour profiter du script tel quel. Pour l'installer : `pip install uv`, ou voir [la doc officielle](https://docs.astral.sh/uv/getting-started/installation/).
2. **Exclusion Windows Defender** — la cause la plus fréquente d'une création de venv lente sous Windows est l'antivirus qui scanne chaque fichier copié en temps réel. Ajouter le dossier du projet aux exclusions de Windows Security (Protection contre les virus et menaces → Gérer les paramètres → Ajouter ou supprimer des exclusions) peut accélérer ça drastiquement. Je ne l'automatise pas dans le script car ça demande les droits administrateur.

## Configuration

1. Copie `.env.example` vers `.env` si tu repars de zéro (ici, `.env` est déjà pré-rempli avec les IDs trouvés dans ton script original — vérifie qu'ils sont corrects).
2. Renseigne `DISCORD_TOKEN` dans `.env`.
3. Vérifie/ajuste `OWNER_PRINCIPAL_ID` (ton ID, owner principal unique) et `OWNERS_SECONDARY_IDS` (liste optionnelle, séparée par des virgules).
4. `DANGEROUS_COMMANDS_ENABLED` reste à `false` par défaut (recommandé) — voir [Commandes sensibles](#commandes-sensibles-raid-remove_raid-dmall-spam) plus bas si besoin de les activer.

## Lancer le bot (Windows)

Double-clique sur `start_bot.bat`, ou en ligne de commande :

```
start_bot.bat
```

Le script crée un environnement virtuel (`venv`) avec Python 3.13, installe les dépendances une seule fois (marqueur `venv\.installed`, pas de réinstallation à chaque lancement — affichage propre, juste le nom de chaque paquet et son statut, pas le flot verbeux de pip/uv), puis lance `panel.py`, qui démarre le bot dans sa propre fenêtre et garde son PID en mémoire (plus de parsing de `tasklist`, suivi via `psutil`).

La fenêtre du `.bat` devient le panel de contrôle (en Python) qui reste ouvert. La liste complète des commandes ne s'affiche **que** via `help` (juste un rappel d'une ligne au tout premier lancement pour que la commande reste découvrable) :

| Commande  | Effet |
|-----------|-------|
| `start`   | démarre le bot s'il n'est pas déjà lancé |
| `stop`    | arrête le bot |
| `restart` | arrête puis relance le bot |
| `status`  | indique si le bot tourne actuellement |
| `uptime`  | depuis combien de temps il tourne, au format `Xh Ym Zs` (calcul instantané, plus de spawn PowerShell) |
| `update`  | met à jour les dépendances (même affichage propre que l'installation initiale) |
| `logs`    | ouvre `bot.log` dans Notepad |
| `security_logs` | affiche les 30 dernières lignes de `security.log` (kill switch, octroi d'owner, ...) directement dans le terminal |
| `servers` | liste les serveurs Discord sur lesquels le bot est présent (lu depuis `servers.txt`, écrit par le bot à la connexion) |
| `add_secondary_owner` | demande un ID Discord et l'ajoute à `OWNERS_SECONDARY_IDS` dans `.env` |
| `set_token` | définit ou change le `DISCORD_TOKEN` dans `.env` (fonctionne qu'il y en ait déjà un ou pas) |
| `set_principal_owner` | définit ou change l'`OWNER_PRINCIPAL_ID` dans `.env` (fonctionne qu'il y en ait déjà un ou pas) |
| `toggle_dangerous` | active/désactive raid, remove_raid, dmall, spam (confirmation requise pour activer) |
| `help`    | réaffiche la liste des commandes |
| `exit`    | ferme ce panel — le bot continue de tourner |

⚠️ Au démarrage, si `OWNER_PRINCIPAL_ID` **ou** `DISCORD_TOKEN` est vide/absent dans `.env`, le panel te demande directement de coller la valeur manquante et l'enregistre, **avant** de tenter de lancer le bot — il n'essaie plus de démarrer puis d'échouer.

La fenêtre s'ouvre en 120x25 caractères (plus large, moins haute que la version précédente). Pas de `chcp 65001` : tout le texte affiché est en ASCII simple, donc ça n'apportait aucun bénéfice visuel et ça forçait parfois un changement de police pas franchement esthétique sur la console Windows classique — retiré. Si la police par défaut de ta console ne te plaît toujours pas, le plus efficace reste d'ajuster ça depuis les propriétés de la fenêtre (clic droit sur la barre de titre → Propriétés → onglet Police), ou encore mieux, d'utiliser [Windows Terminal](https://apps.microsoft.com/detail/9n0dx20hk701) à la place de la console `cmd.exe` classique — bien plus confortable à lire et à personnaliser (zoom au Ctrl+molette, polices modernes comme Cascadia Code).

## Statut Discord

Le bot affiche sa version comme statut personnalisé Discord ("Version 3.7.4", sans verbe devant — via `discord.CustomActivity`, le même type de statut que celui qu'un humain définit manuellement), défini dans `on_ready` à partir de `config.VERSION`. À incrémenter manuellement dans `config.py` à chaque changement notable — pas de lien automatique avec git ou un quelconque système de versioning, c'est une simple constante texte.

## Message de ping

Quand on mentionne le bot (`@bot`), le message affiché dépend de qui demande :
- **Owner (permanent ou temporaire)** : embed détaillé avec statut admin, kill switch, intents activés.
- **Tout le monde d'autre** : message générique ("Salut, utilise `v!help`"), pour ne pas exposer ces infos opérationnelles à n'importe qui.

Le bot écrit ses logs à la fois dans la console et dans `bot.log` (à la racine du projet), pour que la commande `logs` ait quelque chose à ouvrir.

## Lancer le bot manuellement (autre OS)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
