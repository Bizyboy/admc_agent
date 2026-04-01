"""
MemoryStore — persistent conversation memory backed by SQLite.

Stores:
  - Short-term conversation history per user (last N turns)
  - Long-term episodic journal entries (timestamped observations)
  - Key-value facts (persistent beliefs)
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("admc.memory")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversation (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   TEXT    NOT NULL,
    role      TEXT    NOT NULL,
    content   TEXT    NOT NULL,
    ts        REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS episodic (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    category  TEXT    NOT NULL DEFAULT 'journal',
    content   TEXT    NOT NULL,
    metadata  TEXT,
    ts        REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS facts (
    key       TEXT PRIMARY KEY,
    value     TEXT NOT NULL,
    updated   REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_conv_user ON conversation(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_episodic_ts ON episodic(ts);
"""


class MemoryStore:
    """Thread-safe SQLite-backed memory store."""

    def __init__(self, db_path: str = "admc_memory.db") -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        # Initialise schema on main thread connection
        conn = self._get_conn()
        conn.executescript(_SCHEMA)
        conn.commit()
        logger.info("MemoryStore initialised at '%s'.", db_path)

    # ---------------------------------------------------------------------- #
    # Conversation history
    # ---------------------------------------------------------------------- #

    def add_entry(self, user_id: str, role: str, content: str) -> None:
        """Append a conversation turn."""
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO conversation (user_id, role, content, ts) VALUES (?, ?, ?, ?)",
            (user_id, role, content, time.time()),
        )
        conn.commit()

    def get_recent(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent *limit* turns for a user."""
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT role, content, ts FROM conversation WHERE user_id = ? ORDER BY ts DESC LIMIT ?",
            (user_id, limit),
        )
        rows = cur.fetchall()
        return [{"role": r[0], "content": r[1], "ts": r[2]} for r in reversed(rows)]

    def get_all_users(self) -> list[str]:
        conn = self._get_conn()
        cur = conn.execute("SELECT DISTINCT user_id FROM conversation")
        return [r[0] for r in cur.fetchall()]

    def interaction_count(self, user_id: str) -> int:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT COUNT(*) FROM conversation WHERE user_id = ? AND role = 'user'", (user_id,)
        )
        return cur.fetchone()[0]

    def last_interaction_time(self, user_id: str) -> float | None:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT MAX(ts) FROM conversation WHERE user_id = ?", (user_id,)
        )
        result = cur.fetchone()[0]
        return result

    # ---------------------------------------------------------------------- #
    # Episodic journal
    # ---------------------------------------------------------------------- #

    def add_journal_entry(self, content: str, category: str = "journal", metadata: dict | None = None) -> None:
        """Add a timestamped observation to the episodic journal."""
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO episodic (category, content, metadata, ts) VALUES (?, ?, ?, ?)",
            (category, content, json.dumps(metadata or {}), time.time()),
        )
        conn.commit()

    def get_journal(self, category: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        conn = self._get_conn()
        if category:
            cur = conn.execute(
                "SELECT category, content, metadata, ts FROM episodic WHERE category = ? ORDER BY ts DESC LIMIT ?",
                (category, limit),
            )
        else:
            cur = conn.execute(
                "SELECT category, content, metadata, ts FROM episodic ORDER BY ts DESC LIMIT ?",
                (limit,),
            )
        return [
            {"category": r[0], "content": r[1], "metadata": json.loads(r[2] or "{}"), "ts": r[3]}
            for r in cur.fetchall()
        ]

    # ---------------------------------------------------------------------- #
    # Persistent facts / beliefs
    # ---------------------------------------------------------------------- #

    def set_fact(self, key: str, value: Any) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO facts (key, value, updated) VALUES (?, ?, ?)",
            (key, json.dumps(value), time.time()),
        )
        conn.commit()

    def get_fact(self, key: str, default: Any = None) -> Any:
        conn = self._get_conn()
        cur = conn.execute("SELECT value FROM facts WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return default

    # ---------------------------------------------------------------------- #
    # Lifecycle
    # ---------------------------------------------------------------------- #

    def close(self) -> None:
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            del self._local.conn

    # ---------------------------------------------------------------------- #
    # Internal
    # ---------------------------------------------------------------------- #

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn
