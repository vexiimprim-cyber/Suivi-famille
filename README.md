# Suivi Famille

Application de suivi de position en temps réel + historique des trajets sur une
carte, pensée pour un parent qui suit le téléphone de son enfant mineur (ou
toute personne ayant donné son accord explicite).

**⚠️ Cadre légal : n'utilise ceci que pour un enfant mineur sous ton autorité
parentale, ou avec le consentement explicite de la personne suivie. Suivre le
téléphone d'un tiers à son insu est illégal dans la plupart des pays.**

## Comment ça marche

```
[Téléphone enfant]  --envoie sa position toutes les X min-->  [Serveur Flask]  <--consulte-- [Toi, sur le tableau de bord web]
```

Il n'existe aucun moyen de localiser un téléphone à partir du seul numéro : le
téléphone suivi doit exécuter quelque chose qui envoie sa position GPS. C'est
le rôle du client Android (Termux) ou de l'automatisation iOS (Raccourcis)
décrits plus bas.

## 1. Lancer le serveur en local (test)

```bash
cd SuiviFamille
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
set ADMIN_PASSWORD=un-mot-de-passe-solide
set SECRET_KEY=une-chaine-aleatoire-longue
python app.py
```

Ouvre `http://localhost:5000`, connecte-toi avec `ADMIN_PASSWORD`, puis dans
"Ajouter une personne" crée une entrée (ex: "Téléphone de Léa") : une **clé
API** s'affiche, à copier dans le script client du téléphone suivi.

## 2. Déployer en ligne (nécessaire pour un suivi hors de ton Wi-Fi)

Le téléphone de l'enfant doit joindre le serveur en 4G/5G, donc le serveur ne
peut pas rester uniquement sur ton PC local (sauf via un tunnel type ngrok,
pratique pour tester mais pas pour du long terme).

Options simples, par ordre de facilité :

- **Render.com** (gratuit pour commencer) : pousse ce dossier sur un dépôt
  GitHub, crée un "Web Service" pointant dessus, build command
  `pip install -r requirements.txt`, start command `python app.py`, variables
  d'environnement `ADMIN_PASSWORD` et `SECRET_KEY`. HTTPS automatique.
  ⚠️ Le disque du plan gratuit est éphémère : l'historique (`suivi.db`) peut
  être remis à zéro à chaque redéploiement. Pour du vrai long terme, ajoute un
  "Persistent Disk" (payant) ou migre vers Postgres.
- **Railway.app** / **Fly.io** : similaire, avec volume persistant disponible.
- **PythonAnywhere** : plan gratuit avec stockage persistant, un peu plus
  manuel à configurer (WSGI).
- **VPS perso** (OVH, Hetzner...) : le plus robuste, mais demande de gérer
  soi-même HTTPS (ex: Caddy/Let's Encrypt) et le service systemd.

Une fois en ligne, remplace `SERVER_URL` dans les scripts clients par ton
adresse `https://...`.

## 3. Client Android (via Termux)

Voir les instructions détaillées en haut de
[client_android_termux.py](client_android_termux.py). Résumé :

1. Installer **Termux** et **Termux:API** (F-Droid, pas le Play Store).
2. `pkg install python termux-api -y && pip install requests`
3. Copier `client_android_termux.py` sur le téléphone, y renseigner
   `SERVER_URL` et `API_KEY`.
4. Désactiver l'optimisation de batterie pour Termux.
5. Lancer avec `python client_android_termux.py` (et optionnellement
   `Termux:Boot` pour un démarrage automatique au boot du téléphone).

## 4. Client iPhone (via l'app Raccourcis)

iOS ne permet pas de faire tourner du Python en arrière-plan, mais l'app
**Raccourcis** (Shortcuts) native peut envoyer la position périodiquement :

1. Créer un nouveau raccourci avec les actions :
   - **Obtenir la position actuelle**
   - **Obtenir les détails de [Position]** → Latitude, puis Longitude
   - **Texte** : construire un JSON, ex.
     `{"api_key":"TA_CLE","lat":LATITUDE,"lon":LONGITUDE}`
   - **Obtenir le contenu de l'URL** : méthode `POST`, URL de ton serveur
     `https://.../api/ping`, corps de requête `JSON` = le texte ci-dessus,
     en-tête `Content-Type: application/json`.
2. Dans l'app Raccourcis → onglet **Automatisation** → **Créer une
   automatisation personnelle** → déclencheur "Heure du jour" répété toutes
   les heures (ou plusieurs horaires), ou déclencheur "Je quitte/j'arrive à un
   lieu". Désactiver "Demander avant d'exécuter" pour que ça tourne sans
   confirmation.

C'est moins fréquent et moins fiable qu'Android (limitations d'Apple sur les
automatisations en tâche de fond), mais suffisant pour un suivi toutes les
30-60 minutes.

## 5. Sécurité

- Change absolument `ADMIN_PASSWORD` et `SECRET_KEY` (valeurs par défaut non
  sécurisées).
- Chaque personne suivie a sa propre clé API à usage unique : ne la partage
  pas, régénère-la (supprime puis recrée la personne) si tu penses qu'elle a
  fuité.
- Utilise toujours HTTPS en production (Render/Railway/Fly le fournissent
  automatiquement).

## Structure du projet

- `app.py` — serveur Flask (tableau de bord + API)
- `database.py` — accès SQLite (appareils + positions)
- `templates/` — pages web (connexion, tableau de bord avec carte Leaflet)
- `client_android_termux.py` — script à exécuter sur le téléphone Android suivi
- `suivi.db` — base de données créée automatiquement au premier lancement
