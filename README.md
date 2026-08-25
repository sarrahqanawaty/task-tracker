# Task Tracker API

A minimal REST API for tracking tasks. This repository currently contains
the project skeleton only: a FastAPI application instance and a `/health`
endpoint.

## Tech stack

- **Python** with **FastAPI** for the web framework
- **Pydantic** for request/response validation
- **Uvicorn** as the ASGI server
- **python-dotenv** for environment variable loading
- **SQLite** (via Python's built-in `sqlite3`) for persistence — *not yet implemented*

## Project structure

```
task-tracker/
├── app/
│   ├── main.py          # FastAPI app instance, CORS, and routes
│   ├── models.py        # Enums and the three Pydantic models
│   ├── storage.py       # In-memory task store
│   └── business_rules.py # Status transition rules
├── backend/
│   ├── main.py          # Thin re-export of app.main:app
│   └── data/            # Location of the SQLite file (tasks.db), added later
├── frontend/
│   └── index.html       # Kanban board — vanilla HTML, CSS and JavaScript
├── tests/               # pytest suite
├── docs/                # Module deliverables and verification records
├── requirements.txt     # Direct dependencies, pinned
├── requirements.lock.txt # Full resolved tree from `pip freeze`
├── .env.example
├── .gitignore
└── README.md
```

## Setup

From the project root (`task-tracker/`):

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

`requirements.txt` pins the four direct dependencies to the versions this
project was verified against (FastAPI 0.141.1, Uvicorn 0.52.4, Pydantic
2.13.4, python-dotenv 1.2.3), verified on Python 3.14. `requirements.lock.txt`
records the full resolved dependency tree.

If you upgrade a dependency, refresh the lockfile:

```
pip freeze > requirements.lock.txt
```

## Environment variables

| Variable  | Default       | Purpose                                      |
|-----------|---------------|----------------------------------------------|
| `PORT`    | `8000`        | Port the server listens on                    |
| `APP_ENV` | `development` | Environment name; enables auto-reload locally |

`.env` is git-ignored. `.env.example` is committed as the template.

## Run the server

From the project root, with the virtual environment active:

```
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The server runs at <http://127.0.0.1:8000>.

## Test the health endpoint

```
curl http://127.0.0.1:8000/health
```

On Windows PowerShell, `curl` is an alias for `Invoke-WebRequest`; call the
real binary instead:

```
curl.exe http://127.0.0.1:8000/health
```

Expected response — HTTP 200 with a JSON body of this shape:

```json
{
  "status": "ok",
  "timestamp": "2026-08-23T09:15:42.123456+00:00"
}
```

The `timestamp` value is the current UTC time in ISO 8601 format, so it
differs on every request.

## Run the frontend

The board is a single static file. Open it through a local web server, **not**
with `file://` — the API only accepts the origins listed in `ALLOWED_ORIGINS`
in `app/main.py`, and a `file://` page sends `Origin: null`.

From the project root, in a second terminal:

```
python -m http.server 5500 --bind 127.0.0.1
```

Then open <http://localhost:5500/frontend/index.html> with the API running.

Allowed origins are `http://localhost:5500`, `http://127.0.0.1:5500`,
`http://localhost:8080` and `http://127.0.0.1:8080`. Serving the page from a
different port means adding that origin to `ALLOWED_ORIGINS` first.

What the board does: three status columns with counts, cards sorted High →
Medium → Low, loading/ready/empty/error states with a Retry action,
drag-and-drop that PATCHes the API and rolls the card back when the server
rejects the transition, and a create/edit modal with title trimming and visible
server validation messages.

## Interactive API documentation

FastAPI generates documentation automatically:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

## Tests

```
python -m pytest -q
```

24 passing. The suite covers the CRUD routes, the status-transition rules, and
the PATCH edge cases the board depends on.

## Scope

Intentionally **not** included at this stage: database implementation,
authentication, a build step or frontend framework, Docker, and deployment.
Tasks live in memory and are lost when the server restarts.