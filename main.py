"""
Task API — a CRUD API built with FastAPI, now backed by Postgres running in Docker.

Run everything with:
    docker compose up

Or run just the app locally (with Postgres already running separately):
    uvicorn main:app --reload

Then visit:
    http://localhost:8000/         (root info)
    http://localhost:8000/health   (health check, also pings the database)
    http://localhost:8000/docs     (Swagger UI)

What changed from the SQLite version: tasks lived in a single tasks.db file.
Now they live in a real Postgres server, running in its own Docker container.
The endpoints, request bodies, and responses are exactly the same as before —
only the storage layer changed, again.
"""

from typing import Optional

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import get_connection, init_db

app = FastAPI(
    title="Task API",
    version="3.0",
    description="A to-do API backed by Postgres, running in Docker.",
)

# ---------------------------------------------------------------------------
# Connect + set up the table on startup. The connection string comes from
# the DATABASE_URL environment variable (see database.py + .env).
# ---------------------------------------------------------------------------
init_db()


class TaskInput(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


# ---------------------------------------------------------------------------
# Stage: root & health
# Health now also pings the database with SELECT 1 — this is the kind of
# check a real load balancer or deploy pipeline uses to know the app is
# actually usable, not just "the process is running."
# ---------------------------------------------------------------------------
@app.get("/", tags=["Meta"], summary="API info")
def read_root():
    """Basic info about this API and its endpoints."""
    return {"name": "Task API", "version": "3.0", "endpoints": ["/tasks"]}


@app.get("/health", tags=["Meta"], summary="Health check")
def health_check():
    """Checks the app is alive AND the database is reachable."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        return {"status": "ok", "db": "ok"}
    except Exception:
        return JSONResponse(
            status_code=503, content={"status": "ok", "db": "unreachable"}
        )


# ---------------------------------------------------------------------------
# Stage: Read
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

    Optional query parameters (extras), all handled in SQL:
    - **done**: filter by completion status, e.g. `?done=true`
    - **search**: title contains this text (SQL ILIKE), e.g. `?search=milk`
    - **limit** / **offset**: pagination, e.g. `?limit=2&offset=2`
    """
    conn = get_connection()
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list = []

    if done is not None:
        query += " AND done = %s"
        params.append(done)

    if search:
        query += " AND title ILIKE %s"  # ILIKE = case-insensitive LIKE, a Postgres extra
        params.append(f"%{search}%")

    query += " ORDER BY id"

    if limit is not None:
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
    elif offset:
        query += " OFFSET %s"
        params.append(offset)

    with conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    conn.close()

    return rows


@app.get("/tasks/{task_id}", tags=["Tasks"], summary="Get a single task")
def get_task(task_id: int):
    """Returns one task by id. 404 if it doesn't exist."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        row = cur.fetchone()
    conn.close()

    if row is None:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

    return row


# ---------------------------------------------------------------------------
# Stage: Create
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
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
            (payload.title.strip(), False),
        )
        new_row = cur.fetchone()
    conn.commit()
    conn.close()

    return JSONResponse(status_code=201, content=new_row)


# ---------------------------------------------------------------------------
# Stage: Update & Delete
# ---------------------------------------------------------------------------
@app.put("/tasks/{task_id}", tags=["Tasks"], summary="Update a task")
def update_task(task_id: int, payload: TaskInput):
    """
    Updates a task's title and/or done status.
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
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        existing = cur.fetchone()

        if existing is None:
            conn.close()
            return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

        new_title = payload.title.strip() if payload.title is not None else existing["title"]
        new_done = payload.done if payload.done is not None else existing["done"]

        cur.execute(
            "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
            (new_title, new_done, task_id),
        )
        updated = cur.fetchone()

    conn.commit()
    conn.close()

    return updated


@app.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"], summary="Delete a task")
def delete_task(task_id: int):
    """Removes a task by id. Returns 204 with no body, or 404 if unknown id."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        existing = cur.fetchone()

        if existing is None:
            conn.close()
            return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))

    conn.commit()
    conn.close()

    return Response(status_code=204)


# ---------------------------------------------------------------------------
# ★ Extras — same as Week 2, still computed with SQL
# ---------------------------------------------------------------------------
@app.get("/stats", tags=["Extras"], summary="Task statistics")
def get_stats():
    """Returns counts of total / done / open tasks, using SQL COUNT()."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM tasks")
        total = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM tasks WHERE done = TRUE")
        done_count = cur.fetchone()["c"]
    conn.close()
    return {"total": total, "done": done_count, "open": total - done_count}


@app.post("/reset", tags=["Extras"], summary="Reset to seed data")
def reset_tasks():
    """Wipes the table and restores the 3 example tasks. Handy for demos."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM tasks")
        cur.execute("ALTER SEQUENCE tasks_id_seq RESTART WITH 1")  # reset id counter
        cur.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            [("Buy milk", False), ("Walk the dog", False), ("Write README", True)],
        )
        cur.execute("SELECT * FROM tasks ORDER BY id")
        rows = cur.fetchall()
    conn.commit()
    conn.close()

    return {"message": "Tasks reset to seed data", "tasks": rows}
