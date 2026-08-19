"""
Task API — a small in-memory CRUD API built with FastAPI.

Run with:
    uvicorn main:app --reload

Then visit:
    http://localhost:8000/         (root info)
    http://localhost:8000/health   (health check)
    http://localhost:8000/docs     (Swagger UI)
"""

from typing import List, Optional

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A tiny in-memory to-do API built for the CRUD assignment.",
)


# ---------------------------------------------------------------------------
# "Database" — just a list in memory. Resets every time the server restarts.
# ---------------------------------------------------------------------------
def seed_tasks() -> List[dict]:
    return [
        {"id": 1, "title": "Buy milk", "done": False},
        {"id": 2, "title": "Walk the dog", "done": False},
        {"id": 3, "title": "Write README", "done": True},
    ]


tasks: List[dict] = seed_tasks()
next_id: int = 4


# ---------------------------------------------------------------------------
# Request body shape for POST / PUT.
# Both fields are optional here on purpose: we do our own validation below
# so we can return a clean 400 with a JSON error instead of FastAPI's
# default 422 response.
# ---------------------------------------------------------------------------
class TaskInput(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


# ---------------------------------------------------------------------------
# Stage 1 — root & health
# ---------------------------------------------------------------------------
@app.get("/", tags=["Meta"], summary="API info")
def read_root():
    """Basic info about this API and its endpoints."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", tags=["Meta"], summary="Health check")
def health_check():
    """Used to check the server is alive."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Stage 2 — Read
# ---------------------------------------------------------------------------
@app.get("/tasks", tags=["Tasks"], summary="List tasks")
def list_tasks(
    done: Optional[bool] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
):
    """
    Returns all tasks.

    Optional query parameters (extras):
    - **done**: filter by completion status, e.g. `?done=true`
    - **search**: only tasks whose title contains this text, e.g. `?search=milk`
    - **limit** / **offset**: simple pagination, e.g. `?limit=2&offset=2`
    """
    result = tasks

    if done is not None:
        result = [t for t in result if t["done"] == done]

    if search:
        result = [t for t in result if search.lower() in t["title"].lower()]

    if offset:
        result = result[offset:]

    if limit is not None:
        result = result[:limit]

    return result


@app.get("/tasks/{task_id}", tags=["Tasks"], summary="Get a single task")
def get_task(task_id: int):
    """Returns one task by id. 404 if it doesn't exist."""
    for t in tasks:
        if t["id"] == task_id:
            return t
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})


# ---------------------------------------------------------------------------
# Stage 3 — Create
# ---------------------------------------------------------------------------
@app.post("/tasks", status_code=201, tags=["Tasks"], summary="Create a task")
def create_task(payload: TaskInput):
    """Creates a new task. `title` is required and cannot be empty."""
    global next_id

    if not payload.title or not payload.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "title is required and cannot be empty"},
        )

    new_task = {"id": next_id, "title": payload.title.strip(), "done": False}
    tasks.append(new_task)
    next_id += 1
    return JSONResponse(status_code=201, content=new_task)


# ---------------------------------------------------------------------------
# Stage 4 — Update & Delete
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

    for t in tasks:
        if t["id"] == task_id:
            if payload.title is not None:
                t["title"] = payload.title.strip()
            if payload.done is not None:
                t["done"] = payload.done
            return t

    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})


@app.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"], summary="Delete a task")
def delete_task(task_id: int):
    """Removes a task by id. Returns 204 with no body, or 404 if unknown id."""
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            tasks.pop(i)
            return Response(status_code=204)
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})


# ---------------------------------------------------------------------------
# ★ Extras (optional, but included here for a stronger submission)
# ---------------------------------------------------------------------------
@app.get("/stats", tags=["Extras"], summary="Task statistics")
def get_stats():
    """Returns counts of total / done / open tasks."""
    total = len(tasks)
    done_count = len([t for t in tasks if t["done"]])
    return {"total": total, "done": done_count, "open": total - done_count}


@app.post("/reset", tags=["Extras"], summary="Reset to seed data")
def reset_tasks():
    """Restores the 3 example tasks. Handy for demos and re-testing."""
    global tasks, next_id
    tasks = seed_tasks()
    next_id = 4
    return {"message": "Tasks reset to seed data", "tasks": tasks}
