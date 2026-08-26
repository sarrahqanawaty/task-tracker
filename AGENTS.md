# AGENTS.md — Task Tracker

Repo-level instructions for coding agents working in this repository.

## 1. Project summary

A minimal REST API for tracking tasks (`app/`), with a single-file vanilla
JavaScript Kanban board in front of it (`frontend/index.html`). Tasks live in
an in-memory dictionary — there is no database and nothing survives a server
restart. Built across Modules 1–3 of the AI-Assisted Coding course and extended
on the `mid-course-project` branch with due dates/overdue and search/combined
filters.

## 2. Tech stack and commands

| Item | Value | Evidence |
|---|---|---|
| Language | Python 3.14 | `README.md`, `.pyc` files are `cpython-314` |
| Web framework | FastAPI 0.141.1 | `requirements.txt`, `app/main.py` |
| Validation | Pydantic 2.13.4 | `requirements.txt`, `app/models.py` |
| Server | Uvicorn 0.52.4 | `requirements.txt`, `app/main.py` |
| Config | python-dotenv 1.2.3 | `app/main.py` calls `load_dotenv()` |
| Persistence | in-memory `dict` in `app/storage.py` | `_tasks: dict[str, TaskResponse] = {}` |
| Frontend | one static HTML file, no build step | `frontend/index.html` |

Commands that actually work in this repo:

```
pytest -v                                       # 44 passed
uvicorn app.main:app --reload --port 8000       # API on http://127.0.0.1:8000
python -m http.server 5500 --bind 127.0.0.1     # then open /frontend/index.html
docker build -t task-tracker:dev .
docker run -d --name tt-dev -p 8000:8000 task-tracker:dev
```

`pytest.ini` puts the repository root on `sys.path`; without it only
`python -m pytest` works. `backend/main.py` re-exports the same app object, so
`uvicorn backend.main:app` is equivalent locally — but `backend/` is not in the
Docker image.

`SQLite` is named in `README.md` as the intended persistence layer and
`backend/data/` holds a `.gitkeep` for it, but **no database code exists** —
treat persistence as in-memory only.

## 3. Business rules visible in the code

- **Statuses**: `ToDo`, `InProgress`, `Done` (`app/models.py`, `TaskStatus`).
- **Priorities**: `Low`, `Medium`, `High`, default `Medium` (`TaskPriority`).
- **Status transitions** (`app/business_rules.py`): only `ToDo→InProgress`,
  `InProgress→Done`, `Done→InProgress` are allowed. Same-to-same is rejected.
  Anything else returns 422 with the allowed list in `detail`.
- **Title**: trimmed, non-blank, max 200 characters (`_validate_title`).
- **Unknown fields**: all three models use `extra="forbid"`, so an unknown key
  returns 422.
- **`due_date`**: optional ISO `YYYY-MM-DD`; Pydantic does the parsing. Sending
  `"due_date": null` clears it, omitting the key leaves it untouched
  (`exclude_unset` in `storage.update_task`).
- **Overdue** (`app/due_dates.py`): a task is overdue when it has a due date,
  that date is strictly before today (UTC), and its status is not `Done`. It is
  recomputed on every read by `storage._stamp_overdue`, never stored.
- **Filters** (`storage.get_all_tasks`): `status`, `priority`, `assignee`,
  `search`, `overdue` combine with AND; an omitted filter is not applied; a
  blank or whitespace-only `search`/`assignee` means *no filter*, never *match
  nothing*.
- **CORS** (`app/main.py`): four explicit localhost origins, no wildcard, no
  credentials.
- **Authentication**: none. `README.md` lists it as intentionally out of scope.

## 4. Working guardrails

- **Read first.** Inspect the relevant files before proposing anything, and
  show me the diff before applying a file change.
- **Docs-first.** Review, governance and evidence work belongs in `docs/`. That
  is where the output of a review task goes, not into the source tree.
- **Protect `app/` and `frontend/`.** Do not modify them, or `backend/` or
  `tests/`, unless I explicitly approve one specific small change — a bug fix,
  a security fix, or a documentation-supported correction. An unexpected edit
  to those directories is a diff I reject, not a diff I read twice. Any change
  that is made must be explained in `docs/final-ai-review.md`.
- **No new product features.** Comments, authentication, a production database
  and notifications are all out of scope. Say so instead of building them.
- One bounded task at a time.
- Cite the actual files you inspected when you make a claim about this repo.
- If a file is not visible or a fact is not confirmed, say so instead of
  guessing. "Not confirmed" is an acceptable answer; an invented one is not.

## 5. Security and governance reminders

- Do not paste or echo secrets. `.env` is git-ignored and currently holds only
  `PORT` and `APP_ENV`; keep it that way.
- Do not run destructive commands (no `git reset --hard`, no `git branch -M`,
  no deleting files) — the current branch is `mid-course-project` and it is the
  branch under review.
- Do not invent security findings to fill a table. If a category is clean, say
  it is clean.
- Do not weaken a test to make it pass. Fix the source or the example.
- Do not add runtime dependencies. Test-only dependencies go in
  `requirements-dev.txt`, never in `requirements.txt` — the Docker image
  installs the runtime file and must not ship a test runner.

## Assumptions to verify

- Python 3.14 is inferred from `README.md` and the `__pycache__` tags, not from
  a `python-requires` declaration — there is no `pyproject.toml` in the repo.
- There is no `docker-compose` file in this repository. The `Dockerfile` and
  `.github/workflows/ci.yml` exist and are verified; change them only with the
  same read-first, show-me-the-diff rule as the rest of the repo.
