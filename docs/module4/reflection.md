# Module 4 — Deliverable Checklist and Tool-Fit Reflection

## Deliverable checklist

| Deliverable | State | Evidence |
|---|---|---|
| Claude Code set up in the repo root | **Complete** | Working directory is `task-tracker/`; the repo answers about its own files were checked against `app/main.py` and `app/models.py`. |
| `CLAUDE.md` corrected by hand, not left as the `/init` draft | **Complete** | [`CLAUDE.md`](../../CLAUDE.md) — the "What I changed from the generated draft" table lists five corrections, including the missing Python version. |
| `CLAUDE.md` committed | **Missing** | The Module 4 files are still untracked. Nothing has been committed or pushed yet. |
| Plan-mode practice on a change that was never made | **Complete** | The `GET /version` endpoint was planned and deliberately not implemented; it appears in no document as an existing route. |
| CI workflow at the repo root | **Complete** | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — push to any branch, PR to `main`, Python pinned to 3.14, `pytest -v`. |
| CI inspected for false-green patterns | **Complete** | Nine checks in [`ci-evidence.md`](ci-evidence.md): no `continue-on-error`, no `\|\| true`, no `--exit-zero`, no pipe around pytest. |
| Green → red → green proof | **Partial** | Local sequence recorded with real output: `44 passed` → `assert 201 == 200`, exit 1 → `44 passed`, exit 0. On GitHub, run #1 went red on its own and caught a real bug — `pytest -v` could not import `app` from a clean checkout — fixed with `pytest.ini`. Runs #2–#4 pending. |
| `Dockerfile` and `.dockerignore` | **Complete** | Multi-stage on `python:3.14-slim`, non-root `app`, no secrets, no `--reload`. |
| Container verified at runtime (`/health` + `whoami`) | **Complete** | [`docker-verification.md`](docker-verification.md) — build, run, `/health` 200, `whoami` -> `app` (uid 10001), `/app` holds only `app/`, no `.env`/`.git`/`tests` in the image, no pytest or httpx installed, health status `healthy`, image 251 MB. |
| Docstrings added without changing logic | **Complete** | `git diff app/` → 291 insertions, 1 deletion, all docstrings; `pytest -v` → 44 passed. |
| README rewritten with exact commands | **Complete** | [`README.md`](../../README.md) — prerequisites, setup, run, tests, Docker, CI, structure, API, conventions, limitations, links. |
| Documentation checked against the code, with corrections logged | **Complete** | [`claim-vs-reality.md`](claim-vs-reality.md) — three corrections, three docstring spot-checks. |
| Annotated AI review log | **Complete** | [`ai-review-log.md`](ai-review-log.md) — 8 comments: 3 Useful, 2 Noise, 3 Wrong. |
| Technical note, linked from the README | **Complete** | [`dockerfile-design.md`](../decisions/dockerfile-design.md), linked from the README's Docker section. |
| Tool-fit reflection | **Complete** | Below. |

**Still to collect:** the three CI run links. That is blocked on a push, not on
work I have skipped.

## Tool-fit reflection

**GitHub Copilot — Module 3.** Copilot was at its best when the unit of work was
smaller than a file and I already had the file open. Building the Kanban board,
it kept up with what I was typing and let me stay inside one mental context.
What it could not do is see across the project: its sort tie-break was
`Number(a.id) - Number(b.id)`, which is perfectly reasonable code for ids that
are integers, and this project's ids are UUID strings generated in
`app/storage.py`. `Number()` returned `NaN`, the comparison silently did
nothing, and nothing ever threw. That is the shape of Copilot's failure mode —
locally plausible, globally wrong, and quiet. I reach for it when I am editing,
not when I am deciding.

**Cursor — Module 2.** Cursor fit the phase where I needed whole layers
generated from a specification I could write down: the enums, the three
Pydantic models, the storage functions, then the five routes one at a time. Once
I attached the real files and named the exact route, status code and model, the
output came back matching without rework. The comparison that taught me the most
was between a vague `POST /tasks` prompt and a strict one: the vague version
created a second `FastAPI()` instance and its own `Task` model, code that would
have silently removed my `/health` endpoint. Cursor rewards a specification and
punishes a wish. I reach for it for a bounded implementation loop inside the
editor.

**Claude Code — Module 4.** The terminal agent was the right shape for this
module because none of the work was inside one file. It read the repo, wrote a
workflow, a Dockerfile, a `.dockerignore` and docstrings across five modules,
and ran the test suite to check its own work. That is also why it was the
riskiest: one approval can touch several files, and `.dockerignore` plus
`CLAUDE.md` plus a README rewrite is a lot of surface to skim. The two habits
that made it usable were plan mode for anything bigger than a one-line change,
and reading the diff before approving — which is how I noticed that documenting
the code had to stay documentation, and confirmed it with `git diff app/`
showing 291 insertions and exactly one deletion. I reach for it for work that
spans the project: infrastructure, review, and anything where the answer
requires reading more files than I want to open.

**No winner, and that is the point.** The three tools failed in three different
places for three different reasons — Copilot could not see the project, Cursor
could not read my mind, and Claude Code could change more than I was reading.
The engineering task decides: line-level editing, bounded implementation, or
project-wide work. What does not change across all three is the part I own —
inspect, verify, reject, and be the one who approves.
