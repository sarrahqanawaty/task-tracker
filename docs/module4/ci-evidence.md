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

## Green → red → green (local)

The test command in CI is the test command locally, so the proof that a failing
test produces a non-zero exit code was run here first.

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

## Still to collect

The three GitHub Actions runs — green, intentional red, restored green — need a
push to `origin/mid-course-project`. The local sequence above proves the test
suite fails loudly and reversibly; it does not prove that GitHub runs it. That
evidence goes here as three run links once the branch is pushed:

- Green run: _pending push_
- Intentional red run: _pending push_
- Restored green run: _pending push_
