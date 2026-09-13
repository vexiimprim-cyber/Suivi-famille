#!/usr/bin/env bash
# Installe SadTalker (moteur de lip-sync) et ses poids pré-entraînés.
# À lancer une seule fois, depuis une machine avec accès à GitHub et
# HuggingFace (ce n'est PAS le cas de tous les environnements sandboxés).
set -euo pipefail

cd "$(dirname "$0")"

VENDOR_DIR="vendor/SadTalker"

if [ ! -d "$VENDOR_DIR/.git" ]; then
  echo "==> Clonage de SadTalker dans $VENDOR_DIR"
  git clone --depth 1 https://github.com/OpenTalker/SadTalker.git "$VENDOR_DIR"
else
  echo "==> SadTalker déjà cloné, mise à jour"
  git -C "$VENDOR_DIR" pull --ff-only
fi

echo "==> Installation des dépendances Python (SadTalker + app)"
pip install -r requirements.txt

echo "==> Téléchargement des modèles pré-entraînés (~2 Go, peut prendre du temps)"
pushd "$VENDOR_DIR" >/dev/null
bash scripts/download_models.sh
popd >/dev/null

echo "==> Terminé. Vérifie qu'ffmpeg est installé (obligatoire) :"
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "    ffmpeg est introuvable. Installe-le, ex. : sudo apt-get install -y ffmpeg"
else
  echo "    ffmpeg trouvé : $(command -v ffmpeg)"
fi

echo "==> Installation terminée. Lance 'python app.py' ou 'python cli.py --help'."
