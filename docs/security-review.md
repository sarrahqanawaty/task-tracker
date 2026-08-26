# Security Review — Module 5

**Repo:** task-tracker, branch `mid-course-project`
**Mode:** read-only audit. No file under `app/`, `backend/`, `frontend/` or
`tests/` was modified for this review.
**Date:** 2026-08-26

Section 1 is what the audit returned, unedited. The **Grade** and **Reason**
columns are mine, added afterwards. Grades use the Module 5 rubric:

- **Valid** — a real issue in this repo, or a course-scope limitation that
  would matter outside the learning context.
- **False Positive** — wrong about the actual code, severity, or behaviour.
- **Noise** — technically true but too generic or trivial to become an action
  item at this project's scope.

---

## 1. AI findings, graded

| ID | Severity | File / location | Finding | Evidence | Suggested next step | Confidence | **Grade** | **Reason (mine)** |
|---|---|---|---|---|---|---|---|---|
| S1 | Medium | `app/models.py:63`, `:66`, `:101`, `:104` | `description` and `assignee` accept strings of unbounded length on both create and update. | `title` is capped at 200 chars by `_validate_title` (`app/models.py:47`); `description: Optional[str] = ""` and `assignee: Optional[str] = None` carry no constraint at all. | Add `max_length` to both fields in `TaskCreate` and `TaskUpdate`. | High | **Valid** | Confirmed by reading the model. The asymmetry is the tell: the author knew to bound `title`, so the two unbounded fields are an oversight, not a decision. A 10 MB description is accepted today and stored forever. |
| S2 | High (production) / course-scope | `app/main.py:70–223` | No authentication or authorization on any route. Any caller can read, modify or delete any task. | All six routes are plain `@app.get/post/patch/delete` with no dependency, no API key, no session. | Keep as a documented scope decision; require auth before any non-localhost deployment. | High | **Valid** | Valid, but as a *scope* finding, not a defect. `README.md:295` lists authentication as intentionally excluded, and the app binds to `127.0.0.1`. It stays on the list because the moment this leaves localhost it becomes the highest-severity item in the file. |
| S3 | Medium | `app/main.py:70` + `app/storage.py:8`, `:56` | Unauthenticated `POST /tasks` writes into a process-global dict with no size limit and no rate limit. | `_tasks: dict[str, TaskResponse] = {}` at module scope; `add_task` inserts unconditionally. Combined with S1, one client can grow the process until it is killed. | Bound the field lengths first (S1); note the missing rate limit as a deployment prerequisite. | Medium | **Valid** | Valid and it is the finding I did not reach on my own. It is really S1 × S2 compounded: unbounded field × unauthenticated write × unbounded store. Fixing S1 turns this from "trivial" into "needs volume". |
| S4 | Low | `app/main.py:161`, `:197`, `:201`, `:223` | The 404 body reflects the client-supplied `task_id` verbatim: `f"Task with id {task_id} not found"`. | Same f-string in all four 404 raises. `tests/test_tasks.py:69` asserts on it. | Return a fixed message, or echo only a validated UUID. | Medium | **Valid** | Valid at Low. Nothing is leaked *about the server* — the value came from the caller — so this is not information disclosure. It is an untrusted string on an API response path, which matters for the reason in M3 below. |
| S5 | Low | `app/main.py:25` | `PORT = int(os.getenv("PORT", "8000"))` raises `ValueError` at import time if `PORT` is not numeric — the app fails to start. | Line 25, no `try` and no validation. | Validate the env var or fall back to the default. | High | **Noise** | True, but not security. `PORT` is set by whoever starts the process, not by a request; the failure is loud, immediate, and local. Nothing to act on at this scope. |
| S6 | Low | `app/storage.py:142–173` | `update_task` is a read-modify-write across several statements with no lock, so two concurrent PATCHes on the same task can lose one update. | `existing = _tasks.get(...)` → `data.update(changes)` → `_tasks[task_id] = updated`, non-atomic. The routes are `def`, not `async def`, so Starlette runs them in a threadpool and true concurrency is possible. | Note it; it becomes a real design question when storage moves to SQLite. | Medium | **Valid** | Valid at Low, and I checked the claim that makes it real — the routes are sync, so they genuinely run on multiple threads. It is an integrity issue rather than a vulnerability, and it disappears with the database that `README.md:293` already plans. |
| S7 | Medium | `frontend/index.html:526`, `:531` | `innerHTML` is used when rendering board columns — task titles could inject markup (stored XSS). | Two `column.innerHTML = ...` assignments. | Replace with `textContent` / DOM construction. | Medium | **False Positive** | I opened both lines. `:526` assigns a constant empty-state literal and `:531` assigns `""` — neither touches task data. Every task-derived value is set with `textContent` (`:554` title, `:560` description, `:569` priority, `:577` due pill) and the cards are built with `createElement` (`:543`). The pattern matched; the data flow did not. |
| S8 | Low | `requirements.txt`, `requirements.lock.txt` | Dependencies are pinned but never scanned for known vulnerabilities. | Four pinned direct deps, a full lockfile, no scanning step. | Add `pip-audit` to CI. | Low | **Noise** | CI exists (`.github/workflows/ci.yml`), so this has somewhere to live — but a scanning step is a different piece of work from Module 5, and nothing in the audit points at a specific vulnerable version. The pinning and the lockfile are already the part that matters. |
| S9 | Low | `app/main.py:27–31` | Swagger UI, ReDoc and `openapi.json` are served publicly by default, exposing the full API surface. | `FastAPI(...)` with no `docs_url=None`. | Disable interactive docs in production. | Medium | **Noise** | True of every default FastAPI app, and the run command in `README.md:72` binds to `127.0.0.1`. The docs pages are also a *deliverable* of Modules 1–2 — turning them off would remove course evidence. Revisit only if this is ever deployed. |

**Files inspected:** `app/main.py`, `app/models.py`, `app/storage.py`,
`app/business_rules.py`, `app/due_dates.py`, `backend/main.py`,
`frontend/index.html`, `tests/conftest.py`, `tests/test_tasks.py`,
`tests/test_midcourse.py`, `requirements.txt`, `requirements.lock.txt`, `.env`,
`.env.example`, `.gitignore`, `README.md`, `AGENTS.md`, `CLAUDE.md`,
`Dockerfile`, `.dockerignore`, `.github/workflows/ci.yml`,
`requirements-dev.txt`.

**Categories with no issue found:**

- **CORS** — `app/main.py:36–48` lists four explicit localhost origins, with no
  wildcard, no `allow_credentials`, methods restricted to the five the board
  uses, and headers restricted to `Content-Type`. Clean.
- **Secrets** — `.env` contains only `PORT` and `APP_ENV`, and `git ls-files`
  confirms it is not tracked. No credentials, tokens or keys anywhere in the
  repo. Clean *today* — see M1.
- **Broad exception handling** — `grep -n except app/ backend/` returns
  nothing. There is no bare `except:` and no handler that swallows errors.
- **Enum / type handling** — `TaskStatus` and `TaskPriority` are `str` Enums
  validated by Pydantic, and all three models set `extra="forbid"`, so unknown
  fields and bad enum values are 422 before any code runs.
- **Container / CI** — `Dockerfile` builds on a pinned `python:3.14-slim`,
  creates the non-root user `app` and switches to it before `CMD`, and bakes in
  no secrets; `.dockerignore` keeps `.env`, `.env.*`, `.git` and the virtualenv
  out of the build context. `.github/workflows/ci.yml` pins Python 3.14 and has
  no `continue-on-error`, no `|| true`, no `--exit-zero` and no pipe around
  pytest. Clean, and the container half is
  backed by runtime evidence rather than reading: `whoami` returns `app`, and
  the image contains no `.env`, no `.git`, no tests and no test runner
  (`docs/module4/docker-verification.md`).

**Limits of this audit:** static reading only. Nothing was scanned at runtime,
no dependency CVE lookup was performed, and the frontend was reviewed for data
flow rather than executed.

---

## 2. My manual scan

Done with the AI output closed, reading `app/`, `.gitignore` and the tests
directly.

| ID | File / location | What I found | Why it matters |
|---|---|---|---|
| M1 | `.gitignore:14–16` | The ignore rules are `.env` and `.env.local` only. `.env.production`, `.env.staging` and `.env.dev` would all be committed. And `.env` is currently byte-identical to `.env.example` — there is no secret in it yet. | The safeguard is a filename match, not a rule. The day someone adds a real value, the protection depends on which of two spellings they picked. Fix: `.env*` plus `!.env.example`, verified with `git check-ignore -v .env.production`. |
| M2 | `app/business_rules.py:5–9` vs `app/main.py:205–223` | The transition matrix refuses `Done → ToDo` to protect workflow integrity — but `DELETE /tasks/{id}` is unrestricted and unauthenticated. You cannot walk a task backwards, and you can erase it entirely. | The rule that is enforced hardest is the one an attacker does not need. This is business context, not a pattern: the AI graded "no auth" globally and never connected it to the one rule the code works hardest to protect. |
| M3 | `app/main.py:161` + `frontend/index.html:833` | S4 is harmless *only because* `show()` uses `textContent`. The API's safety here rests on a convention in a different file, and no test asserts it. | The API is public and the board is not its only possible client. A second client that renders `detail` with `innerHTML` re-opens the hole without a single line of API code changing. |
| M4 | `app/due_dates.py:30`, `:63` | `is_task_overdue` compares against `today_utc()`. For a user at UTC+3, between 00:00 and 03:00 local the UTC date has not rolled over yet, so a task that was due yesterday on their calendar still shows as *not overdue*. | Not a vulnerability — a trust bug. The board's whole point is telling you what is late, and it is late by up to the size of the offset. No security scanner raises this because it is a business-time decision, not a pattern. |
| M5 | `app/main.py:36–48` vs `tests/` | `ALLOWED_ORIGINS` is a security control with zero test coverage. Widening it to `["*"]` leaves all 44 tests green. | The Break Test habit from Module 2 applies to controls, not only to features: a rule no test protects is a rule that can be deleted by accident. |

---

## 3. Reconciliation

| Agreement | AI-only | You-only |
|---|---|---|
| S1 — unbounded `description` / `assignee` | S3 — unbounded store growth via unauthenticated writes | M1 — `.gitignore` covers `.env` but not `.env.production` |
| S2 — no authentication on any route | S4 — 404 reflects the client-supplied id | M2 — `DELETE` bypasses the workflow the transition matrix protects |
| | S6 — non-atomic read-modify-write in `update_task` | M3 — the API's safety depends on a frontend convention no test enforces |
| | | M4 — overdue is decided in UTC, not in the user's day |
| | | M5 — `ALLOWED_ORIGINS` has no test coverage |

**Observation (two lines).** The AI is strong where the risk is visible in a
single file — a missing constraint, a global dict, a non-atomic write — and it
found the compound memory finding (S3) that I read past twice. Everything it
missed needed two files held together at once, or a rule about *this project*
rather than about Python: what the delete route means next to the transition
matrix, what UTC means to a person in Beirut, what an untested control is worth.

---

## 4. Top-3 security backlog

| Rank | Finding | Why it matters | Suggested owner | Next action |
|---|---|---|---|---|
| 1 | S1 — bound `description` and `assignee` | Smallest change with the largest effect: it is also the fix that defuses S3, and it is a two-field edit in one file. | Backend | Add `Field(max_length=...)` to both fields in `TaskCreate` and `TaskUpdate`, plus a test asserting 422 on an over-length description. Not applied in Module 5. |
| 2 | M1 — `.gitignore` env pattern | Cheapest irreversible mistake in the repo. `.env` holds nothing today, which is exactly why nobody will notice the gap until it holds something. | Project owner (me) | Replace `.env` / `.env.local` with `.env*` and `!.env.example`; verify with `git check-ignore -v .env.production`. |
| 3 | M5 — no test covers `ALLOWED_ORIGINS` | The one deliberate security control in the codebase is unprotected; a refactor can widen it to `*` and stay green. | Backend | Add one test that asserts a disallowed origin gets no `access-control-allow-origin` header. |

S2 (no auth) is deliberately not in the top three: it is a recorded scope
decision, not a backlog item, and it becomes rank 1 the day this app is
deployed anywhere other than `127.0.0.1`.

---

## 5. Optional one-line fix

Not taken. Prompt 5.2X is optional and Module 5 is documentation-first; S1 is
the natural candidate but it touches four field declarations plus a test, which
is a backlog item rather than a one-line fix. `app/` is unchanged and the suite
still reports `44 passed`.
