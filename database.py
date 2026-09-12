import os
import secrets
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "suivi.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            api_key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            accuracy REAL,
            battery INTEGER,
            recorded_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_positions_device_time
            ON positions(device_id, recorded_at);
        """
    )
    conn.commit()
    conn.close()


def add_device(name):
    api_key = secrets.token_hex(16)
    conn = get_connection()
    conn.execute(
        "INSERT INTO devices (name, api_key, created_at) VALUES (?, ?, ?)",
        (name, api_key, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()
    return api_key


def delete_device(device_id):
    conn = get_connection()
    conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
    conn.close()


def get_devices():
    conn = get_connection()
    rows = conn.execute("SELECT id, name, api_key, created_at FROM devices ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_device_by_id(device_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_device_by_api_key(api_key):
    conn = get_connection()
    row = conn.execute("SELECT * FROM devices WHERE api_key = ?", (api_key,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_position(device_id, lat, lon, accuracy=None, battery=None, recorded_at=None):
    if recorded_at is None:
        recorded_at = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    conn.execute(
        "INSERT INTO positions (device_id, lat, lon, accuracy, battery, recorded_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (device_id, lat, lon, accuracy, battery, recorded_at),
    )
    conn.commit()
    conn.close()


def get_latest_position(device_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM positions WHERE device_id = ? ORDER BY recorded_at DESC LIMIT 1",
        (device_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_history(device_id, start=None, end=None, limit=2000):
    query = "SELECT * FROM positions WHERE device_id = ?"
    params = [device_id]
    if start:
        query += " AND recorded_at >= ?"
        params.append(start)
    if end:
        query += " AND recorded_at <= ?"
        params.append(end)
    query += " ORDER BY recorded_at ASC LIMIT ?"
    params.append(limit)

    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
