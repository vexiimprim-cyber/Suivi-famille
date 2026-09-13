# Lip Sync App

Anime une photo (portrait) à partir d'un enregistrement audio de ta voix :
mouvements de bouche, légers mouvements de tête et clignements d'yeux
générés automatiquement pour un rendu le plus réaliste possible.

Le moteur utilisé est **[SadTalker](https://github.com/OpenTalker/SadTalker)**
(licence Apache 2.0 pour le code ; les poids pré-entraînés sont fournis par
les auteurs à des fins de recherche — voir leur dépôt pour le détail des
conditions d'usage). Ce projet ne réimplémente pas le modèle : il l'installe
comme dépendance externe (`vendor/SadTalker`) et fournit une appli web +
CLI par-dessus pour l'utiliser facilement.

## ⚠️ Utilisation responsable

Cette technologie peut faire dire n'importe quoi à n'importe quel visage.
- N'utilise cette application qu'avec **ta propre photo et ta propre voix**,
  ou avec le **consentement explicite et informé** de la personne dont tu
  utilises l'image/la voix.
- Ne l'utilise jamais pour usurper l'identité de quelqu'un, harceler,
  tromper ou diffuser de fausses informations.
- Indique toujours clairement qu'une vidéo produite avec cet outil est
  **synthétique** si tu la partages.
- Vérifie la loi de ton pays : la création ou diffusion de « deepfakes » sans
  consentement est illégale dans de nombreuses juridictions.

## Prérequis

- Python 3.9 – 3.10 (SadTalker n'est pas garanti compatible au-delà)
- [ffmpeg](https://ffmpeg.org/) installé et dans le `PATH`
- ~6 Go d'espace disque libre (code + modèles)
- Un accès réseau à GitHub et HuggingFace **au moment de l'installation**
  (pour cloner SadTalker et télécharger ses poids pré-entraînés — ce
  dépôt-ci ne les inclut pas, ils sont trop volumineux et sous licence
  distincte)
- GPU NVIDIA + CUDA fortement recommandé (le CPU fonctionne mais un clip de
  quelques secondes peut prendre plusieurs minutes à générer)

## Installation

```bash
cd lipsync-app
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

# Installe torch en premier, avec la bonne commande pour ton matériel :
# CPU :  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
# CUDA : pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# (voir https://pytorch.org/get-started/locally/)

bash setup.sh   # clone SadTalker, installe ses dépendances, télécharge les modèles
```

`setup.sh` est idempotent : tu peux le relancer sans risque (il met juste à
jour le clone existant).

## Utilisation — appli web

```bash
python app.py
```

Ouvre `http://localhost:5001`, dépose une photo (visage bien visible, de
face) et un fichier audio, puis clique sur « Générer la vidéo ». La vidéo
générée s'affiche et peut être téléchargée directement.

## Utilisation — ligne de commande

```bash
python cli.py --image moi.jpg --audio message.wav --out video.mp4
```

Options utiles :
- `--no-still` : autorise des mouvements de tête plus amples (par défaut la
  tête reste quasi immobile, ce qui donne un rendu plus stable et naturel
  pour un simple message parlé)
- `--no-enhancer` : désactive la passe GFPGAN de restauration du visage
  (plus rapide, légèrement moins net)

## Conseils pour un rendu réaliste

- Utilise une photo nette, bien éclairée, visage de face, yeux ouverts.
- Un enregistrement audio propre (peu de bruit de fond, volume constant)
  donne un bien meilleur mouvement de bouche.
- Laisse `--enhancer gfpgan` activé (par défaut) : la passe de restauration
  du visage réduit nettement les artefacts autour de la bouche et des yeux.
- Sur GPU, essaie `--no-still` pour des vidéos de plusieurs phrases : de
  légers mouvements de tête rendent le résultat beaucoup plus vivant.

## Structure du projet

```
lipsync-app/
├── app.py              # appli web Flask (upload → vidéo)
├── cli.py              # utilisation en ligne de commande
├── setup.sh            # installe SadTalker + modèles
├── requirements.txt    # dépendances Python
├── lipsync/
│   └── engine.py        # appelle SadTalker (vendor/SadTalker/inference.py)
├── templates/           # pages HTML de l'appli web
├── static/               # CSS
├── uploads/              # fichiers temporaires (vidés après chaque job)
├── results/              # vidéos générées (un sous-dossier par job)
└── vendor/SadTalker/     # cloné par setup.sh, non versionné (trop volumineux)
```

## Dépannage

- **« SadTalker introuvable »** : relance `bash setup.sh`.
- **« ffmpeg: command not found »** : installe ffmpeg (`apt install ffmpeg`,
  `brew install ffmpeg`, ou télécharge un build officiel sous Windows).
- **Très lent** : sans GPU, chaque génération peut prendre plusieurs minutes ;
  c'est attendu. `--no-enhancer` accélère un peu les choses.
- **Erreur liée à la version de `numpy`/`torch`** : SadTalker est assez
  strict sur ses versions de dépendances ; utilise un environnement virtuel
  dédié à ce projet plutôt qu'un environnement partagé.
