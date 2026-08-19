"""
Task API — a CRUD API built with FastAPI, now backed by a real SQLite database.

Run with:
    uvicorn main:app --reload

Then visit:
    http://localhost:8000/         (root info)
    http://localhost:8000/health   (health check)
    http://localhost:8000/docs     (Swagger UI)

What changed from Week 2: tasks used to live in a Python list (gone on
restart). Now they live in tasks.db, a SQLite file (still there on restart).
The endpoints, request bodies, and responses are exactly the same as before —
only the storage layer changed.
"""

import sqlite3
from typing import Optional

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import get_connection, init_db

app = FastAPI(
    title="Task API",
    version="2.0",
    description="A to-do API backed by a real SQLite database (tasks.db).",
)

# ---------------------------------------------------------------------------
# "Database" — tasks.db, created + seeded automatically the first time
# this file is imported (i.e. the first time the server starts).
# ---------------------------------------------------------------------------
init_db()


def row_to_task(row) -> dict:
    """Turns a sqlite3.Row into the same {id, title, done} shape as Week 2."""
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


# ---------------------------------------------------------------------------
# Request body shape for POST / PUT — unchanged from Week 2.
# ---------------------------------------------------------------------------
class TaskInput(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


# ---------------------------------------------------------------------------
# Stage 1 — root & health (unchanged, nothing to do with storage)
# ---------------------------------------------------------------------------
@app.get("/", tags=["Meta"], summary="API info")
def read_root():
    """Basic info about this API and its endpoints."""
    return {"name": "Task API", "version": "2.0", "endpoints": ["/tasks"]}


@app.get("/health", tags=["Meta"], summary="Health check")
def health_check():
    """Used to check the server is alive."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Stage 2 — Read (now runs a SELECT instead of filtering a Python list)
# ---------------------------------------------------------------------------
@app.get("/tasks", tags=["Tasks"], summary="List tasks")
def list_tasks(
    done: Optional[bool] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
):
    """
    Returns tasks from the database.

    Optional query parameters (extras), all handled in SQL now:
    - **done**: filter by completion status, e.g. `?done=true`
    - **search**: title contains this text (SQL LIKE), e.g. `?search=milk`
    - **limit** / **offset**: pagination, e.g. `?limit=2&offset=2`
    """
    conn = get_connection()
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list = []

    if done is not None:
        query += " AND done = ?"
        params.append(1 if done else 0)

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    elif offset:
        query += " LIMIT -1 OFFSET ?"
        params.append(offset)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_task(r) for r in rows]


@app.get("/tasks/{task_id}", tags=["Tasks"], summary="Get a single task")
def get_task(task_id: int):
    """Returns one task by id. 404 if it doesn't exist."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()

    if row is None:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

    return row_to_task(row)


# ---------------------------------------------------------------------------
# Stage 3 — Create (INSERT instead of list.append)
# ---------------------------------------------------------------------------
@app.post("/tasks", status_code=201, tags=["Tasks"], summary="Create a task")
def create_task(payload: TaskInput):
    """Creates a new task. `title` is required and cannot be empty."""
    if not payload.title or not payload.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "title is required and cannot be empty"},
        )

    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (payload.title.strip(), 0),
    )
    conn.commit()

    new_row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    conn.close()

    return JSONResponse(status_code=201, content=row_to_task(new_row))


# ---------------------------------------------------------------------------
# Stage 4 — Update & Delete (UPDATE / DELETE instead of list mutation)
# ---------------------------------------------------------------------------
@app.put("/tasks/{task_id}", tags=["Tasks"], summary="Update a task")
def update_task(task_id: int, payload: TaskInput):
    """
    Replaces a task's title and/or done status with whatever is in the body.
    404 if the id is unknown, 400 if the body is empty/invalid.
    """
    if payload.title is None and payload.done is None:
        return JSONResponse(
            status_code=400,
            content={"error": "provide at least 'title' or 'done' to update"},
        )
    if payload.title is not None and not payload.title.strip():
        return JSONResponse(status_code=400, content={"error": "title cannot be empty"})

    conn = get_connection()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if existing is None:
        conn.close()
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

    new_title = payload.title.strip() if payload.title is not None else existing["title"]
    new_done = (1 if payload.done else 0) if payload.done is not None else existing["done"]

    conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, new_done, task_id),
    )
    conn.commit()

    updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()

    return row_to_task(updated)


@app.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"], summary="Delete a task")
def delete_task(task_id: int):
    """Removes a task by id. Returns 204 with no body, or 404 if unknown id."""
    conn = get_connection()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if existing is None:
        conn.close()
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return Response(status_code=204)


# ---------------------------------------------------------------------------
# ★ Extras — now computed with SQL instead of Python loops
# ---------------------------------------------------------------------------
@app.get("/stats", tags=["Extras"], summary="Task statistics")
def get_stats():
    """Returns counts of total / done / open tasks, using SQL COUNT()."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    done_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
    conn.close()
    return {"total": total, "done": done_count, "open": total - done_count}


@app.post("/reset", tags=["Extras"], summary="Reset to seed data")
def reset_tasks():
    """Wipes the table and restores the 3 example tasks. Handy for demos."""
    conn = get_connection()
    conn.execute("DELETE FROM tasks")
    try:
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'tasks'")
    except sqlite3.OperationalError:
        pass  # sqlite_sequence only exists once an autoincrement id has been used

    conn.executemany(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        [("Buy milk", 0), ("Walk the dog", 0), ("Write README", 1)],
    )
    conn.commit()

    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()

    return {
        "message": "Tasks reset to seed data",
        "tasks": [row_to_task(r) for r in rows],
    }
