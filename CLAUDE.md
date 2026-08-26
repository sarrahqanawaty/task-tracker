# CLAUDE.md — Task Tracker

Project memory for Claude Code. Corrected by hand after `/init`; the generated
draft is listed at the bottom under "What I changed from the generated draft".

## 1. Tech stack

| Item | Version | Where I verified it |
|---|---|---|
| Python | **3.14.0** | `.venv/Scripts/python --version`; `README.md` says "verified on Python 3.14"; `__pycache__` files are tagged `cpython-314` |
| FastAPI | 0.141.1 | `requirements.txt` |
| Pydantic | 2.13.4 (v2 API: `ConfigDict`, `field_validator`, `model_dump`) | `requirements.txt`, `app/models.py` |
| Uvicorn | 0.52.4 (`uvicorn[standard]`) | `requirements.txt` |
| python-dotenv | 1.2.3 | `requirements.txt`, `load_dotenv()` in `app/main.py` |
| pytest | 9.1.1 | `requirements-dev.txt` |
| httpx | 0.28.1 | `requirements-dev.txt` — required by `fastapi.testclient` |
| Frontend | vanilla HTML/CSS/JS, one file, no build step | `frontend/index.html` |

**Note on the Python version:** the course materials say Python 3.11. This repo
is actually built and verified on **3.14**, so 3.14 is what CLAUDE.md, the CI
workflow and the Dockerfile all pin. Changing it to 3.11 would make the
documentation disagree with the project.

## 2. Run command

```
uvicorn app.main:app --reload --port 8000
```

`backend/main.py` re-exports the same app object, so
`uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000` (the command in
`README.md`) is equivalent. In the container the command has no `--reload` and
binds to `0.0.0.0`.

## 3. Test command

```
pytest -v
```

Currently **44 passed** (24 from Modules 1–3 in `tests/test_tasks.py`, 20 from
the mid-course project in `tests/test_midcourse.py`). Three
`StarletteDeprecationWarning`s are expected and documented in
`docs/warnings_note.md` — they are not failures.

## 4. Architecture

```
app/
  main.py           FastAPI instance, CORS, the six routes, uvicorn entry point
  models.py         TaskStatus, TaskPriority, TaskCreate, TaskUpdate, TaskResponse
  storage.py        in-memory _tasks dict, CRUD, filter chain, _stamp_overdue, _reset
  business_rules.py VALID_TRANSITIONS + validate_status_transition
  due_dates.py      is_task_overdue — pure, imports nothing from the app
backend/
  main.py           thin re-export of app.main:app
  data/             reserved for a SQLite file; empty, no database code exists
frontend/
  index.html        the whole Kanban board
tests/
  conftest.py       client + created_task fixtures, autouse storage._reset()
  test_tasks.py     Modules 1–3 suite
  test_midcourse.py due dates, overdue, search, combined filters
docs/               module deliverables
```

Layering rule: **routes delegate, storage holds state, rules live in their own
pure modules.** Storage returns `None` for "not found"; the route layer turns
that into `HTTPException(404)`. `business_rules.py` is the only non-route module
that raises HTTP.

## 5. Business rules (as implemented, not as imagined)

- **Statuses:** `ToDo`, `InProgress`, `Done` (`app/models.py`, `TaskStatus`).
- **Priorities:** `Low`, `Medium`, `High`; default `Medium`.
- **Allowed transitions** (`app/business_rules.py`): `ToDo→InProgress`,
  `InProgress→Done`, `Done→InProgress`. **Everything else is 422**, including
  same-to-same (`ToDo→ToDo`) and `Done→ToDo`. The `detail` string lists the
  allowed transitions.
- The transition rule runs **only when the PATCH body contains `status`**, and
  the task is looked up **first**, so a missing id is 404 and not a rule error.
- **Title:** stripped, non-blank, max 200 characters.
- **Unknown fields:** all three models use `extra="forbid"` → 422.
- **`due_date`:** optional ISO `YYYY-MM-DD`, parsed by Pydantic. Sending
  `"due_date": null` clears it; omitting the key leaves it untouched
  (`model_dump(exclude_unset=True)` in `storage.update_task`).
- **Overdue** (`app/due_dates.py`): has a due date **and** that date is strictly
  before today (UTC) **and** status is not `Done`. Recomputed on every read by
  `storage._stamp_overdue`; never stored.
- **Filters** (`storage.get_all_tasks`): `status`, `priority`, `assignee`,
  `search`, `overdue` combine with **AND**; an omitted filter is not applied; a
  blank or whitespace-only `search`/`assignee` means *no filter*, never *match
  nothing*.
- **Status codes:** `POST /tasks` → 201, `DELETE /tasks/{id}` → 204 with no
  body, validation errors → 422, missing task → 404.

## 6. UI states and CORS

- The board has explicit **loading / ready / empty / error** states, with a
  Retry action on the error state (`showBoardError`, `frontend/index.html`).
- Drag-and-drop PATCHes the API and **rolls the card back** when the server
  rejects the transition.
- The modal omits `status` from the PATCH body when it did not change —
  otherwise a same-to-same transition would 422 every edit. Do not "simplify"
  this away; `docs/module3_debug_log.md` is the record of that bug.
- Cards are built with `createElement` + `textContent`. **Never `innerHTML`**
  for task data.
- **CORS** (`app/main.py`): four explicit origins —
  `http://localhost:5500`, `http://127.0.0.1:5500`, `http://localhost:8080`,
  `http://127.0.0.1:8080`. No wildcard, no credentials, methods limited to
  `GET, POST, PATCH, DELETE, OPTIONS`, headers limited to `Content-Type`.
  Serving the frontend from any other port requires adding that origin first.

## 7. Do-not rules

- Do not add authentication, a database, or deployment steps without asking.
  They are deliberately out of scope (`README.md`).
- Do not change `VALID_TRANSITIONS` or the overdue rule to make a test pass.
- Do not weaken or delete a test to turn it green — fix the source or the
  example (`docs/midcourse/prompt-log.md`).
- Do not add runtime dependencies. Test-only dependencies go in
  `requirements-dev.txt`, never in `requirements.txt`.
- Do not touch `.env` or commit it, and do not print its contents.
- Do not restructure `frontend/index.html`'s sorting, drag-and-drop, or modal
  dismissal behaviour — it is pinned by `docs/module3_behavior_contract.md`.
- Show me the diff before applying file changes.

## What I changed from the generated draft

| Generated draft said | Corrected to | Why |
|---|---|---|
| No Python version at all | Python 3.14.0, with evidence | Without it, a generated Dockerfile picks whatever `python:latest` is that week |
| Listed the run command as `uvicorn backend.main:app` only | Both, with `app.main:app` as the primary | `backend/main.py` is a re-export; the real app object lives in `app/main.py` |
| "In-memory storage, not a database" | Same, plus the note that `backend/data/` exists but holds no database code | The empty folder looks like an implemented feature |
| No test dependencies | pytest and httpx, called out as test-only | CI cannot run `pytest` from `requirements.txt` alone; `TestClient` needs `httpx` |
| Business rules summarised as "status transitions are validated" | The full matrix, including that same-to-same is rejected and that the rule only runs when `status` is present | "Validated" is the kind of sentence that sounds correct and teaches nothing |
