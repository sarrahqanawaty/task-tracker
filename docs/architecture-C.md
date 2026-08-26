# Architecture — Task Tracker (Strategy C: targeted context)

> Strategy C of my context experiment. Same task again, but restricted to
> exactly three files — `app/main.py`, `app/models.py`, `app/storage.py` — with
> a standing instruction to mark anything not visible in them instead of
> inferring it. Left untouched, like the other two.

## 1. What the app does

A REST API for tracking tasks. It exposes a health check and five task routes:
create, list with filters, get one, partially update, delete. Tasks are held in
a module-level dictionary in `app/storage.py`, so they exist only for the life
of the process.

## 2. Data model

One entity in three models — `TaskCreate`, `TaskUpdate`, `TaskResponse`, all
with `extra="forbid"`.

- `id` (str, UUID4 from `storage.add_task`), `title` (required, stripped,
  non-blank, max 200), `description` (str, `""` when omitted), `status`
  (`ToDo`/`InProgress`/`Done`, default `ToDo`), `priority`
  (`Low`/`Medium`/`High`, default `Medium`), `assignee` (optional str),
  `due_date` (optional `date`), `is_overdue` (bool, derived), `created_at` and
  `updated_at` (UTC datetimes set in storage).
- `TaskUpdate` makes every field optional; `storage.update_task` uses
  `model_dump(exclude_unset=True)`, so an omitted key is untouched while an
  explicit `null` clears the value.

## 3. Request flow — creating a task

`POST /tasks` → CORS middleware (four allowed localhost origins) → FastAPI
validates the body into `TaskCreate` → `create_task` calls `storage.add_task` →
a UUID and one UTC timestamp are generated for both `created_at` and
`updated_at` → the task is stored in `_tasks` → `_stamp_overdue` returns a copy
with `is_overdue` recomputed → 201 with `TaskResponse`.

## 4. Key files

| File | Role | How I know |
|---|---|---|
| `app/main.py` | App instance, CORS, six routes, uvicorn entry point | read |
| `app/models.py` | Enums, three models, shared title validator | read |
| `app/storage.py` | `_tasks` dict, CRUD, filter chain, `_stamp_overdue`, `_reset` | read |
| `app/business_rules.py` | Provides `validate_status_transition`, called from the PATCH route | imported by `app/main.py`; contents **not visible from the files I read** |
| `app/due_dates.py` | Provides `is_task_overdue(due_date, status)` | imported by `app/storage.py`; contents **not visible from the files I read** |
| `.env` | Read via `load_dotenv()`; supplies `PORT` and `APP_ENV` | referenced in `app/main.py`; contents not visible |

Test files, frontend files and any other module are **not visible from the
files I read**.

## 5. Conventions

- Routes are thin: `create_task`, `list_tasks`, `get_task`, `delete_task` are
  one to three lines and delegate to `storage`.
- Storage signals "not found" by returning `None`; the route turns it into
  `HTTPException(404, f"Task with id {task_id} not found")`. HTTP status codes
  live in the route layer, not in storage.
- PATCH checks the transition rule only when `payload.status is not None`, and
  looks the task up first so a missing id returns 404 rather than a rule error.
- `is_overdue` is never stored: `_stamp_overdue` returns a `model_copy` on every
  read path.
- Filters combine with AND; a whitespace-only `search` or `assignee` is treated
  as no filter at all.
- Configuration comes from environment variables with defaults
  (`PORT`, `APP_ENV`); `APP_ENV == "development"` enables uvicorn reload.

## 6. Not visible / assumptions

- **The overdue rule itself** — `app/due_dates.py` was not in my file set, so I
  can say `is_overdue` is derived but not what makes a task overdue.
- **The transition matrix** — which status changes are legal is decided in
  `app/business_rules.py`, not visible from the files I read.
- **Tests** — none read; I cannot say what is covered.
- **The frontend** — `app/main.py` names four allowed origins on ports 5500 and
  8080, which implies a browser client served locally, but I have not seen it.
- **Dependencies, run commands, deployment, persistence plans** — not visible
  from the files I read.

---

**Files read:** `app/main.py`, `app/models.py`, `app/storage.py`.

**What narrowing the file set cost me:** the two rules that give the app its
behaviour both live one import away, so this draft describes the plumbing
accurately and the *policy* not at all. It also says nothing about test
coverage, the board, or how the project is meant to be run — which is most of
what a new joiner needs on day one.
