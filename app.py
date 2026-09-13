import os
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import database as db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-moi-en-production")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-moi")

db.init_db()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        error = "Mot de passe incorrect."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/suivre/<api_key>")
def track_page(api_key):
    device = db.get_device_by_api_key(api_key)
    if not device:
        return render_template("track.html", device_name=None, api_key=None), 404
    return render_template("track.html", device_name=device["name"], api_key=api_key)


# ---------- API consultée par le tableau de bord (protégée par login) ----------

@app.route("/api/devices", methods=["GET"])
@login_required
def api_list_devices():
    devices = db.get_devices()
    for d in devices:
        d.pop("api_key", None)
    return jsonify(devices)


@app.route("/api/devices", methods=["POST"])
@login_required
def api_create_device():
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "nom requis"}), 400
    api_key = db.add_device(name)
    return jsonify({"name": name, "api_key": api_key}), 201


@app.route("/api/devices/<int:device_id>", methods=["DELETE"])
@login_required
def api_delete_device(device_id):
    db.delete_device(device_id)
    return jsonify({"ok": True})


@app.route("/api/devices/<int:device_id>/key", methods=["GET"])
@login_required
def api_get_device_key(device_id):
    device = db.get_device_by_id(device_id)
    if not device:
        return jsonify({"error": "introuvable"}), 404
    return jsonify({"api_key": device["api_key"]})


@app.route("/api/positions/<int:device_id>/latest", methods=["GET"])
@login_required
def api_latest_position(device_id):
    pos = db.get_latest_position(device_id)
    return jsonify(pos or {})


@app.route("/api/positions/<int:device_id>/history", methods=["GET"])
@login_required
def api_history(device_id):
    start = request.args.get("start")
    end = request.args.get("end")
    history = db.get_history(device_id, start=start, end=end)
    return jsonify(history)


# ---------- API utilisée par le téléphone suivi (protégée par clé API) ----------

@app.route("/api/ping", methods=["POST"])
def api_ping():
    payload = request.get_json(silent=True) or {}
    api_key = payload.get("api_key") or request.headers.get("X-API-Key")
    device = db.get_device_by_api_key(api_key) if api_key else None
    if not device:
        return jsonify({"error": "clé API invalide"}), 401

    try:
        lat = float(payload["lat"])
        lon = float(payload["lon"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "lat/lon requis"}), 400

    accuracy = payload.get("accuracy")
    battery = payload.get("battery")
    recorded_at = payload.get("recorded_at")

    db.add_position(device["id"], lat, lon, accuracy=accuracy, battery=battery, recorded_at=recorded_at)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
