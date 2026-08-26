# Architecture — Task Tracker (Strategy A: minimal context)

> Strategy A of my context experiment. I gave one line — "create a concise
> architecture document for the Task Tracker app" — with no summaries, no
> `AGENTS.md` and no file list, and left the result untouched so the three
> strategies stay comparable.

## 1. What the app does

Task Tracker is a small REST API for creating, listing, updating and deleting
tasks, with a browser-based Kanban board in front of it. Tasks carry a status,
a priority, an optional assignee and an optional due date, and the board shows
them in three columns so a user can drag a card from one status to the next.

## 2. Data model

One entity, `Task`:

| Field | Type | Notes |
|---|---|---|
| `id` | string | UUID, server-generated |
| `title` | string | required, trimmed, max 200 |
| `description` | string | optional, defaults to `""` |
| `status` | enum | `ToDo`, `InProgress`, `Done` |
| `priority` | enum | `Low`, `Medium`, `High`, default `Medium` |
| `assignee` | string or null | optional |
| `due_date` | date or null | optional ISO date |
| `is_overdue` | bool | derived, recomputed on read |
| `created_at` / `updated_at` | datetime | UTC, server-generated |

It is represented by three Pydantic models — `TaskCreate`, `TaskUpdate` and
`TaskResponse` — following the usual FastAPI split between input and output
schemas.

## 3. Request flow — creating a task

1. The browser POSTs JSON to `/tasks`.
2. CORS middleware checks the origin against a list of allowed local origins.
3. FastAPI parses the body into `TaskCreate`; Pydantic rejects a blank title, an
   unknown enum value or an unknown field with 422 before the handler runs.
4. `create_task` calls `storage.add_task`, which generates a UUID and the
   `created_at` / `updated_at` timestamps and persists the task.
5. The stored task is stamped with a freshly computed `is_overdue` and returned
   as `TaskResponse` with HTTP 201.

## 4. Key files

| File | Role |
|---|---|
| `app/main.py` | FastAPI instance, CORS configuration, all six routes |
| `app/models.py` | Enums and the three Pydantic models |
| `app/storage.py` | Persistence layer and the query filters |
| `app/business_rules.py` | The status-transition matrix |
| `app/due_dates.py` | The overdue rule as a pure function |
| `backend/main.py` | Re-export so `uvicorn backend.main:app` works |
| `backend/data/` | Location of the SQLite database file |
| `frontend/index.html` | The Kanban board — HTML, CSS and JavaScript in one file |
| `tests/` | pytest suite covering the routes and the rules |

## 5. Conventions

- **Validation** happens in Pydantic, not in hand-written checks; the API
  answers 422 with FastAPI's standard error shape.
- **Persistence** is SQLite, stored under `backend/data/`, accessed through the
  storage layer so the routes never touch the database directly.
- **Business rules** live in their own modules rather than inside routes, so
  they can be unit-tested in isolation.
- **Derived values** such as `is_overdue` are computed on read rather than
  stored, so they cannot go stale.
- **Errors** use `HTTPException` with a `detail` string; the frontend reads
  `detail` and displays it.
- **Frontend/backend interaction** is plain `fetch` against a hardcoded API
  base URL, with no build step and no framework.

## 6. Not visible / assumptions

- There is a `Dockerfile`, but hosting and deployment are not described
  anywhere in the repository.
- There is no authentication layer; presumably it is planned for later.
- The exact test count and coverage were not verified for this draft.

---

**Files inspected:** `README.md`, `app/main.py`, `app/models.py`,
`app/storage.py`, `frontend/index.html` (skimmed).
