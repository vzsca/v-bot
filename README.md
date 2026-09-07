# 🤖 v-bot

Discord bot développé en **Python avec discord.py**, orienté modération, gestion de serveurs, annonces Twitch/YouTube et administration sécurisée.

v-bot inclut un **panel local** pour gérer le processus, le `.env`, les propriétaires, les logs et les fonctionnalités sensibles. Le projet est prévu pour Windows, Linux et macOS.

## ✨ Fonctionnalités

- 🛡️ Modération
- ℹ️ Commandes d'information
- 👑 Système de propriétaires permanents et temporaires
- 🔐 Kill Switch global
- 🧹 Snipe des messages supprimés
- 🌐 Gestion multi-serveurs
- ⚙️ Panel local
- 📋 Logs standards et de sécurité
- 📢 Annonces automatiques Twitch et YouTube
- 🔑 API principale globale + API configurées individuellement par serveur
- 🔒 Commandes sensibles désactivées par défaut
- 🧩 Architecture modulaire par Cogs

---

# 🚀 Installation

## Prérequis

- Windows, Linux ou macOS
- Python **3.13 recommandé**
- Un bot Discord créé depuis le Discord Developer Portal
- Les intents nécessaires activés

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

Commandes principales :

- `start`, `stop`, `restart`
- `status` — version, plateforme, Python, état `.env`, PID, processus, uptime, mémoire, CPU et owners
- `uptime`
- `logs`, `security_logs`, `servers`
- `set_token`
- `set_principal_owner`
- `add_secondary_owner`
- `set_prefix`
- `toggle_dangerous`
- `set_twitch_api`
- `set_youtube_api`

Le panel affiche l'owner principal et les owners secondaires avec le compteur `X/5`.

Les clés configurées depuis le panel correspondent à **l'API principale**, c'est-à-dire les credentials personnels de l'instance du bot. Elles sont écrites atomiquement dans `.env` et rechargées automatiquement pour Twitch/YouTube.

---

# 👑 Owners

Il existe **1 owner principal maximum** et **5 owners secondaires maximum**.

```env
OWNER_PRINCIPAL_ID=123456789
OWNERS_SECONDARY_IDS=111111111,222222222
```

Le panel refuse l'ajout d'un sixième owner secondaire et empêche les doublons ou l'ajout de l'owner principal comme secondaire.

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

Si aucune API valide n'est disponible pour la plateforme choisie, l'annonce ne peut pas être configurée correctement.

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

Les commandes `spam`, `dmall`, `raid` et `remove_raid` sont isolées dans `cogs/dangerous_safe.py` et désactivées par défaut.

```env
DANGEROUS_COMMANDS_ENABLED=false
```

---

# 🛡️ Sécurité

- Permissions centralisées dans `checks.py`
- Autorisations temporaires limitées au serveur et expirables
- Secrets jamais écrits dans les logs de sécurité
- `.env` et configurations persistantes écrites atomiquement
- Logs bornés et rotatifs
- Credentials API par serveur isolés par `guild_id`
- `api_credentials.json` exclu de Git
- Commandes sensibles séparées et désactivées par défaut

---

# 🧩 Architecture

Le projet utilise des Cogs pour séparer les responsabilités :

```text
v-bot/
├── main.py
├── panel.py
├── config.py
├── version.py
├── checks.py
├── state.py
├── security_log.py
├── integration_config.py
├── announcement_store.py
├── api_access.py
├── api_credentials.py
│
└── cogs/
    ├── events.py
    ├── moderation.py
    ├── info.py
    ├── owner.py
    ├── api_config.py
    ├── annonce.py
    ├── twitch.py
    ├── youtube.py
    ├── help_cog.py
    └── dangerous_safe.py
```

`main.py` reste volontairement limité au bootstrap, au logging et au chargement des extensions. La logique métier appartient aux modules et Cogs dédiés.

---

# 🏷️ Versioning

La version est centralisée dans `version.py` et dérivée de Git avec :

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

---

# 🔒 Fichiers privés

Ne jamais publier :

```text
.env
api_credentials.json
```

ou tout autre fichier contenant un token ou une clé API.

---

# 📌 Version actuelle

Le projet utilise désormais le versioning Git comme source de vérité.

---

# 📄 License

Personal project.
