import os
import uuid
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from lipsync.engine import (
    APP_ROOT,
    GenerationOptions,
    InferenceFailed,
    SadTalkerNotInstalled,
    generate,
)

ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_AUDIO_EXT = {".wav", ".mp3", ".m4a", ".ogg"}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-moi-en-production")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

UPLOAD_DIR = APP_ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def _ext_ok(filename: str, allowed: set[str]) -> bool:
    return Path(filename).suffix.lower() in allowed


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate_video():
    image = request.files.get("image")
    audio = request.files.get("audio")

    if not image or not image.filename or not _ext_ok(image.filename, ALLOWED_IMAGE_EXT):
        flash("Image invalide (formats acceptés : png, jpg, jpeg, webp).")
        return redirect(url_for("index"))
    if not audio or not audio.filename or not _ext_ok(audio.filename, ALLOWED_AUDIO_EXT):
        flash("Audio invalide (formats acceptés : wav, mp3, m4a, ogg).")
        return redirect(url_for("index"))

    job_id = uuid.uuid4().hex[:12]
    image_path = UPLOAD_DIR / f"{job_id}{Path(image.filename).suffix.lower()}"
    audio_path = UPLOAD_DIR / f"{job_id}{Path(audio.filename).suffix.lower()}"
    image.save(image_path)
    audio.save(audio_path)

    still = request.form.get("still") == "on"
    enhancer = request.form.get("enhancer") or None
    options = GenerationOptions(still=still, enhancer=enhancer)

    try:
        video_path = generate(image_path, audio_path, options)
    except SadTalkerNotInstalled as exc:
        flash(str(exc))
        return redirect(url_for("index"))
    except InferenceFailed as exc:
        flash(f"La génération a échoué : {exc}")
        return redirect(url_for("index"))
    finally:
        image_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)

    return render_template("result.html", video_url=url_for("download", job=video_path.parent.name, filename=video_path.name))


@app.route("/results/<job>/<filename>")
def download(job: str, filename: str):
    results_dir = (APP_ROOT / "results").resolve()
    video_path = (results_dir / job / filename).resolve()
    if results_dir not in video_path.parents or not video_path.exists():
        return "Vidéo introuvable ou déjà nettoyée.", 404
    return send_file(video_path, mimetype="video/mp4")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
