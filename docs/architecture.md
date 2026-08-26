# Architecture — Task Tracker

The final one-page architecture document, assembled from the strongest parts of
the three context-strategy drafts (`architecture-A.md`, `architecture-B.md`,
`architecture-C.md`). The comparison log that produced it follows below.

---

## 1. What the app does

Task Tracker is a minimal REST API for tracking tasks, with a single-file
vanilla-JavaScript Kanban board in front of it. A task has a title, a priority,
an optional assignee and an optional due date; the board shows tasks in three
status columns and moves them by dragging a card, which PATCHes the API. The
server — not the browser — decides which status moves are legal and whether a
task is late. Tasks live in a module-level dictionary and are lost when the
process restarts.

## 2. Data model

One entity, three Pydantic models in `app/models.py`: `TaskCreate` (input),
`TaskUpdate` (partial input, every field optional) and `TaskResponse` (output).
All three set `extra="forbid"`.

| Field | Type | Rules |
|---|---|---|
| `id` | `str` | UUID4, generated in `storage.add_task` |
| `title` | `str` | required; stripped, non-blank, max 200 |
| `description` | `str` | optional in, always a string out (`""`) |
| `status` | `TaskStatus` | `ToDo` \| `InProgress` \| `Done`, default `ToDo` |
| `priority` | `TaskPriority` | `Low` \| `Medium` \| `High`, default `Medium` |
| `assignee` | `str \| None` | optional |
| `due_date` | `date \| None` | optional ISO `YYYY-MM-DD`, parsed by Pydantic |
| `is_overdue` | `bool` | derived on read, never sent by the client |
| `created_at`, `updated_at` | `datetime` | UTC, server-owned |

Both enums are `str` Enums — which is what lets `app/due_dates.py` compare
`status == "Done"` without importing `app.models` and creating a cycle.

## 3. Request flow — creating a task

1. The board calls `fetch(API + "/tasks")` with a JSON body.
2. `CORSMiddleware` checks the `Origin` against four explicit localhost
   origins; there is no wildcard and no credentials.
3. FastAPI validates the body into `TaskCreate`. A blank title, a bad enum
   value, a malformed date or an unknown field is a 422 before the handler runs.
4. `create_task` delegates immediately to `storage.add_task` — the route holds
   no logic.
5. `add_task` mints `str(uuid4())` and one `datetime.now(timezone.utc)` used for
   both timestamps, and stores the task in `_tasks`.
6. `_stamp_overdue` returns a copy with `is_overdue` freshly computed by
   `app/due_dates.is_task_overdue`.
7. FastAPI serialises `TaskResponse` and answers 201.

## 4. Key files

| File | Role |
|---|---|
| `app/main.py` | FastAPI instance, CORS, the six routes, uvicorn entry point |
| `app/models.py` | Two enums, three models, the shared title validator |
| `app/storage.py` | `_tasks` dict, CRUD, the filter chain, `_stamp_overdue`, `_reset` |
| `app/business_rules.py` | `VALID_TRANSITIONS` and the 422 it raises |
| `app/due_dates.py` | `is_task_overdue` — pure, imports nothing from the app |
| `backend/main.py` | Thin re-export so `uvicorn backend.main:app` works |
| `frontend/index.html` | The whole board: markup, CSS, filters, modal, drag-and-drop |
| `tests/conftest.py` | `client` and `created_task` fixtures + autouse `storage._reset()` |
| `tests/test_tasks.py` | Modules 1–3: CRUD, transitions, PATCH edge cases |
| `tests/test_midcourse.py` | Due dates, overdue, search and combined filters |

## 5. Conventions

- **Layering.** Routes delegate, storage holds state, rules live in their own
  pure modules. Storage returns `None` for "not found"; only the route layer and
  `business_rules` speak HTTP.
- **Validation at the edge.** Pydantic owns parsing and shape; there is no
  hand-written date or enum handling in the app.
- **`extra="forbid"` everywhere.** An unknown field is a 422, not a silent
  ignore — and it is why a derived field cannot be added casually to
  `TaskResponse`, since `update_task` feeds `model_dump()` back through it.
- **Derived on read.** `is_overdue` is recomputed on every read path, so it
  cannot go stale as the calendar advances.
- **Partial updates.** `model_dump(exclude_unset=True)` is the whole PATCH
  semantic: an omitted key is untouched, an explicit `null` clears the value.
- **Filters combine with AND**, and blank means "no filter", never "match
  nothing".
- **Frontend.** No framework, no build step; cards are built with
  `createElement` and `textContent`, and errors are rendered from `detail`.

## 6. Not visible / assumptions

- SQLite is named in `README.md:293` and `backend/data/` exists for it, but **no
  database code is present** — persistence is in-memory only.
- The delivery layer added in Module 4 — `Dockerfile`, `.dockerignore` and
  `.github/workflows/ci.yml` — exists but has not been exercised here: the
  container has not been run and the workflow has not been pushed.
- No authentication; `README.md` records it as an intentional scope decision.
- Python 3.14 is inferred from `README.md` and the `__pycache__` tags; there is
  no `pyproject.toml`.

---

# Context strategy comparison log

Same task, three fresh threads, three context strategies.

| | **A — minimal context** | **B — structured context** | **C — targeted context** |
|---|---|---|---|
| Context given | The one-line task, free exploration | `AGENTS.md` + a one-line summary of every file | Exactly three files: `main.py`, `models.py`, `storage.py` |
| Length | 84 lines | 111 lines | 88 lines |
| **Got right** | The overall shape, the six routes, the derived-on-read idea, and the fact that rules live in their own modules. Readable, and correct about everything it took from the code. | Everything A got right, plus the things only a careful reader finds: `extra="forbid"`, `exclude_unset`, the `str`-Enum reason for the import-cycle avoidance, and the honest note that SQLite is planned but absent. | The plumbing, precisely: route-to-storage delegation, `None`-means-404, the PATCH ordering (id check before rule check), and `_stamp_overdue`. Every claim traced to a line it actually read. |
| **Got wrong, missed, or invented** | **Invented persistence.** "Persistence is SQLite, stored under `backend/data/`" — it is not; the store is a dict. `README.md` mentions SQLite as a plan and A promoted a plan to a fact. Also "presumably planned for later" about auth, where the README says it is deliberately excluded. | Nothing factually wrong, but it **restates `AGENTS.md`** for the business rules instead of re-deriving them, so an error in `AGENTS.md` would have passed straight through. It is also the longest draft and the only one that misses "one page". | Missed the two rules that give the app its behaviour — the transition matrix and the overdue rule both live one import away — and could say nothing about tests, the board, or how to run anything. It said so, on every line, instead of guessing. |
| **Best suited for** | A first orientation when nobody has written any context yet — and a reminder to check its confident sentences. | Onboarding docs, README rewrites, anything where completeness matters and a maintained context file already exists. | Correctness-sensitive work — a security review, a bug hunt, a change to one subsystem — where an invented fact costs more than a missing one. |

**Verdict.** The final document above is B's structure and completeness, with
C's evidence discipline layered on top: every claim that C could not confirm
from source is either sourced here or explicitly listed in §6, and the
"Not visible" section is C's habit, not B's. A contributed the clean §1 framing
and one very useful mistake — it is the only draft that got persistence wrong,
and it got it wrong by repeating a sentence from `README.md` in a more
confident voice than the README used. That is precisely the failure mode I would
not have noticed if I had run only one strategy.

The length ordering was the opposite of what I expected: more context produced a
*longer* answer, not a sharper one. C was not the shortest by much, because half
its lines are "not visible from the files I read" — which is exactly what makes
it trustworthy.

**My context rule.**

> For onboarding and documentation tasks, I use structured context (`AGENTS.md`
> plus file summaries), because completeness matters more than precision and a
> maintained context file is the cheapest way to get it. For correctness-
> sensitive tasks — security review, debugging, changing one subsystem — I use
> targeted context and treat every "not visible" as a finding, because on those
> tasks a confident invention costs more than an admitted gap.
