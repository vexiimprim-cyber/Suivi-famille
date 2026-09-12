"""
Script client a executer SUR LE TELEPHONE ANDROID a suivre, via Termux.

Prerequis sur le telephone (une seule fois) :
  1. Installer l'app "Termux" (F-Droid, PAS le Play Store qui est obsolete).
  2. Installer l'app "Termux:API" (meme source).
  3. Dans Termux :
       pkg update && pkg install python termux-api -y
       pip install requests
  4. Desactiver l'optimisation de batterie pour Termux (Parametres > Batterie
     > Termux > Non restreint), sinon Android tue le script en arriere-plan.
  5. Autoriser la permission de localisation pour Termux:API.

Configuration : renseigner SERVER_URL et API_KEY ci-dessous (la cle API est
generee dans le tableau de bord quand on ajoute une personne suivie).

Lancement manuel :
  python client_android_termux.py

Lancement automatique au demarrage du telephone (optionnel) :
  - Installer l'app "Termux:Boot" (meme source que Termux).
  - Creer le fichier ~/.termux/boot/start-tracker.sh contenant :
        #!/data/data/com.termux/files/usr/bin/sh
        termux-wake-lock
        python /data/data/com.termux/files/home/client_android_termux.py
  - Rendre le fichier executable : chmod +x ~/.termux/boot/start-tracker.sh
"""

import json
import subprocess
import time
from datetime import datetime, timezone

import requests

SERVER_URL = "https://TON-SERVEUR.exemple.com/api/ping"
API_KEY = "COLLE_ICI_LA_CLE_API_DU_TABLEAU_DE_BORD"
INTERVAL_SECONDES = 60


def get_location():
    result = subprocess.run(
        ["termux-location", "-p", "gps", "-r", "once"],
        capture_output=True, text=True, timeout=30,
    )
    data = json.loads(result.stdout)
    return {
        "lat": data["latitude"],
        "lon": data["longitude"],
        "accuracy": data.get("accuracy"),
    }


def get_battery():
    try:
        result = subprocess.run(
            ["termux-battery-status"], capture_output=True, text=True, timeout=10,
        )
        data = json.loads(result.stdout)
        return data.get("percentage")
    except Exception:
        return None


def send_ping(location, battery):
    payload = {
        "api_key": API_KEY,
        "lat": location["lat"],
        "lon": location["lon"],
        "accuracy": location.get("accuracy"),
        "battery": battery,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    response = requests.post(SERVER_URL, json=payload, timeout=15)
    response.raise_for_status()


def main():
    print("Suivi demarre. Ctrl+C pour arreter.")
    while True:
        try:
            location = get_location()
            battery = get_battery()
            send_ping(location, battery)
            print(f"OK  lat={location['lat']} lon={location['lon']} batterie={battery}%")
        except Exception as exc:
            print(f"Erreur d'envoi : {exc}")
        time.sleep(INTERVAL_SECONDES)


if __name__ == "__main__":
    main()
