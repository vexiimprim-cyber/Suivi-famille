"""Wrapper around the vendored SadTalker inference pipeline.

SadTalker (https://github.com/OpenTalker/SadTalker) turns a single portrait
photo plus a voice recording into a talking-head video: it drives mouth
shape, head pose and eye blinks from the audio using a 3D face model, then
renders the result back onto the source photo.

This module does not reimplement any of that. It shells out to SadTalker's
own ``inference.py`` (cloned by ``setup.sh`` into ``vendor/SadTalker``) and
manages the temp/result directories around it, because the model code and
its pretrained checkpoints are a separate project with their own release
cycle and license.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
VENDOR_DIR = APP_ROOT / "vendor" / "SadTalker"
CHECKPOINTS_DIR = VENDOR_DIR / "checkpoints"
RESULTS_DIR = APP_ROOT / "results"


class SadTalkerNotInstalled(RuntimeError):
    """Raised when the vendored SadTalker checkout or its weights are missing."""


class InferenceFailed(RuntimeError):
    """Raised when the SadTalker subprocess exits non-zero."""


@dataclass
class GenerationOptions:
    still: bool = True          # keep head mostly still, focus on lip movement
    enhancer: str | None = "gfpgan"  # face restoration pass for extra realism
    preprocess: str = "full"    # "full" keeps the whole frame, not just a crop


def check_installed() -> None:
    inference_script = VENDOR_DIR / "inference.py"
    if not inference_script.exists():
        raise SadTalkerNotInstalled(
            "SadTalker introuvable dans vendor/SadTalker. Lance `bash setup.sh` "
            "une fois (nécessite un accès réseau à GitHub/HuggingFace) avant "
            "d'utiliser l'application."
        )
    if not CHECKPOINTS_DIR.exists() or not any(CHECKPOINTS_DIR.iterdir()):
        raise SadTalkerNotInstalled(
            "Les poids pré-entraînés de SadTalker sont manquants "
            f"({CHECKPOINTS_DIR}). Relance `bash setup.sh` pour les télécharger."
        )


def generate(
    image_path: str | Path,
    audio_path: str | Path,
    options: GenerationOptions | None = None,
) -> Path:
    """Run SadTalker on one image + one audio file, return the output mp4 path."""
    check_installed()
    options = options or GenerationOptions()

    job_id = uuid.uuid4().hex[:12]
    job_result_dir = RESULTS_DIR / job_id
    job_result_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(VENDOR_DIR / "inference.py"),
        "--source_image", str(image_path),
        "--driven_audio", str(audio_path),
        "--result_dir", str(job_result_dir),
        "--preprocess", options.preprocess,
    ]
    if options.still:
        cmd.append("--still")
    if options.enhancer:
        cmd += ["--enhancer", options.enhancer]

    proc = subprocess.run(
        cmd,
        cwd=str(VENDOR_DIR),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise InferenceFailed(
            f"SadTalker a échoué (code {proc.returncode}).\n"
            f"--- stdout ---\n{proc.stdout[-4000:]}\n"
            f"--- stderr ---\n{proc.stderr[-4000:]}"
        )

    videos = sorted(job_result_dir.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not videos:
        raise InferenceFailed(
            f"SadTalker s'est terminé sans erreur mais aucune vidéo .mp4 n'a été "
            f"trouvée dans {job_result_dir}."
        )
    return videos[-1]


def cleanup_job(video_path: Path) -> None:
    """Remove a job's result directory (call once the video has been sent)."""
    job_dir = video_path.parent
    if job_dir.parent == RESULTS_DIR and job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)
