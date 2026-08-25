# Task Tracker API — Summary Checklist (Prompt O2)

Built from verified facts only: the files in this project and the verification
runs recorded below.

## 1. Models and enums

**Enums** — `app/models.py`

| Enum | Values |
|---|---|
| `TaskStatus` | `ToDo`, `InProgress`, `Done` |
| `TaskPriority` | `Low`, `Medium`, `High` |

**Models** — all three use `model_config = ConfigDict(extra="forbid")`, so an
unknown field is rejected with 422.

| Model | Purpose | Fields |
|---|---|---|
| `TaskCreate` | Request body for POST | `title` (required), `description` (default `""`), `status` (default `ToDo`), `priority` (default `Medium`), `assignee` (default `None`) |
| `TaskUpdate` | Request body for PATCH | all five fields optional |
| `TaskResponse` | Response body | `id`, `title`, `description`, `status`, `priority`, `assignee`, `created_at`, `updated_at` |

**Title rule:** whitespace is stripped; blank titles and titles over 200
characters (measured after stripping) are rejected with 422.

**Server-managed fields:** `id`, `created_at`, and `updated_at` are generated
inside `app/storage.py` and cannot be set by a client — they appear on
`TaskResponse` only.

**Storage** — `app/storage.py`, an in-memory `dict[str, TaskResponse]`. No
database, no ORM. State is lost on server restart.

## 2. Endpoints and status codes

| Method | Path | Success | Error cases |
|---|---|---|---|
| GET | `/health` | 200 | — |
| POST | `/tasks` | 201 Created | 422 — missing/blank/overlong title, invalid enum, unknown field |
| GET | `/tasks` | 200 | — (empty result is `[]` with 200, never 404) |
| GET | `/tasks/{task_id}` | 200 | 404 — `Task with id {task_id} not found` |
| PATCH | `/tasks/{task_id}` | 200 | 404 — missing task; 422 — invalid body or illegal transition |
| DELETE | `/tasks/{task_id}` | 204 No Content, empty body | 404 — missing task |

`GET /tasks` accepts two optional query parameters, `status` and `priority`,
which filter the list and can be combined.

## 3. Status transition rules

`app/business_rules.py` allows exactly three transitions:

| From | To |
|---|---|
| ToDo | InProgress |
| InProgress | Done |
| Done | InProgress |

Everything else returns 422 — including `ToDo -> Done`, `Done -> ToDo`, and
any same-to-same transition. **There is no route back to ToDo once a task
leaves it.**

Validation runs only when `status` is present in the PATCH body, so a
title-only PATCH is unaffected. A missing task returns 404 *before* the
transition rule is consulted.

## 4. Verification commands already passed

```
.\.venv\Scripts\python.exe -m tests.verify_a
```
8 of 8 PASS — model validation.

```
.\.venv\Scripts\python.exe -m tests.verify_transitions
```
`200, 200, 422, 200, 422, 200` — matches the expected pattern.

```
.\.venv\Scripts\python.exe -m pytest -q
```
17 passed, 2 warnings.

```
curl.exe -i http://127.0.0.1:8000/health
```
`HTTP/1.1 200 OK`.

Swagger UI at `http://127.0.0.1:8000/docs` lists all six routes.

## 5. Break Test proof

Commenting out `validate_status_transition(...)` in the PATCH route produced:

```
2 failed, 15 passed
FAILED test_patch_invalid_transition_todo_to_done_returns_422
FAILED test_patch_same_status_returns_422
```

Both failed on `assert 200 == 422` — the tests detected the missing rule rather
than passing regardless. Restoring the line returned the suite to 17 passed.
Full record in `docs/break_test.md`.

---

**Not part of this build:** authentication, a database or ORM, a frontend,
Docker, and deployment.
