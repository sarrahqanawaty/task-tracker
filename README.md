# Task Tracker API

A minimal REST API for tracking tasks, with a vanilla-JavaScript Kanban board
in front of it. Built across Modules 1-3 of the AI-Assisted Coding course and
extended in the mid-course project.

**Branches**

| Branch | Contents |
|---|---|
| `main` | The Modules 1-3 baseline: CRUD API, status-transition rules, Kanban board, 24 tests. |
| `mid-course-project` | The baseline plus two new features (below) and 20 more tests. **This is the branch to review.** |

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
│   ├── storage.py       # In-memory task store and the query filters
│   ├── business_rules.py # Status transition rules
│   └── due_dates.py     # Overdue rule (mid-course Feature 1)
├── backend/
│   ├── main.py          # Thin re-export of app.main:app
│   └── data/            # Location of the SQLite file (tasks.db), added later
├── frontend/
│   └── index.html       # Kanban board — vanilla HTML, CSS and JavaScript
├── tests/               # pytest suite
├── docs/                # Module deliverables and verification records
│   └── midcourse/       # Mid-course project documentation
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

## Mid-course project features

Two features were added on the `mid-course-project` branch. Both are usable from
the board.

### Feature 1 — Due dates and overdue tasks

Every task takes an optional `due_date` (an ISO `YYYY-MM-DD` date). The API
returns a derived `is_overdue` flag, and the card shows a red **Overdue** pill
for a late task or a neutral **Due** pill otherwise.

A task counts as overdue when it has a due date, that date is strictly in the
past, and its status is not `Done`. The rule lives in `app/due_dates.py` and is
recomputed on every read, so a task becomes overdue on its own as the date
passes. Filter the board to late work with the **Overdue only** checkbox, or the
API directly:

```
curl "http://127.0.0.1:8000/tasks?overdue=true"
```

### Feature 2 — Search and combined filters

`GET /tasks` accepts `search`, `assignee`, `overdue`, `status` and `priority`.
They combine with AND, and any parameter left out is not applied. `search` is a
case-insensitive substring match on title and description; a blank or
whitespace-only value means *no filter*, never *match nothing*.

```
curl "http://127.0.0.1:8000/tasks?search=invoice&assignee=Sarah&overdue=true"
```

The filter bar above the board drives the same parameters. Filtering happens on
the server, so the column counts always match what the API returned.

Documentation for this work is in [`docs/midcourse/`](docs/midcourse/):
user stories, the mini-ADR, the prompt log, verification evidence, and a
reflection.

## Interactive API documentation

FastAPI generates documentation automatically:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

## Tests

```
python -m pytest -q
```

**44 passing** on `mid-course-project` (24 from Modules 1-3, 20 added by the
mid-course project). The suite covers the CRUD routes, the status-transition
rules, the PATCH edge cases the board depends on, the due-date and overdue
rules, and every filter combination.

Run one group at a time with `-k`:

```
python -m pytest -q -k "overdue"
python -m pytest -q -k "transition"
```

## Scope

Intentionally **not** included: database implementation, authentication, a build
step or frontend framework, Docker, and deployment. Tasks live in memory and are
lost when the server restarts.

Also deliberately out of scope for the mid-course features: recurring due dates,
reminders and notifications, saved filter presets, sorting by due date, bulk
edits, and persisting filter state in the URL. The reasoning is in
[`docs/midcourse/mini-adr.md`](docs/midcourse/mini-adr.md).