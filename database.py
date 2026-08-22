"""
database.py — connects to Postgres and sets up the "tasks" table.

Reads the connection string from the DATABASE_URL environment variable
(loaded from .env). Creates the table if missing, and seeds 3 example
tasks only the very first time (when the table is empty) — same rule
as Week 2's SQLite version.
"""

import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()  # reads the .env file into environment variables

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection() -> psycopg.Connection:
    """Opens a connection to Postgres. Rows come back as dicts (by column name)."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db() -> None:
    """Creates the table if needed, and seeds it if it's empty. Call once at startup."""
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )
        conn.commit()

        cur.execute("SELECT COUNT(*) AS count FROM tasks")
        count = cur.fetchone()["count"]

        if count == 0:
            cur.executemany(
                "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                [
                    ("Buy milk", False),
                    ("Walk the dog", False),
                    ("Write README", True),
                ],
            )
            conn.commit()

    conn.close()
