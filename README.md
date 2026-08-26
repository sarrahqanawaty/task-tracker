# Task Tracker API

A minimal REST API for tracking tasks, with a vanilla-JavaScript Kanban board
in front of it. Built across Modules 1–3 of the AI-Assisted Coding course,
extended in the mid-course project, and wrapped in a delivery layer (CI,
Docker, documentation) in Module 4.

Tasks live in memory. There is no database, no authentication, and no
deployment — see [Limitations](#conventions-and-current-limitations).

**Branches**

| Branch | Contents |
|---|---|
| `main` | The Modules 1–3 baseline: CRUD API, status-transition rules, Kanban board, 24 tests. |
| `mid-course-project` | The baseline plus two features (below), 44 tests, and the Module 4 delivery layer. |
| `final-project` | The release check: verified baselines, CI, Docker, and the AI review and ownership evidence in `docs/`. **This is the branch to review.** |

## Final Project

Branch reviewed: `final-project`

### What this submission demonstrates

- The existing Task Tracker still runs inside the intended course scope — no
  new product features, and `app/` and `frontend/` are unchanged on this branch.
- CI runs the pytest suite on push and on pull requests to `main`.
- The Docker image builds and runs, with `/health` returning 200 and the
  container running as the non-root user `app`.
- AI review, security and ownership evidence lives in `docs/`.

### How to run locally

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env             # Linux/macOS: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Then, in a second terminal, for the board:

```
python -m http.server 5500 --bind 127.0.0.1
```

and open <http://localhost:5500/frontend/index.html>.

### How to run tests

```
pytest -v
```

### How to run with Docker

```
docker build -t task-tracker:dev .
```

```
docker run -d --name tt-dev -p 8000:8000 task-tracker:dev
```

```
curl.exe http://127.0.0.1:8000/health
```

```
docker exec tt-dev whoami
```

`whoami` must print `app`. Clean up with `docker rm -f tt-dev`.

### Evidence files

- [`docs/release-evidence.md`](docs/release-evidence.md) — baselines, CI,
  Docker and the claim-vs-reality log.
- [`docs/final-ai-review.md`](docs/final-ai-review.md) — AI code review and
  security grading, the manual check, the rejected suggestion, and the
  ownership statement.
- [`docs/ai-playbook.md`](docs/ai-playbook.md) — my rules for working with AI.

### AI assistance summary

AI helped draft or review: CI, Docker, documentation, docstrings, the security
review and the code review. I verified the work by running the test suite
before and after every change, reading each diff, building and running the
container, checking `/health` and `whoami`, exercising the documented endpoints
against a live server, and doing my own manual scan of the repository
configuration. One AI suggestion I rejected: a Medium-severity stored-XSS
finding on two `innerHTML` lines in `frontend/index.html` that turned out to
assign constant strings — every task-derived value already goes through
`textContent`, so I graded it a false positive and changed nothing.

## Prerequisites

- **Python 3.14** — the version this project is built and verified on
  (`python --version` should print `3.14.x`).
- **git**.
- **Docker** — only if you want to run the container section. Not needed for
  local development or tests.

## Local setup

From the project root (`task-tracker/`):

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
cp .env.example .env
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

`requirements.txt` pins the four runtime dependencies (FastAPI 0.141.1,
Uvicorn 0.52.4, Pydantic 2.13.4, python-dotenv 1.2.3).
`requirements-dev.txt` includes those plus the test-only dependencies
(pytest 9.1.1, httpx 0.28.1 — `fastapi.testclient` needs httpx).
`requirements.lock.txt` records the resolved **runtime** tree from `pip freeze`;
it does not include the test-only packages.

Install `requirements.txt` alone if you only want to run the app;
`requirements-dev.txt` if you want to run the tests.

### Environment variables

| Variable  | Default       | Purpose                                      |
|-----------|---------------|----------------------------------------------|
| `PORT`    | `8000`        | Port the server listens on                    |
| `APP_ENV` | `development` | Environment name; enables auto-reload locally |

`.env` is git-ignored; `.env.example` is committed as the template.

## Run the app locally

```
uvicorn app.main:app --reload --port 8000
```

The server runs at <http://127.0.0.1:8000>. `backend/main.py` re-exports the
same application object, so `uvicorn backend.main:app --reload --port 8000`
is equivalent.

Check it is alive:

```
curl http://127.0.0.1:8000/health
```

On Windows PowerShell, `curl` is an alias for `Invoke-WebRequest` — call the
real binary instead:

```
curl.exe http://127.0.0.1:8000/health
```

Expected — HTTP 200 with a body of this shape (the timestamp changes on every
request):

```json
{
  "status": "ok",
  "timestamp": "2026-08-26T09:15:42.123456+00:00"
}
```

### Run the frontend

The board is a single static file. Serve it over HTTP, **not** with `file://` —
the API only accepts the origins listed in `ALLOWED_ORIGINS` in `app/main.py`,
and a `file://` page sends `Origin: null`.

From the project root, in a second terminal:

```
python -m http.server 5500 --bind 127.0.0.1
```

Then open <http://localhost:5500/frontend/index.html> with the API running.
Allowed origins are `http://localhost:5500`, `http://127.0.0.1:5500`,
`http://localhost:8080` and `http://127.0.0.1:8080`; any other port has to be
added to `ALLOWED_ORIGINS` first.

The board has three status columns with counts, cards sorted High → Medium →
Low, loading/ready/empty/error states with a Retry action, drag-and-drop that
PATCHes the API and rolls the card back when the server rejects the transition,
and a create/edit modal with title trimming and visible server validation
messages.

## Run tests

```
pytest -v
```

`pytest.ini` puts the repository root on `sys.path`, so the bare command works
from a clean checkout.

**44 passing** — 24 from Modules 1–3 (`tests/test_tasks.py`) and 20 from the
mid-course project (`tests/test_midcourse.py`). Three
`StarletteDeprecationWarning`s are expected; they are triaged in
[`docs/warnings_note.md`](docs/warnings_note.md).

Run one group at a time with `-k`:

```
pytest -q -k "overdue"
```

## Run with Docker

From the project root, with the Docker daemon running:

```
docker build -t task-tracker:dev .
```

```
docker run -d --name tt-dev -p 8000:8000 task-tracker:dev
```

Verify it works and that it is not running as root:

```
curl.exe http://127.0.0.1:8000/health
```

```
docker exec tt-dev whoami
```

`whoami` must print `app`. Stop and remove the container with:

```
docker rm -f tt-dev
```

The image is a two-stage build on `python:3.14-slim`: the builder installs
`requirements.txt` into a virtualenv, and the runtime stage copies only that
virtualenv and `app/`, then switches to the non-root user `app` before `CMD`.
The container command is `uvicorn app.main:app`, with no `--reload`, bound to
`0.0.0.0:8000`. `backend/` is **not** in the image, so the
`uvicorn backend.main:app` alias works locally but not inside the container.
Tests, docs, the frontend, `.env` and `.git` are excluded by `.dockerignore`
and never enter the build context. The reasoning is in
[`docs/decisions/dockerfile-design.md`](docs/decisions/dockerfile-design.md).

## CI workflow

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push to
any branch and on pull requests to `main`. One job, `test`, on
`ubuntu-latest`:

1. `actions/checkout@v4`
2. `actions/setup-python@v5` pinned to Python **3.14**, with pip caching
3. `python -m pip install --upgrade pip` and `pip install -r requirements-dev.txt`
4. `pytest -v`

There is no `continue-on-error`, no `|| true`, no `--exit-zero` and no pipe
around pytest, so a failing test fails the job. There are no deployment steps.

## Project structure

```
task-tracker/
├── .github/workflows/ci.yml   # CI: install and run pytest on push and PR
├── app/
│   ├── main.py                # FastAPI app instance, CORS, and routes
│   ├── models.py              # Enums and the three Pydantic models
│   ├── storage.py             # In-memory task store and the query filters
│   ├── business_rules.py      # Status transition rules
│   └── due_dates.py           # Overdue rule (mid-course Feature 1)
├── backend/
│   ├── main.py                # Thin re-export of app.main:app
│   └── data/                  # Reserved for a SQLite file; no database code exists
├── frontend/
│   └── index.html             # Kanban board — vanilla HTML, CSS and JavaScript
├── tests/                     # pytest suite
├── docs/                      # Module deliverables and verification records
│   ├── decisions/             # Technical notes and design plans
│   ├── module4/               # Module 4 evidence logs
│   └── midcourse/             # Mid-course project documentation
├── Dockerfile                 # Multi-stage build, non-root runtime
├── .dockerignore
├── CLAUDE.md                  # Project memory for Claude Code
├── AGENTS.md                  # Repo-level instructions for coding agents
├── pytest.ini                 # Test config: repo root on sys.path, testpaths
├── requirements.txt           # Runtime dependencies, pinned
├── requirements-dev.txt       # Runtime + test dependencies
├── requirements.lock.txt      # Full resolved tree from `pip freeze`
├── .env.example
└── .gitignore
```

## API

| Method | Path | Success | Notes |
|---|---|---|---|
| `GET` | `/health` | 200 | Liveness probe with a UTC timestamp |
| `POST` | `/tasks` | 201 | 422 on a blank/over-long title, bad enum, bad date, or unknown field |
| `GET` | `/tasks` | 200 | Filters: `status`, `priority`, `assignee`, `search`, `overdue` — combined with AND |
| `GET` | `/tasks/{task_id}` | 200 | 404 when the id is unknown |
| `PATCH` | `/tasks/{task_id}` | 200 | 404 for an unknown id; 422 for a rejected status transition |
| `DELETE` | `/tasks/{task_id}` | 204 | Empty body; 404 when the id is unknown |

FastAPI generates interactive documentation from the same source:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

## Mid-course project features

### Feature 1 — Due dates and overdue tasks

Every task takes an optional `due_date` (ISO `YYYY-MM-DD`). The API returns a
derived `is_overdue` flag and the card shows a red **Overdue** pill for late
work or a neutral **Due** pill otherwise.

A task is overdue when it has a due date, that date is strictly in the past
(UTC), and its status is not `Done`. The rule lives in `app/due_dates.py` and
is recomputed on every read, so a task becomes overdue on its own as the date
passes. Filter with the **Overdue only** checkbox, or directly:

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

Filtering happens on the server, so the column counts always match what the API
returned.

## Conventions and current limitations

**Conventions**

- Routes delegate, storage holds state, business rules live in their own pure
  modules. Storage returns `None` for "not found"; the route layer turns that
  into a 404.
- Validation happens in Pydantic. All three models set `extra="forbid"`, so an
  unknown field is a 422 rather than a silent no-op.
- Allowed status transitions: `ToDo→InProgress`, `InProgress→Done`,
  `Done→InProgress`. Everything else — including same-to-same — is 422.
- Derived values (`is_overdue`) are recomputed on read, never stored.
- The frontend builds cards with `createElement` and `textContent`, never
  `innerHTML` for task data.

**Limitations**

- **No persistence.** Tasks are held in a module-level dict and are lost when
  the server restarts. `backend/data/` is reserved for a SQLite file, but no
  database code exists.
- **No authentication or authorization.** Every route is open. This is a
  deliberate course-scope decision, not an oversight — see
  [`docs/security-review.md`](docs/security-review.md).
- **Not production-ready and not deployed.** The container runs the app; there
  is no deployment pipeline, no TLS, no rate limiting and no process manager.
- **CORS is localhost-only** by design.
- Also out of scope for the mid-course features: recurring due dates,
  reminders, saved filter presets, sorting by due date, bulk edits, and
  persisting filter state in the URL. Reasoning in
  [`docs/midcourse/mini-adr.md`](docs/midcourse/mini-adr.md).

## Documentation

- [`docs/release-evidence.md`](docs/release-evidence.md) — final project:
  baselines, CI, Docker and the claim-vs-reality log.
- [`docs/final-ai-review.md`](docs/final-ai-review.md) — final project: AI
  review and security grading, manual check, and ownership statement.
- [`docs/ai-playbook.md`](docs/ai-playbook.md) — my rules for working with AI.
- [`docs/decisions/dockerfile-design.md`](docs/decisions/dockerfile-design.md) —
  technical note: why the container is built this way.
- [`docs/decisions/comments-feature-plan.md`](docs/decisions/comments-feature-plan.md) —
  design plan for a comments feature (planned, not implemented).
- [`docs/module4/`](docs/module4/) — CI, Docker, documentation-audit and AI
  review evidence for Module 4.
- [`docs/midcourse/`](docs/midcourse/) — user stories, mini-ADR, prompt log,
  verification and reflection for the mid-course project.
- [`docs/architecture.md`](docs/architecture.md) — one-page architecture
  overview.
- [`docs/security-review.md`](docs/security-review.md) — graded security review.
