# Documentation Audit — Claim vs Reality

Module 4, Part 4.4. Documentation that reads well is not documentation that is
true. This is the log of what the generated docs claimed, what the code and the
commands actually do, and what I changed.

## 1. Inaccuracies found and fixed

| # | Documentation claim | Code or runtime reality | Resolution | Evidence kept |
|---|---|---|---|---|
| 1 | The old README listed under **Tech stack**: "SQLite (via Python's built-in `sqlite3`) for persistence — *not yet implemented*". | There is no `sqlite3` import, no connection, no schema and no query anywhere: `grep -rn "sqlite" app/ backend/ --include=*.py` returns nothing. `backend/data/` contains only `.gitkeep`. | Removed SQLite from the stack list. It is now stated once, under **Limitations**: tasks are in memory and `backend/data/` is *reserved* for a database file that does not exist. | The empty grep, and `ls backend/data/` showing only `.gitkeep`. |
| 2 | The old README's setup step was `pip install -r requirements.txt`, and its Tests section said `python -m pytest -q` gives **44 passing**. | `requirements.txt` has exactly four lines — fastapi, uvicorn, pydantic, python-dotenv. Neither `pytest` nor `httpx` is in it, and `fastapi.testclient` imports httpx. A reader following the README from a clean checkout cannot run a single test. | Added `requirements-dev.txt` (`-r requirements.txt` plus `pytest==9.1.1` and `httpx==0.28.1`) and changed the README setup step to install it. CI installs the same file. | `grep -iE "pytest|httpx" requirements.txt` returns nothing. |
| 3 | The old README named Python 3.14 only inside a paragraph about pinning, with no Prerequisites section. | The project genuinely requires 3.14 — the course materials say 3.11, which would be a different environment from the one every test result in `docs/` was recorded on. | Added a **Prerequisites** section naming Python 3.14, and pinned 3.14 in both `.github/workflows/ci.yml` and the `Dockerfile`. The 3.11-vs-3.14 divergence is recorded in `CLAUDE.md` §1. | `.venv/Scripts/python --version` → `Python 3.14.0`. |

Numbers 1 and 2 are the two required corrections. Number 2 is the one that
would have bitten someone: it is also exactly why the first CI run in the
lecture went red.

## 2. Docstring spot-checks

Three docstrings added in Part 4.4, each compared against the function body
rather than against how it reads.

| Docstring claim | Reality | Verdict |
|---|---|---|
| `delete_task` — "Answered with HTTP 204 and an empty body." | `@app.delete(..., status_code=status.HTTP_204_NO_CONTENT)` in `app/main.py`, and `test_delete_existing_returns_204_no_body` asserts `response.content == b""`. | **Accurate.** A docstring saying "returns the deleted task" would have been the classic version of this mistake. |
| `update_task` — "The status-transition rule runs only when the body carries `status`, and the task is looked up first, so a request for a missing id answers 404 rather than a transition error." | `if payload.status is not None:` guards the rule, and `storage.get_task_by_id` runs inside that guard before `validate_status_transition`. Pinned by `test_patch_missing_id_with_status_returns_404_not_422`. | **Accurate**, and worth documenting: `docs/module3_debug_log.md` records the bug that appears when that guard is removed. |
| `list_tasks` — "`search`: … max 200 characters." | `Query(default=None, max_length=200, ...)` in `app/main.py`. The limit is on the **query parameter**, not on the stored `description`, which has no limit at all. | **Accurate but easy to misread.** I kept the wording tied to the parameter. The unbounded `description` is a separate finding in `docs/security-review.md`. |

## 3. Claims I decided not to state

- I did not document a `GET /version` endpoint. It was planned in plan mode
  (Part 4.1) and never implemented, so it does not exist in any document.
- I did not write "production ready" anywhere. The container runs; there is no
  deployment, no TLS, no rate limiting, no process manager.
- I did not claim the frontend is covered by tests. It is not — every one of
  the 44 tests is a backend test.

## 4. Verification actually performed

```
pytest -v                     ->  44 passed, 3 warnings
git diff app/                 ->  291 insertions, 1 deletion, all docstrings
```

The single deleted line is the old one-line `health()` docstring that was
replaced by the Google-style version. No runtime line changed, which is the
check that documentation work has not quietly become a code change.
