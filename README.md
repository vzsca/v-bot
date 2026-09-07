# 🤖 v-bot

Discord bot développé en **Python avec discord.py**, orienté modération, gestion de serveurs, annonces Twitch/YouTube et administration sécurisée.

v-bot inclut un **panel local** pour gérer le processus, la configuration, les propriétaires, les logs, les mises à jour et les fonctionnalités sensibles. Le projet est prévu pour Windows, Linux et macOS.

## ✨ Fonctionnalités

- 🛡️ Modération
- ℹ️ Commandes d'information
- 👑 Propriétaires permanents et autorisations temporaires
- 🔐 Kill Switch
- 🧹 Snipe des messages supprimés
- 🌐 Gestion multi-serveurs
- ⚙️ Panel local cross-platform
- 🔄 Mise à jour du code depuis Git avec redémarrage automatique
- 🧯 Rollback automatique en cas d'échec de dépendances ou de démarrage
- 📋 Logs standards et de sécurité
- 📢 Annonces automatiques Twitch et YouTube
- 🔑 API principale globale + API configurées individuellement par serveur
- 🔒 Commandes sensibles désactivées par défaut
- 🚦 Rate limiting, audit et détection anti-spam/anti-raid
- 🧩 Architecture modulaire par Cogs et modules applicatifs

---

# 🚀 Installation

## Prérequis

- Windows, Linux ou macOS
- Python **3.13 recommandé**
- Un bot Discord créé depuis le Discord Developer Portal
- Les intents nécessaires activés
- Git installé pour utiliser les mises à jour depuis le panel

```bash
git clone https://github.com/vzsca/v-bot.git
cd v-bot
```

Crée `.env` depuis `.env.example`, puis renseigne au minimum :

```env
DISCORD_TOKEN=YOUR_TOKEN
BOT_PREFIX=v!
OWNER_PRINCIPAL_ID=YOUR_DISCORD_ID
OWNERS_SECONDARY_IDS=
DANGEROUS_COMMANDS_ENABLED=false
TWITCH_CLIENT_ID=YOUR_CLIENT_ID
TWITCH_CLIENT_SECRET=YOUR_CLIENT_SECRET
YOUTUBE_API_KEY=YOUR_API_KEY
```

`BOT_VERSION` n'est plus une valeur à maintenir manuellement : la version applicative est dérivée des tags Git, avec un fallback pour les installations sans historique Git.

> 🔒 Ne publie jamais `.env`, le token Discord ou une clé API.

## ▶️ Lancement

### Windows

```text
start_bot.bat
```

### Linux / macOS

```bash
./start_bot.sh
```

Le launcher prépare l'environnement Python et démarre le panel local.

---

# 🖥️ Panel local

Le panel est interactif et fonctionne sous Windows, Linux et macOS.

### Processus

```text
start
stop
restart
status
uptime
logs
security_logs
servers
```

### Configuration

```text
set_token
set_principal_owner
add_secondary_owner
set_prefix
set_twitch_api
set_youtube_api
toggle_dangerous
```

### Mise à jour

```text
update
```

`update` :

1. vérifie d'abord si `origin/main` contient réellement de nouveaux commits ;
2. ne redémarre pas le bot lorsqu'il n'y a aucune mise à jour ;
3. arrête le bot uniquement lorsqu'une mise à jour est disponible ;
4. effectue un fast-forward Git sans écraser les modifications suivies localement ;
5. met à jour les dépendances uniquement si `requirements.txt` a changé ;
6. redémarre le bot avec le nouveau code ;
7. restaure automatiquement l'ancien commit si l'installation des dépendances échoue ou si le nouveau bot ne démarre pas.

Les fichiers de configuration et données runtime ignorés par Git restent en place pendant toute la procédure : `.env`, `api_credentials.json`, `annonce_config.json`, `api_config_access.json`, logs et fichiers PID/runtime.

Une branche locale divergente ou des modifications Git suivies localement bloquent l'update automatique afin d'éviter une écriture destructive.

### `status`

`status` affiche notamment :

- version et plateforme ;
- owner principal ;
- owners secondaires et compteur `X/5` ;
- état du bot, PID et processus ;
- uptime ;
- CPU/RAM ;
- état du dépôt Git et nombre de commits disponibles ;
- commit actuellement installé.

---

# 👑 Owners

Il existe **1 owner principal maximum** et **5 owners secondaires maximum**.

```env
OWNER_PRINCIPAL_ID=123456789
OWNERS_SECONDARY_IDS=111111111,222222222
```

Le panel refuse l'ajout d'un sixième owner secondaire et empêche les doublons ou l'ajout de l'owner principal comme secondaire.

Les autorisations temporaires sont limitées au serveur concerné et expirent automatiquement.

---

# 🔑 Configuration des API par serveur

Un serveur autorisé dans `api_config_access.json` utilise automatiquement **l'API principale** définie dans `.env`.

Un serveur non autorisé utilise uniquement ses **propres credentials**, configurés depuis Discord.

### Twitch

```text
v!set_api twitch
```

Le bot ouvre un formulaire privé pour renseigner le Twitch Client ID et le Twitch Client Secret.

### YouTube

```text
v!set_api yt
```

Le formulaire permet de renseigner la YouTube API Key.

### Vérifier

```text
v!api_status
```

La commande affiche le mode utilisé et l'état de configuration, sans révéler les secrets.

### Supprimer

```text
v!clear_api twitch
v!clear_api yt
```

Les credentials par serveur sont stockés dans `api_credentials.json`, isolés par `guild_id`, avec écriture atomique. Ce fichier est ignoré par Git.

> ⚠️ Les secrets ne doivent jamais être envoyés directement dans un salon Discord. `v!set_api` utilise un formulaire privé.

---

# 📢 Annonces Twitch / YouTube

## Création

```text
v!create_annonce
```

Le bot demande l'URL, le message et le salon cible. L'annonce utilise automatiquement l'API correspondant au serveur : API principale pour un serveur autorisé, credentials locaux pour un serveur non autorisé.

## Gestion

```text
v!annonces
v!test_annonce <id>
v!delete_annonce <id>
```

### Twitch placeholders

- `{streamer}` — nom Twitch
- `{title}` — titre du live
- `{game}` — catégorie
- `{url}` — URL du live

### YouTube placeholders

- `{channel}` — nom de la chaîne
- `{title}` — titre de la vidéo
- `{url}` — URL de la vidéo

---

# ⚠️ Commandes sensibles

Les commandes `spam`, `dmall`, `raid` et `remove_raid` sont isolées et désactivées par défaut.

```env
DANGEROUS_COMMANDS_ENABLED=false
```

Des limites de volume, confirmations et contrôles de permissions empêchent leur utilisation accidentelle.

---

# 🛡️ Sécurité

- Permissions centralisées dans `app/checks.py`
- Rate limiting global, par utilisateur et par commande
- Audit des actions et détection de rafales suspectes
- Détection anti-spam et anti-raid
- Autorisations temporaires limitées au serveur et expirables
- Secrets jamais écrits dans les logs de sécurité
- `.env` et configurations persistantes écrites atomiquement
- JSON corrompu refusé au lieu d'être remplacé silencieusement
- Logs bornés et rotatifs
- Credentials API par serveur isolés par `guild_id`
- `api_credentials.json` exclu de Git
- Commandes sensibles séparées et désactivées par défaut
- Mises à jour Git en fast-forward uniquement
- Rollback automatique du code en cas d'échec critique pendant une mise à jour

---

# 🧩 Architecture

```text
v-bot/
├── app/
│   ├── announcement_store.py
│   ├── api_access.py
│   ├── api_credentials.py
│   ├── audit.py
│   ├── checks.py
│   ├── config.py
│   ├── deps.py
│   ├── exceptions.py
│   ├── extensions.py
│   ├── integration_config.py
│   ├── metrics.py
│   ├── rate_limit.py
│   ├── safe_json.py
│   ├── security.py
│   ├── security_log.py
│   ├── state.py
│   ├── updater.py
│   └── version.py
├── cogs/
│   ├── events.py
│   ├── moderation.py
│   ├── info.py
│   ├── owner.py
│   ├── api_config.py
│   ├── annonce.py
│   ├── twitch.py
│   ├── youtube.py
│   ├── help_cog.py
│   └── dangerous_safe.py
├── tests/
├── main.py
├── panel.py
├── bootstrap.py
├── start_bot.bat
├── start_bot.sh
└── requirements.txt
```

`main.py` reste limité au bootstrap, au logging, aux checks globaux et au chargement des extensions. La logique métier appartient aux modules applicatifs et aux Cogs.

---

# 🏷️ Versioning

La version est dérivée de Git avec :

```text
git describe --tags --match v[0-9]* --always --dirty
```

Utiliser des tags de release comme :

```text
v3.8.2
v3.9.0
```

La version affichée par le bot et le panel suit ainsi Git au lieu de nécessiter plusieurs modifications manuelles.

---

# 🧰 Technologies

- Python 3.13
- discord.py
- python-dotenv
- psutil
- aiohttp
- pytest
- ruff
- Git

---

# 🔒 Fichiers privés / runtime

Ne jamais publier :

```text
.env
api_credentials.json
annonce_config.json
api_config_access.json
security.log
bot.log
```

ou tout autre fichier contenant un token ou une clé API.

---

# 📄 License

Personal project.
