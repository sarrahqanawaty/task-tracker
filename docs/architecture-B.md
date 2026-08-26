# Architecture — Task Tracker (Strategy B: structured context)

> Strategy B of my context experiment. Same task as A, but I supplied the full
> `AGENTS.md` plus a one-line summary of every file under `app/`, `backend/`,
> `frontend/` and `tests/`. Left untouched, like the other two.

## 1. What the app does

Task Tracker is a minimal REST API for tracking tasks, paired with a single-file
vanilla-JavaScript Kanban board. A user creates a task with a title, an optional
description, a priority, an optional assignee and an optional due date; the
board shows tasks in three status columns and moves them by dragging a card,
which PATCHes the API. The server decides which status moves are legal and
whether a task is overdue. Tasks live in an in-memory dictionary and are lost
when the server restarts — there is no database.

## 2. Data model

One entity, `Task`, expressed as three Pydantic models in `app/models.py`:
`TaskCreate` (input), `TaskUpdate` (partial input, every field optional) and
`TaskResponse` (output). All three set `extra="forbid"`.

| Field | Type | Rules |
|---|---|---|
| `id` | `str` | UUID4, generated in `storage.add_task` |
| `title` | `str` | required; stripped, non-blank, max 200 chars |
| `description` | `str` | optional on input, always a string on output (`""`) |
| `status` | `TaskStatus` | `ToDo` \| `InProgress` \| `Done`, default `ToDo` |
| `priority` | `TaskPriority` | `Low` \| `Medium` \| `High`, default `Medium` |
| `assignee` | `str \| None` | optional |
| `due_date` | `date \| None` | optional; Pydantic parses ISO `YYYY-MM-DD` |
| `is_overdue` | `bool` | derived; never sent by the client |
| `created_at`, `updated_at` | `datetime` | UTC, server-owned |

Two enums, `TaskStatus` and `TaskPriority`, are `str` Enums, which is what lets
`app/due_dates.py` compare `status == "Done"` without importing the models.

## 3. Request flow — creating a task

1. The board calls `fetch(API + "/tasks")` with a JSON body.
2. `CORSMiddleware` checks the `Origin` against the four allowed localhost
   origins in `app/main.py`; anything else is refused by the browser.
3. FastAPI validates the body against `TaskCreate`. A blank title, a bad enum
   value, a malformed date or an unknown field returns 422 before the handler
   runs — `extra="forbid"` and the `title` field validator do this work.
4. `create_task` (`app/main.py`) delegates immediately to `storage.add_task`;
   the route contains no logic of its own.
5. `add_task` generates `str(uuid4())` and a single `datetime.now(timezone.utc)`
   used for both `created_at` and `updated_at`, builds a `TaskResponse`, and
   stores it in the module-level `_tasks` dict.
6. Before returning, `_stamp_overdue` produces a copy with `is_overdue` freshly
   computed by `app/due_dates.is_task_overdue`.
7. FastAPI serialises the `TaskResponse` and answers 201.

## 4. Key files

| File | Role |
|---|---|
| `app/main.py` | FastAPI instance, CORS, the six routes, the uvicorn entry point |
| `app/models.py` | The two enums, the three Pydantic models, the shared title validator |
| `app/storage.py` | The `_tasks` dict, CRUD helpers, the filter chain, `_stamp_overdue`, `_reset` |
| `app/business_rules.py` | `VALID_TRANSITIONS` and `validate_status_transition`, which raises 422 |
| `app/due_dates.py` | `is_task_overdue` — a pure function importing nothing from the app |
| `backend/main.py` | Thin re-export so `uvicorn backend.main:app` keeps working |
| `frontend/index.html` | The whole board: markup, CSS, filter bar, modal, drag-and-drop |
| `tests/conftest.py` | `client` and `created_task` fixtures, plus an autouse `storage._reset()` |
| `tests/test_tasks.py` | Modules 1–3 suite: CRUD, transitions, PATCH edge cases |
| `tests/test_midcourse.py` | Mid-course suite: due dates, overdue, search and combined filters |

## 5. Conventions

- **Layering.** Routes delegate; storage holds state; rules live in their own
  pure modules. `app/main.py` is thin by design.
- **Validation at the edge.** Pydantic owns parsing and shape validation, so
  there is no hand-written date or enum handling anywhere in the app.
- **`extra="forbid"` everywhere.** An unknown field is a 422, not a silent
  ignore — and it is why a derived field cannot be added casually to
  `TaskResponse`.
- **Business rules raise HTTP.** `validate_status_transition` raises
  `HTTPException(422)` with the allowed transitions in `detail`; storage never
  raises HTTP and returns `None` for "not found" instead.
- **Derived on read.** `is_overdue` is recomputed by `_stamp_overdue` on every
  read path, so it cannot go stale as the calendar advances.
- **Filters combine with AND**, and a blank value means "no filter", never
  "match nothing".
- **Frontend.** No framework, no build step; cards are built with
  `createElement` and `textContent`, and API errors are rendered from `detail`.
- **Config.** `python-dotenv` loads `.env`; only `PORT` and `APP_ENV` exist, and
  `.env` is git-ignored.

## 6. Not visible / assumptions

- SQLite is named in `README.md` and `backend/data/` exists for it, but **no
  database code is present** — persistence is in-memory only.
- `Dockerfile`, `.dockerignore` and `.github/workflows/ci.yml` exist; I did
  not inspect them for this draft, so nothing here describes them.
- No authentication; `README.md` records it as an intentional scope decision.
- Python 3.14 is inferred from `README.md` and the `__pycache__` tags, not from
  a `pyproject.toml` — there is none.

---

**Which piece of context did the work:** the "Business rules visible in the
code" section of `AGENTS.md`. It supplied the transition matrix, the
blank-means-no-filter rule and the `exclude_unset` distinction with no file
reading at all, and it is also what kept the SQLite mistake out of this draft —
`AGENTS.md` says in so many words that no database code exists.

**What is still taken on trust here:** this draft restates `AGENTS.md` for the
business rules instead of re-deriving them from the code, so an error in
`AGENTS.md` would pass straight through. Only the request-flow section went back
to the source files.
