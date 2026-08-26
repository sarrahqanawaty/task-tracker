# AI Review Log — Module 4 delivery layer

Module 4, Part 4.5. The diff under review is the Module 4 work on
`mid-course-project`: `.github/workflows/ci.yml`, `Dockerfile`,
`.dockerignore`, `requirements-dev.txt`, `CLAUDE.md`, the README rewrite, and
the docstring additions across `app/`.

This is a triage exercise, not a trust exercise. Every comment below is
labelled **Useful**, **Noise**, or **Wrong**, with the reason and — for the
useful ones — what I actually did about it.

## Triage

| # | Comment summary | File / location | Severity | Bucket | Evidence found | Action |
|---|---|---|---|---|---|---|
| 1 | `.dockerignore` excludes `backend/`, but the README presents `uvicorn backend.main:app` as an equivalent run command. Inside the container that module does not exist. | `.dockerignore`, `README.md` | medium | **Useful** | `backend` is in the ignore list; the image only receives `app/`. The container `CMD` is `app.main:app`, so nothing is broken — but the README implied the alias works everywhere. | **Fixed.** The Docker section now says `backend/` is not in the image and the alias is local-only. |
| 2 | `requirements.lock.txt` no longer describes the environment the tests run in, now that pytest and httpx are installed from `requirements-dev.txt`. | `requirements.lock.txt`, `README.md` | low | **Useful** | The lockfile lists 19 runtime packages and no pytest, no httpx; the venv has both. | **Fixed.** The README now calls it the resolved *runtime* tree. |
| 3 | Nothing verifies that the runtime-only dependency set can actually import the app. CI installs `requirements-dev.txt`; the image installs `requirements.txt`. A runtime import error would only show up when the container is run. | `.github/workflows/ci.yml`, `Dockerfile` | medium | **Useful** | The two files genuinely install different sets, and no job builds the image. | **Backlogged**, not fixed. Recorded as an open question in `docs/decisions/dockerfile-design.md`; adding a `docker build` job is beyond this module's CI scope. |
| 4 | `ENV APP_ENV=production` in the Dockerfile has no effect: `APP_ENV` is only read inside the `if __name__ == "__main__"` block of `app/main.py`, which the container never executes because `CMD` calls uvicorn directly. | `Dockerfile` | low | **Noise** | True — I checked `app/main.py`. `APP_ENV` is also read at module import for the module-level constant, but only the `__main__` block uses it to set `reload`. | **No change.** It documents intent and costs nothing. Removing it would invite someone to add `--reload` back. |
| 5 | Documentation is inconsistent about the test command: `pytest -v` in the README and CI, `python -m pytest -q` in the older module docs. | `README.md`, `docs/` | low | **Noise** | Both commands exist across the docs, and both work. | **No change.** The older docs are records of what was run at the time; rewriting them would falsify the logs. |
| 6 | Excluding `tests` in `.dockerignore` means CI cannot run the test suite. | `.dockerignore` | high (claimed) | **Wrong** | CI runs on the GitHub checkout, not inside the image — `.github/workflows/ci.yml` never calls `docker build`. `.dockerignore` only filters the Docker build context. | None. Acting on this would have put the test suite into the runtime image for no reason. |
| 7 | The `list_tasks` docstring claims `search` is limited to 200 characters, but `storage.get_all_tasks` enforces no length limit — the docstring documents behaviour that does not exist. | `app/main.py`, `app/storage.py` | medium (claimed) | **Wrong** | The limit is real, it is just in the other half of the request: `search: Optional[str] = Query(default=None, max_length=200, ...)` on the route. FastAPI rejects a longer value with 422 before `storage` is reached. | None. |
| 8 | The `HEALTHCHECK` calls `http://127.0.0.1:8000/health` while uvicorn binds `0.0.0.0`, so the check can never connect. | `Dockerfile` | high (claimed) | **Wrong** | `0.0.0.0` means *all* interfaces, loopback included, and the health check runs inside the same container. | None. |

**Score: 3 Useful, 2 Noise, 3 Wrong.** Two of the three Useful comments became
one-line documentation fixes; the third became an open question.

## What each side caught

**Caught by the review, missed by me:** comment 2. I wrote the sentence "the
full resolved tree from `pip freeze`" in the README myself, carried over from
the previous version, and did not notice that adding a second requirements file
made it false.

**Caught by me, missed by the review:** that CI must install
`requirements-dev.txt` and not `requirements.txt`. Nothing in the diff says so —
the failure only appears when the workflow runs and pytest cannot be imported.
That is a project-history fact (the four pinned runtime deps were chosen in
Module 1), not something visible in the lines being reviewed.

**The pattern.** All three Wrong comments share a shape: each is a real rule
applied to the wrong scope — build context confused with CI checkout, route
validation confused with storage validation, bind address confused with target
address. None of them look careless. Comment 8 was the one I had to open the
Dockerfile and think about before dismissing, which is exactly the kind of
comment that gets accepted when a reviewer is tired.

**Conclusion.** The review earned its place — one real catch I would have
shipped — but three of eight comments would have made the repo worse if
applied. AI review is a support tool, not an approval authority.
