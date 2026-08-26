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
python -m pytest -q                                          # 44 passed
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
python -m http.server 5500 --bind 127.0.0.1                  # then open /frontend/index.html
```

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

## 4. Module 5 guardrails

- Docs-first: Module 5 output belongs in `docs/`.
- Read-only by default. Do not modify `app/`, `backend/`, `frontend/` or
  `tests/` during Module 5 unless I explicitly approve one specific minimal fix.
- One bounded task per thread.
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

## Assumptions to verify

- Python 3.14 is inferred from `README.md` and the `__pycache__` tags, not from
  a `python-requires` declaration — there is no `pyproject.toml` in the repo.
- There is no `docker-compose` file in this repository. The `Dockerfile` and
  `.github/workflows/ci.yml` are Module 4 artefacts; both are read-only for
  Module 5 work.
