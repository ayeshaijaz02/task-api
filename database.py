"""
database.py — sets up the SQLite database for the Task API.

Creates tasks.db (if missing), creates the "tasks" table (if missing),
and seeds the same 3 example tasks used in Week 2 — but only on the
very first run, so restarting the server never duplicates them.
"""

import sqlite3

DB_FILE = "tasks.db"


def get_connection() -> sqlite3.Connection:
    """Opens a connection to tasks.db. Rows come back dict-like (by column name)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Creates the table if needed, and seeds it if it's empty. Call once at startup."""
    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

    if count == 0:
        conn.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Buy milk", 0),
                ("Walk the dog", 0),
                ("Write README", 1),
            ],
        )
        conn.commit()

    conn.close()
