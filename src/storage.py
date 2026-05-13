"""Simple SQLite storage for hardware sensor readings.

Provides functions to initialize a local SQLite DB and insert/read sensor payloads.

The DB file is stored at `data/hardware.db` so Render or local deployments can persist
hardware readings between restarts (if the service volume is persisted).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable
import json

DB_PATH = Path(__file__).parent.parent / "data" / "hardware.db"


def init_db(db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            payload TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def insert_reading(payload: dict, db_path: Path | None = None) -> int:
    """Insert a JSON payload into the DB and return the new row id."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("INSERT INTO sensor_readings (payload) VALUES (?)", (json.dumps(payload),))
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid


def get_recent(limit: int = 100, db_path: Path | None = None) -> list[dict]:
    """Return the most recent `limit` readings as dicts: id, timestamp, payload(dict)."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, payload FROM sensor_readings ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    results: list[dict] = []
    for rid, ts, payload in rows:
        try:
            obj = json.loads(payload)
        except Exception:
            obj = {"raw": payload}
        results.append({"id": rid, "timestamp": ts, "payload": obj})
    return results
