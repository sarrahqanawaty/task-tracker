# CI Evidence — green → red → green

Module 4, Part 4.2. A green check is only worth something if it turns red when
a test fails. This is the proof.

## The workflow

`.github/workflows/ci.yml` — one job, `test`, on `ubuntu-latest`:
checkout → set up Python 3.14 (pinned, with pip cache) → `pip install -r
requirements-dev.txt` → `pytest -v`.

## Inspection before trusting it (C2)

I searched the YAML for the patterns that produce a false green, before pushing
anything.

| Check | Result | Evidence |
|---|---|---|
| `push` and `pull_request` triggers present | **Pass** | `push: branches: ['**']`, `pull_request: branches: [main]` |
| Python version pinned, not `3.x` or latest | **Pass** | `python-version: '3.14'` |
| Dependencies installed **and** tests actually run | **Pass** | separate `Install dependencies` and `Run tests` steps; the last one is `pytest -v` |
| `continue-on-error` | **Pass** — absent | `grep -n "continue-on-error" .github/workflows/ci.yml` → no match |
| `\|\| true` | **Pass** — absent | same grep, no match |
| `--exit-zero` | **Pass** — absent | that flag belongs to flake8; it is not in the file |
| pytest output piped in a way that hides the exit code | **Pass** | `run: pytest -v` with no pipe, no `tee`, no summary step |
| Deployment steps | **Pass** — none | the job ends after the test step |
| Workflow file in the right folder | **Pass** | `.github/workflows/ci.yml` at the **repository root**, not inside `app/` |

The one that mattered most here was not on the list: **which requirements file
gets installed.** `requirements.txt` has no pytest and no httpx, so a workflow
installing it would fail at collection with `ModuleNotFoundError` — a red run,
but for the wrong reason. CI installs `requirements-dev.txt`.

Nine checks passed, and the first run still failed. That is the part worth
keeping.

## Run #1 — red, and I did not plan it

```
JOB test  ->  failure
  1 Set up job                 -> success
  2 Check out the repository   -> success
  3 Set up Python 3.14         -> success
  4 Install dependencies       -> success
  5 Run tests                  -> failure
```

<https://github.com/sarrahqanawaty/task-tracker/actions/runs/32980828271>

Install succeeded and `pytest -v` failed, on a suite that had just reported
`44 passed` on my machine. Reproduced locally the moment I ran the command CI
runs, instead of the one I always type:

```
$ .venv/Scripts/pytest -v
ImportError while loading conftest 'tests\conftest.py'.
tests\conftest.py:4: in <module>
    from app.main import app
E   ModuleNotFoundError: No module named 'app'
```

**Diagnosis.** `python -m pytest` puts the current directory on `sys.path`;
plain `pytest` does not. `tests/` has no `__init__.py`, so pytest's prepend
import mode inserts `tests/` and never the repository root, and
`from app.main import app` in `conftest.py` cannot resolve. Every test result
recorded in `docs/` was produced with `python -m pytest` — the form that hides
the problem.

**What it actually caught: a documentation lie.** `README.md` and `CLAUDE.md`
both told a reader to run `pytest -v`. From a clean checkout that command did
not work, and no amount of re-reading the README would have revealed it,
because the README was checked against my shell, and my shell had the
repository root on `sys.path` for an unrelated reason.

**Fix.** `pytest.ini` at the repository root:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

One file, no test changed, no application code changed. Both invocations now
work:

```
$ .venv/Scripts/pytest -q          ->  44 passed
$ .venv/Scripts/python -m pytest -q ->  44 passed
```

This is the module's whole argument in one run. I inspected the YAML line by
line and found nothing, because nothing was wrong with the YAML — the workflow
was correct and my environment was the thing that lied. A green first run would
have shipped a README that does not work.

## Green → red → green (local rehearsal)

Run before pushing, so the intentional red run on GitHub would fail for the
reason I chose rather than for a fourth reason I had not thought of.

**1. Green**

```
$ pytest -q
44 passed, 3 warnings in 0.53s
exit code: 0
```

**2. Red — one intentional, reversible, one-line change**

In `tests/test_tasks.py::test_create_task_valid_returns_201_with_full_body`,
`assert response.status_code == 201` → `== 200`. A test expectation, not
production code.

```
$ pytest -q
>       assert response.status_code == 200
E       assert 201 == 200
FAILED tests/test_tasks.py::test_create_task_valid_returns_201_with_full_body
1 failed, 43 passed, 3 warnings in 0.63s
exit code: 1
```

Two things this proves: the failure is *the one I caused* (`assert 201 == 200`,
in the test I edited, and only that test), and pytest exits non-zero — which is
the only signal the workflow reads.

**3. Green again**

```
$ pytest -q
44 passed, 3 warnings in 0.64s
exit code: 0

$ git diff --stat tests/
(no changes)
```

The restore is verified by the empty diff, not by remembering that I undid it.

## The runs on GitHub

| Run | SHA | Result | What it proves | Link |
|---|---|---|---|---|
| #1 — unplanned red | `3ce0fc7` | **failure** | `pytest -v` could not import `app` from a clean checkout — a real bug in the README, not in the workflow | [runs/32980828271](https://github.com/sarrahqanawaty/task-tracker/actions/runs/32980828271) |
| #2 — green | `d7695c6` | **success** | after `pytest.ini`, the documented command works on a machine that has never seen this project | [runs/32981262056](https://github.com/sarrahqanawaty/task-tracker/actions/runs/32981262056) |
| #3 — intentional red | `bd6982b` | **failure** | one flipped assertion turns the check red; install stayed green, so the job reached the tests and failed on them | [runs/32981499078](https://github.com/sarrahqanawaty/task-tracker/actions/runs/32981499078) |
| #4 — restored green | `eba1ae2` | **success** | the revert is complete — `git diff d7695c6 -- tests/` is empty, so the file is byte-identical to the last green state | [runs/32981688552](https://github.com/sarrahqanawaty/task-tracker/actions/runs/32981688552) |

Run #3's step list is the part that matters:

```
2 Check out the repository   -> success
3 Set up Python 3.14         -> success
4 Install dependencies       -> success
5 Run tests                  -> failure
```

Failing at step 5 with steps 1-4 green is what separates "CI runs the tests"
from "CI fell over before reaching them". Run #1 has the same shape for a
different reason, which is why it took a local reproduction to tell them apart.

Runs after #4 are documentation commits on the same branch.
