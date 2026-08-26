# Release Evidence

Everything below is copied from commands I ran on this branch, not from
memory and not from earlier modules.

## Baseline

- **Branch:** `final-project`
- **Date:** 2026-08-26
- **Local app run command:** `uvicorn app.main:app --reload --port 8000`
- **`/health` result:**

  ```
  $ curl.exe -s -i http://127.0.0.1:8000/health
  HTTP/1.1 200 OK
  server: uvicorn
  content-type: application/json

  {"status":"ok","timestamp":"2026-08-26T17:05:07.198689+00:00"}
  ```

- **Frontend check:** served with `python -m http.server 5500 --bind 127.0.0.1`
  and opened at <http://localhost:5500/frontend/index.html>. The board renders
  the three columns (To Do / In Progress / Done) with the filter bar above
  them; clicking **+ New Task**, typing a title and pressing Save added the
  card to **To Do (1)** with `Medium`, `Unassigned` and an Edit button — so the
  create flow still reaches the API and the board re-renders from the response.
- **Test command:** `pytest -v`
- **Test result:** **44 passed, 3 warnings in 0.62s.** No failures. The three
  warnings are one `StarletteDeprecationWarning` raised from
  `app/main.py:198` (`HTTP_422_UNPROCESSABLE_ENTITY` renamed upstream),
  triaged in `docs/warnings_note.md` — pre-existing, cosmetic, not introduced
  by final-project work.

**Scope:** no product feature was added on this branch. `app/` and `frontend/`
are unchanged on `final-project`; the only source change in the whole delivery
layer was the Module 4 docstring pass, which added documentation and deleted
one line (the docstring it replaced).

## CI evidence

- **Workflow file:** `.github/workflows/ci.yml`
- **Latest run:** [run #7 — success](https://github.com/sarrahqanawaty/task-tracker/actions/runs/32993493231)
  on `final-project`, commit `06c6c4b` — the commit that carries this evidence
  file. The [run history for the branch](https://github.com/sarrahqanawaty/task-tracker/actions?query=branch%3Afinal-project)
  is green throughout; anything after #7 is a documentation-only commit.
- **Test command used by CI:** `pytest -v`, as the last step of the `test` job.
- **Dependency installation:** `python -m pip install --upgrade pip` then
  `pip install -r requirements-dev.txt`. The dev file is deliberate:
  `requirements.txt` holds only the four runtime dependencies, and
  `fastapi.testclient` needs `httpx`, so installing the runtime file alone
  cannot run a single test.
- **Python version:** pinned to `3.14`, not `3.x` and not "latest".
- **Shortcut check:**

  | Shortcut | Present? |
  |---|---|
  | `continue-on-error` | no |
  | `\|\| true` | no |
  | `--exit-zero` | no |
  | pytest skipped or replaced by a summary step | no — `run: pytest -v`, no pipe, no `tee` |
  | deployment steps | none |

- **Optional red-run evidence** (produced during Module 4, kept because it is
  the strongest proof the pipeline is real): the same workflow went
  [red on a broken assertion](https://github.com/sarrahqanawaty/task-tracker/actions/runs/32981499078)
  and [green again after the revert](https://github.com/sarrahqanawaty/task-tracker/actions/runs/32981688552).
  Full record in `docs/module4/ci-evidence.md`.

## Docker evidence

- **Build command:** `docker build -t task-tracker:dev .`
- **Run command:** `docker run -d --name tt-dev -p 8000:8000 task-tracker:dev`
- **`/health` check:**

  ```
  $ curl.exe -s -i http://127.0.0.1:8000/health
  HTTP/1.1 200 OK
  server: uvicorn
  content-type: application/json
  ```

- **Non-root check:**

  ```
  $ docker exec tt-dev whoami
  app
  ```

  The Dockerfile creates `app` (uid 10001) in the runtime stage and switches to
  it with `USER app` before `CMD`.
- **No-baked-secrets check:**

  ```
  $ docker exec tt-dev find / -maxdepth 3 \( -name ".env" -o -name ".git" -o -name "tests" \)
  (no output)

  $ docker exec tt-dev ls -a /app
  .  ..  app
  ```

  `.dockerignore` excludes `.env`, `.env.*` (with `!.env.example`), `.git`,
  `.github`, virtualenvs, caches, `tests`, `docs`, `frontend` and `backend`, so
  none of them enter the build context in the first place.
- **Runtime command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000` — no
  `--reload` in the container.
- **Health status:** `docker inspect --format "{{.State.Health.Status}}" tt-dev`
  → `healthy`, so the `HEALTHCHECK` instruction actually runs.
- **Image size:** 251 MB, two-stage build on `python:3.14-slim`.
- **Cleanup:** `docker rm -f tt-dev`.

## Documentation claim-vs-reality log

| Claim checked | Evidence used | Result | Change made, if any |
|---|---|---|---|
| README: "**44 passing**" from `pytest -v` | Ran `pytest -v` on this branch | **True.** `44 passed, 3 warnings in 0.62s` | None |
| README API table: `DELETE /tasks/{task_id}` → **204**, empty body | Live run: created a task, then `curl -X DELETE` against the running API | **True.** `status=204  body_bytes=0`, and a follow-up `GET` on the same id returned `404` with `{"detail":"Task with id 8c06134a-… not found"}` | None |
| README conventions: "Everything else — including same-to-same — is 422" for status transitions | Live run: `PATCH {"status":"Done"}` on a fresh `ToDo` task | **True.** `422` with `{"detail":"Invalid status transition from ToDo to Done. Allowed transitions: ['Done->InProgress', 'InProgress->Done', 'ToDo->InProgress']"}` | None |
| README: run the tests with `pytest -v` | The first CI run on a clean checkout | **False when written.** `pytest -v` failed with `ModuleNotFoundError: No module named 'app'`; only `python -m pytest` worked, because `tests/` has no `__init__.py` and plain `pytest` never puts the repo root on `sys.path` | **Fixed.** Added `pytest.ini` with `pythonpath = .` and `testpaths = tests`. No test and no application code changed; both invocations now report 44 passed |
| README: `docker exec tt-dev whoami` must print `app` | Ran it against the running container | **True.** Printed `app`; `id` confirms `uid=10001(app)` | None |

The fourth row is the one worth reading. It was not found by re-reading the
README — it was found by a machine that had never run this project, which is
the entire argument for having CI at all.
