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
BOT_VERSION=3.8.2
OWNER_PRINCIPAL_ID=YOUR_DISCORD_ID
OWNERS_SECONDARY_IDS=
DANGEROUS_COMMANDS_ENABLED=false
TWITCH_CLIENT_ID=YOUR_CLIENT_ID
TWITCH_CLIENT_SECRET=YOUR_CLIENT_SECRET
YOUTUBE_API_KEY=YOUR_API_KEY
```

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

Le panel permet notamment de gérer :

- `start`, `stop`, `restart`, `status`, `uptime`
- `logs`, `security_logs`, `servers`
- `set_token`
- `set_principal_owner`
- `add_secondary_owner`
- `set_prefix`
- `toggle_dangerous`
- `set_twitch_api`
- `set_youtube_api`

Les clés configurées depuis le panel correspondent à **l'API principale**, c'est-à-dire les credentials personnels de l'instance du bot. Elles sont écrites atomiquement dans `.env` et rechargées automatiquement pour Twitch/YouTube.

---

# 🔑 Configuration des API par serveur

Un serveur autorisé dans `api_config_access.json` utilise automatiquement **l'API principale** définie dans `.env`.

Un serveur non autorisé utilise uniquement ses **propres credentials**, configurés depuis Discord.

### Twitch

```text
v!set_api twitch
```

Le bot affiche un bouton permettant d'ouvrir un formulaire privé pour renseigner :

- Twitch Client ID
- Twitch Client Secret

### YouTube

```text
v!set_api yt
```

Le formulaire permet de renseigner la YouTube API Key.

### Vérifier la configuration

```text
v!api_status
```

La commande affiche uniquement l'état des credentials, jamais leur contenu.

### Supprimer une configuration serveur

```text
v!clear_api twitch
v!clear_api yt
```

Les credentials par serveur sont stockés dans `api_credentials.json`, isolés par `guild_id`, avec écriture atomique. Ce fichier est ignoré par Git.

> ⚠️ Les secrets ne doivent jamais être envoyés directement dans un salon Discord. `v!set_api` utilise un formulaire privé pour éviter cette exposition.

---

# 📢 Annonces Twitch / YouTube

## Création

```text
v!create_annonce
```

Le bot demande successivement :

1. L'URL Twitch ou YouTube
2. Le message de l'annonce
3. Le salon Discord cible

L'annonce utilise automatiquement le bon compte API :

```text
Serveur autorisé
└── API principale (.env)

Serveur non autorisé
└── API du serveur (api_credentials.json)
```

Si aucune API valide n'est disponible pour le serveur et la plateforme choisie, la configuration ne peut pas être utilisée pour cette annonce.

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

Les annonces sont stockées dans `annonce_config.json` et isolées par serveur.

---

# 🛡️ Commandes principales

### Modération

```text
v!mute @member 10 raison
v!unmute @member
v!kick @member raison
v!ban @member raison
v!unban <id>
v!give_role @member @role
v!clear 50
v!slowmode 10
v!lock
v!unlock
```

### Information

```text
v!help
v!user_info
v!server_info
v!avatar
v!snipe
v!snipe 2
```

### Administration

```text
v!servers
v!add_temp @user 3600
v!owner_list
v!say message
v!embed <title> | <description>
v!killswitch on
v!killswitch off
```

Les permissions sont centralisées dans `checks.py`.

---

# ⚠️ Commandes sensibles

Le Cog `cogs/dangerous_safe.py` contient :

- `spam`
- `dmall`
- `raid`
- `remove_raid`

Ces commandes sont **désactivées par défaut**, chargées uniquement lorsque `DANGEROUS_COMMANDS_ENABLED=true`, et protégées par des limites et confirmations.

---

# 🛡️ Sécurité

- Permissions centralisées dans `checks.py`
- Autorisations temporaires limitées au serveur et automatiquement expirées
- Kill Switch global
- Secrets jamais affichés par les commandes de statut
- Credentials serveur isolés par `guild_id`
- `.env` et configurations persistantes écrits atomiquement
- `bot.log` et `security.log` avec rotation
- Fichiers secrets exclus de Git
- Les erreurs internes ne sont pas exposées aux utilisateurs Discord

---

# 📁 Structure

```text
v-bot/
├── main.py
├── panel.py
├── bootstrap.py
├── deps.py
├── config.py
├── checks.py
├── state.py
├── exceptions.py
├── security_log.py
├── integration_config.py
├── announcement_store.py
├── api_access.py
├── api_credentials.py
├── requirements.txt
├── .env.example
├── start_bot.bat
├── start_bot.sh
└── cogs/
    ├── events.py
    ├── moderation.py
    ├── info.py
    ├── owner.py
    ├── api_config.py
    ├── dangerous_safe.py
    ├── annonce.py
    ├── twitch.py
    ├── youtube.py
    └── help_cog.py
```

## Technologies

- Python 3.13
- discord.py
- python-dotenv
- aiohttp
- psutil
- pytest
- ruff

## Version

**3.8.2**

## Licence

Projet personnel. Toute utilisation, modification ou redistribution doit respecter les conditions définies par son propriétaire.
