# 🤖 v-bot

Bot Discord polyvalent développé en **Python avec discord.py**, pensé pour la modération, la gestion des serveurs et l'administration sécurisée du bot.

Le projet possède également un **panel de contrôle local** permettant de gérer le processus du bot, la configuration `.env`, les owners, les logs et les fonctionnalités sensibles.

---

## ✨ Fonctionnalités

* 🛡️ Modération complète
* ℹ️ Commandes d'information
* 👑 Système d'owners permanents et temporaires
* 🔐 Kill Switch global
* 🧹 Snipe des messages supprimés
* 🌐 Gestion de plusieurs serveurs
* ⚙️ Panel de contrôle local
* 📋 Logs classiques et logs de sécurité
* 🔒 Commandes sensibles désactivées par défaut
* 🔄 Gestion automatique du démarrage et de l'arrêt
* 🧩 Architecture modulaire avec des Cogs
* ⚡ Commandes préfixées et commandes slash/hybrides pour les commandes compatibles

---

# 📁 Structure du projet

```text
v-bot/
├── main.py                  # Point d'entrée du bot
├── panel.py                 # Panel de contrôle local
├── bootstrap.py             # Installation initiale
├── deps.py                  # Gestion des dépendances
├── config.py                # Configuration du bot
├── checks.py                # Système de permissions
├── state.py                 # État interne du bot
├── exceptions.py            # Exceptions personnalisées
├── security_log.py          # Journal de sécurité
│
├── start_bot.bat            # Lance le panel
├── requirements.txt         # Dépendances Python
├── .env                     # Configuration privée
├── .env.example             # Exemple de configuration
│
├── bot.log                  # Logs du bot
├── security.log             # Logs de sécurité
├── servers.txt              # Liste des serveurs
│
└── cogs/
    ├── events.py            # Événements Discord
    ├── moderation.py        # Modération
    ├── info.py              # Informations
    ├── owner.py             # Administration du bot
    ├── dangerous.py         # Commandes sensibles
    └── help_cog.py          # Système d'aide
```

> ⚠️ Le dossier `venv/` est généré localement et ne devrait pas être envoyé sur GitHub.

---

# 🚀 Installation

## Prérequis

* Windows **recommandé**
* Python **3.13 recommandé**
* Un bot Discord créé sur le [Discord Developer Portal](https://discord.com/developers/applications)
* Les intents nécessaires activés sur le bot Discord

Les dépendances sont installées automatiquement lors du premier lancement.

---

## 1. Cloner le projet

```bash
git clone https://github.com/vzsca/v-bot.git
cd v-bot
```

---

## 2. Configurer `.env`

Copiez `.env.example` vers `.env` :

```bash
copy .env.example .env
```

Puis configurez :

```env
DISCORD_TOKEN=VOTRE_TOKEN

BOT_NAME=v-bot
BOT_PREFIX=v!
BOT_VERSION=3.7.5

OWNER_PRINCIPAL_ID=VOTRE_ID_DISCORD
OWNERS_SECONDARY_IDS=

DANGEROUS_COMMANDS_ENABLED=false
```

### 🔑 Variables

| Variable                     | Description                                 |
| ---------------------------- | ------------------------------------------- |
| `DISCORD_TOKEN`              | Token du bot Discord                        |
| `BOT_NAME`                   | Nom du bot                                  |
| `BOT_PREFIX`                 | Préfixe des commandes                       |
| `BOT_VERSION`                | Version affichée par le bot                 |
| `OWNER_PRINCIPAL_ID`         | Owner principal                             |
| `OWNERS_SECONDARY_IDS`       | Owners secondaires séparés par des virgules |
| `DANGEROUS_COMMANDS_ENABLED` | Active ou non les commandes sensibles       |

> 🔒 **Ne partagez jamais votre `.env` ou votre token Discord.**

---

# ▶️ Lancement

Le lancement recommandé se fait avec :

```text
start_bot.bat
```
Lancer le bot manuellement :

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Le script :

1. Vérifie Python
2. Crée le `venv` si nécessaire
3. Installe les dépendances
4. Lance le panel
5. Le panel permet ensuite de démarrer le bot

---

# 🖥️ Panel de contrôle

Le panel affiche :

```text
v-bot>
```

Commandes disponibles :

| Commande              | Fonction                                       |
| --------------------- | ---------------------------------------------- |
| `start`               | Démarrer le bot                                |
| `stop`                | Arrêter le bot                                 |
| `restart`             | Redémarrer le bot                              |
| `status`              | Voir l'état du bot                             |
| `uptime`              | Voir depuis combien de temps le bot fonctionne |
| `update`              | Mettre à jour les dépendances                  |
| `logs`                | Ouvrir `bot.log`                               |
| `security_logs`       | Afficher les derniers événements de sécurité   |
| `servers`             | Afficher les serveurs du bot                   |
| `add_secondary_owner` | Ajouter un owner secondaire                    |
| `set_token`           | Modifier le token Discord                      |
| `set_principal_owner` | Modifier l'owner principal                     |
| `toggle_dangerous`    | Activer/désactiver les commandes sensibles     |
| `set_name`            | Modifier le nom du bot                         |
| `set_prefix`          | Modifier le préfixe                            |

Utilisez :

```text
help
```

pour afficher la liste directement dans le panel.

---

# 📜 Commandes Discord

Le préfixe par défaut est :

```text
v!
```

Vous pouvez le modifier depuis le panel avec :

```text
set_prefix
```

---

## 🛡️ Modération

### `v!mute`

Mute temporairement un membre.

```text
v!mute @membre 10 raison
```

### `v!unmute`

Retire le mute d'un membre.

```text
v!unmute @membre
```

### `v!kick`

Expulse un membre.

```text
v!kick @membre raison
```

### `v!ban`

Bannit un membre.

```text
v!ban @membre raison
```

### `v!unban`

Débannit un utilisateur avec son ID.

```text
v!unban 123456789012345678
```

### `v!give_role`

Donne un rôle à un membre.

```text
v!give_role @membre @role
```

### `v!lock`

Verrouille le salon actuel.

```text
v!lock
```

### `v!unlock`

Déverrouille le salon actuel.

```text
v!unlock
```

### `v!slowmode`

Configure le mode lent.

```text
v!slowmode 10
```

### `v!clear`

Supprime des messages.

```text
v!clear 50
```

Les commandes de modération vérifient les permissions Discord correspondantes ou les droits d'owner.

---

# ℹ️ Informations

### `v!help`

Affiche l'aide du bot.

```text
v!help
```

Des catégories peuvent également être utilisées.

```text
v!help owner
```

### `v!user_info`

Affiche les informations d'un membre.

```text
v!user_info @membre
```

### `v!server_info`

Affiche les informations du serveur.

```text
v!server_info
```

### `v!avatar`

Affiche l'avatar d'un utilisateur.

```text
v!avatar @membre
```

### `v!snipe`

Affiche un message récemment supprimé.

```text
v!snipe
```

Il est également possible de sélectionner un message précédent :

```text
v!snipe 2
```

---

# 👑 Système d'owners

v-bot possède plusieurs niveaux d'accès.

### Owner principal

Un seul owner principal est défini avec :

```env
OWNER_PRINCIPAL_ID=123456789
```

### Owners secondaires

Plusieurs owners secondaires peuvent être définis :

```env
OWNERS_SECONDARY_IDS=123456789,987654321
```

Ils sont ajoutés depuis le panel avec :

```text
add_secondary_owner
```

### Owners temporaires

Un owner permanent peut temporairement donner des permissions à un utilisateur :

```text
v!add_temp @utilisateur 3600
```

Ici, l'autorisation dure **3600 secondes**.

### Liste des owners

```text
v!owner_list
```

Affiche les owners permanents et temporaires.

---

# 🔐 Kill Switch

Le bot possède un système de **Kill Switch** permettant de bloquer les commandes protégées.

Vérifier son état :

```text
v!killswitch
```

Activer :

```text
v!killswitch on
```

Désactiver :

```text
v!killswitch off
```

Le Kill Switch est particulièrement utile en cas de problème de sécurité ou de comportement inattendu du bot.

---

# 🌐 Gestion des serveurs

Les owners peuvent utiliser :

```text
v!servers
```

pour accéder au panneau de gestion des serveurs.

Le panel local possède également :

```text
servers
```

qui affiche la liste des serveurs auxquels le bot est connecté.

La liste est enregistrée automatiquement dans :

```text
servers.txt
```

---

# 🗣️ Commande `say`

Les owners peuvent faire envoyer un message par le bot :

```text
v!say Bonjour tout le monde !
```

Le message contenant la commande est ensuite supprimé.

---

# ⚠️ Commandes sensibles

Les commandes suivantes sont volontairement séparées dans :

```text
cogs/dangerous.py
```

* `spam`
* `dmall`
* `raid`
* `remove_raid`

Elles sont **désactivées par défaut**.

```env
DANGEROUS_COMMANDS_ENABLED=false
```

Lorsqu'elles sont désactivées, le Cog `dangerous` n'est même pas chargé par le bot.

---

## Activation

Depuis le panel :

```text
toggle_dangerous
```

Le panel demande une confirmation explicite :

```text
ACTIVER
```

Après activation, un redémarrage est nécessaire :

```text
restart
```

---

## `v!spam`

Permet l'envoi contrôlé de plusieurs messages.

```text
v!spam <nombre> <message>
```

La quantité maximale est limitée par la configuration du bot.

---

## `v!dmall`

Envoie un message privé aux membres du serveur.

```text
v!dmall <message>
```

Cette commande est protégée et doit être utilisée avec précaution.

---

## `v!raid`

Fonction de test contrôlée créant des salons et rôles temporaires.

```text
v!raid 10
```

Les éléments créés sont enregistrés afin de pouvoir être supprimés avec :

```text
v!remove_raid
```

---

# 🛡️ Sécurité

v-bot possède plusieurs protections.

### Permissions centralisées

Les permissions sont gérées dans :

```text
checks.py
```

avec différents niveaux :

* Owner permanent
* Owner permanent ou temporaire
* Owner ou propriétaire du serveur
* Owner ou permission Discord spécifique
* Kill Switch

---

### Protection anti-double-exécution

Les commandes sensibles ne peuvent pas être exécutées plusieurs fois simultanément sur le même serveur.

Cela évite notamment :

* créations multiples de salons/rôles ;
* doubles opérations ;
* exécutions simultanées accidentelles.

---

### Logs de sécurité

Les actions sensibles sont enregistrées dans :

```text
security.log
```

Exemples :

* changement de token ;
* changement d'owner principal ;
* ajout d'un owner secondaire ;
* ajout d'un owner temporaire ;
* activation/désactivation des commandes sensibles ;
* activation/désactivation du Kill Switch.

Le token lui-même n'est **jamais écrit dans les logs**.

---

# 📝 Logs

## `bot.log`

Contient les événements et erreurs du bot.

Depuis le panel :

```text
logs
```

ouvre directement le fichier.

## `security.log`

Contient uniquement les événements sensibles.

Depuis le panel :

```text
security_logs
```

affiche les dernières entrées.

---

# ⚙️ Architecture

Le bot est organisé en plusieurs **Cogs** afin de garder le projet modulaire.

### `cogs/moderation.py`

Toutes les commandes de modération.

### `cogs/info.py`

Commandes d'informations et système de snipe.

### `cogs/owner.py`

Administration du bot et gestion des owners.

### `cogs/events.py`

Gestion des événements Discord :

* connexion ;
* arrivée/départ de serveur ;
* mentions du bot ;
* messages supprimés ;
* erreurs ;
* nettoyage des owners temporaires.

### `cogs/dangerous.py`

Commandes sensibles, chargées uniquement lorsqu'elles sont activées.

### `cogs/help_cog.py`

Système d'aide.

---

# 🔧 Configuration Discord

Le bot utilise notamment les intents :

```text
guilds
members
messages
message_content
reactions
```

Les intents nécessaires doivent être activés dans le **Discord Developer Portal**.

Le bot synchronise également ses commandes lors de sa connexion à Discord.

---

# 🧰 Technologies

* **Python 3.13**
* **discord.py**
* **python-dotenv**
* **psutil**
* **asyncio**
* **Windows Batch**

---

# 🔒 Fichiers à ne jamais publier

Ne publiez jamais :

```text
.env
```

ou un fichier contenant votre token Discord.

Le projet utilise `.env.example` pour fournir uniquement le modèle de configuration.

---

# 📌 Version

Version actuelle :

```text
3.7.5
```

---

# 📄 Licence

Projet personnel.

Toute utilisation, modification ou redistribution du projet doit respecter les conditions définies par son propriétaire.
