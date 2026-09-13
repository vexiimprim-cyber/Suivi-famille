#!/usr/bin/env python3
"""Ligne de commande : anime une photo à partir d'un fichier audio (SadTalker).

Exemple :
    python cli.py --image moi.jpg --audio message.wav --out video.mp4
"""
import argparse
import shutil
import sys

from lipsync.engine import GenerationOptions, InferenceFailed, SadTalkerNotInstalled, generate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Photo source (portrait, visage visible)")
    parser.add_argument("--audio", required=True, help="Fichier audio (voix à synchroniser)")
    parser.add_argument("--out", required=True, help="Chemin du fichier vidéo de sortie (.mp4)")
    parser.add_argument("--no-still", action="store_true", help="Autoriser des mouvements de tête plus amples")
    parser.add_argument("--no-enhancer", action="store_true", help="Désactiver GFPGAN (plus rapide, moins net)")
    args = parser.parse_args()

    options = GenerationOptions(
        still=not args.no_still,
        enhancer=None if args.no_enhancer else "gfpgan",
    )

    try:
        video_path = generate(args.image, args.audio, options)
    except SadTalkerNotInstalled as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    except InferenceFailed as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    shutil.copyfile(video_path, args.out)
    print(f"Vidéo générée : {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
