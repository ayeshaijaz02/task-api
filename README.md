# Task API

A small in-memory CRUD API for managing a to-do list, built with **Python + FastAPI**.
Built for FlyRank Internship — Backend Track — W2 · A1.

## What this is

A tiny backend that lets a client **C**reate, **R**ead, **U**pdate, and **D**elete tasks.
Data lives only in memory (a Python list) — it resets every time the server restarts. No database yet.

## How to install & run

```bash
# 1. clone this repo, then cd into it
cd task-api

# 2. create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate

# 3. install dependencies
pip install -r requirements.txt

# 4. run the server
uvicorn main:app --reload
```

The server starts on **http://localhost:8000**.

## Endpoints

| CRUD op | Method | Path             | Description                              | Success | Error codes |
|---------|--------|------------------|-------------------------------------------|---------|-------------|
| —       | GET    | `/`              | API info                                  | 200     | —           |
| —       | GET    | `/health`        | Health check                              | 200     | —           |
| Read    | GET    | `/tasks`         | List all tasks (supports `?done=`, `?search=`, `?limit=`, `?offset=`) | 200 | — |
| Read    | GET    | `/tasks/{id}`    | Get one task                              | 200     | 404         |
| Create  | POST   | `/tasks`         | Create a task (`{"title": "..."}`)        | 201     | 400         |
| Update  | PUT    | `/tasks/{id}`    | Update a task's title and/or done         | 200     | 400, 404    |
| Delete  | DELETE | `/tasks/{id}`    | Delete a task                             | 204     | 404         |
| Extra   | GET    | `/stats`         | `{ total, done, open }` counts            | 200     | —           |
| Extra   | POST   | `/reset`         | Restore the 3 example tasks               | 200     | —           |

## Swagger UI

Interactive docs (built into FastAPI, zero setup) live at:

**http://localhost:8000/docs**

Every endpoint above is listed there with a "Try it out" button.

## Testing it — example curl commands

```bash
# root + health
curl -i http://localhost:8000/
curl -i http://localhost:8000/health

# read
curl -i http://localhost:8000/tasks
curl -i http://localhost:8000/tasks/1
curl -i http://localhost:8000/tasks/99          # -> 404

# create
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'                     # -> 201

curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{}'                                       # -> 400

# update
curl -i -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"done": true}'                           # -> 200

# delete
curl -i -X DELETE http://localhost:8000/tasks/1 # -> 204
curl -i -X DELETE http://localhost:8000/tasks/1 # -> 404 (already gone)
```

<!--
  ⬇️ PASTE YOUR OWN curl -i OUTPUT HERE BEFORE SUBMITTING ⬇️
  Run one of the commands above against your running server and paste the
  real terminal output (with status code + headers visible) below.
-->

### Sample curl -i output

```
PASTE-YOUR-REAL-OUTPUT-HERE
```

## Swagger screenshot

<!-- ⬇️ Take a screenshot of /docs with the CRUD cycle working, save it as
     swagger-screenshot.png in this folder, and reference it below. -->

![Swagger UI](swagger-screenshot.png)

## The mortality experiment

<!--
  Do this yourself: create a few tasks, restart the server (Ctrl+C, then
  `uvicorn main:app --reload` again), then GET /tasks. Write 2 sentences
  about what happened and why.
-->

_Your two sentences here._

## AI vs me

<!--
  This section is intentionally left for you to complete honestly — the
  assignment explicitly asks you to write your OWN prompt from memory
  (without copying from the assignment doc), generate a second version in
  ai-version/, run both, diff them, and reflect. That comparison is only
  useful if the prompt and the reflection are genuinely yours.
-->

**My prompt:**

```
PASTE-YOUR-OWN-PROMPT-HERE
```

**What the AI did better:**

**What it got wrong or ignored:**

**What my prompt forgot to specify:**

**After the rematch, what changed:**
