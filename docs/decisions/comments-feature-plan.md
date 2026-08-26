# Comments on Tasks — Feature Plan

**Status:** plan only. Nothing in `app/`, `frontend/` or `tests/` was changed.

A comment has:

- `id` — string UUID
- `task_id` — reference to a task
- `author` — required string, 1–100 characters
- `body` — required string, 1–2000 characters
- `created_at` — server-generated UTC datetime

---

## 1. Data model

The repo keeps every Pydantic model in `app/models.py` and puts *rules* in
their own tiny pure modules (`app/business_rules.py`, `app/due_dates.py`).
Comments have validation but no rule, so they belong in `app/models.py` and
nothing new is needed beside it.

```
CommentCreate   author, body                        (extra="forbid")
CommentResponse id, task_id, author, body, created_at (extra="forbid")
```

- All three existing models set `model_config = ConfigDict(extra="forbid")`
  (`app/models.py:60`, `:98`, `:140`). Both comment models must do the same, or
  the feature will be the only place in the API where a typo is silently
  accepted.
- Length limits follow the existing `_validate_title` pattern
  (`app/models.py:29–49`): strip, reject blank, reject over-length, return the
  stripped value. A shared `_validate_text(value, label, max_len)` helper keeps
  `author` (100) and `body` (2000) on the same code path as `title` (200).
  This is deliberate: `docs/security-review.md` finding **S1** is that
  `description` and `assignee` were left unbounded. A new feature should not
  add two more unbounded fields.
- `created_at` is server-generated in storage, exactly like tasks
  (`app/storage.py:43`, `datetime.now(timezone.utc)`); the client cannot send
  it, because `CommentCreate` does not have the field and `extra="forbid"`
  rejects it.
- `task_id` is set by the route from the path, never read from the body.
- **No `updated_at`.** Comments are append-only in v1 — see Open Questions.

**Do not add a `comment_count` field to `TaskResponse` in v1.**
`storage.update_task` does `existing.model_dump()` → `data.update(changes)` →
`TaskResponse(**data)` under `extra="forbid"` (`app/storage.py:168–171`). The
mid-course log records that this exact round-trip is why the `computed_field`
version of `is_overdue` was rejected (`docs/midcourse/prompt-log.md:79–90`). A
count would have to be re-stamped on every read path the way
`_stamp_overdue` does, which is a second derived field's worth of machinery for
a number the board can live without.

## 2. API routes

Paths nest under the existing task routes and reuse the response conventions in
`app/main.py`.

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| `POST` | `/tasks/{task_id}/comments` | `CommentCreate` | `201` + `CommentResponse` | `404` if the task does not exist; `422` on blank/over-length/unknown field |
| `GET` | `/tasks/{task_id}/comments` | — | `200` + `list[CommentResponse]`, oldest first | `404` if the task does not exist |

- The 404 detail must reuse the exact existing string,
  `f"Task with id {task_id} not found"` (`app/main.py:161`, `:197`, `:201`,
  `:223`) — `tests/test_tasks.py:69` asserts on that wording, and the board's
  `readError()` (`frontend/index.html:804`) surfaces `detail` directly.
- `tags=["comments"]`, matching the `tags=["tasks"]` / `tags=["system"]`
  grouping already used, so `/docs` stays readable.
- Routes stay `def`, not `async def`, like every existing route.
- A task with no comments returns `200 []`, never `404` — the same choice
  `GET /tasks` already makes (`tests/test_tasks.py:35`).
- **No `DELETE`, no `PATCH` on comments in v1.** See Open Questions.

## 3. Storage

In `app/storage.py`, beside `_tasks`:

```python
_comments: dict[str, list[CommentResponse]] = {}   # task_id -> comments, insertion-ordered
```

Three repo-specific details that a generic plan will not contain:

1. **`_reset()` must clear both dicts.** `tests/conftest.py:8–12` calls
   `storage._reset()` in an `autouse` fixture before and after every test. If
   `_reset` clears only `_tasks`, comments leak across all 44 existing tests and
   the failures will look random.
2. **`delete_task` must drop the task's comments** (`app/storage.py:176–188`).
   Otherwise deleting a task orphans its comments in memory forever, and a
   recycled id would inherit them.
3. No `_stamp_*` helper is needed — nothing about a comment is derived, so
   comments are returned as stored.

`add_comment(task_id, payload)` mints `str(uuid4())` and the UTC timestamp the
same way `add_task` does; `get_comments(task_id)` returns the list as stored,
which is already oldest-first.

## 4. Tests

A new `tests/test_comments.py`, matching the naming style of
`tests/test_midcourse.py` (`test_<subject>_<condition>_<expected>`), reusing the
`client` and `created_task` fixtures from `conftest.py`.

*Happy path*
- `test_create_comment_returns_201_with_full_body`
- `test_list_comments_returns_them_oldest_first`
- `test_list_comments_on_task_without_comments_returns_200_and_empty_list`

*Validation*
- `test_create_comment_blank_body_returns_422`
- `test_create_comment_body_over_2000_chars_returns_422`
- `test_create_comment_author_over_100_chars_returns_422`
- `test_create_comment_unknown_field_returns_422`
- `test_create_comment_cannot_set_id_or_created_at`

*Edge cases*
- `test_create_comment_on_missing_task_returns_404_with_task_detail`
- `test_list_comments_on_missing_task_returns_404`
- `test_deleting_a_task_removes_its_comments`
- `test_comments_do_not_leak_between_tests` (the `_reset` guard)

**Break Test for this feature** (the Module 2 habit, `docs/break_test.md`):
delete the `_comments.pop(task_id, None)` line from `delete_task` and confirm
that exactly `test_deleting_a_task_removes_its_comments` fails.

## 5. Frontend changes

`frontend/index.html` only — one file, no build step, no framework.

- `buildCard()` (`:542`) gains a small comment-count element, built with
  `createElement` and `textContent` like every other card element (`:554`,
  `:560`, `:569`, `:577`). **Never `innerHTML`** — the only two `innerHTML`
  uses in the file are constant strings (`:526`, `:531`), and
  `docs/security-review.md` finding S7 explains why that distinction matters.
- `openEditModal()` (`:692`) gains a comments panel: a list of existing
  comments plus an author/body form that POSTs and re-renders.
- Fetches go through the existing `API` constant (`:386`) and errors through
  `readError()` (`:804`), so a 422 message appears the same way it does for a
  blank title today.
- Untouched, per the Module 3 behaviour contract
  (`docs/module3_behavior_contract.md`): `compareTasks()`, `renderBoard()`
  sorting, the drag-and-drop handlers, `moveTask()`'s optimistic
  update-and-rollback, the four modal dismissal paths, and the same-status
  guard in `saveTask()` that `docs/module3_debug_log.md:9–33` exists to protect.

## 6. Migration notes

- There is no database and no migration to write: the store is a module-level
  dict (`app/storage.py:8`), so "migration" means only that comments vanish on
  restart, exactly like tasks.
- No existing task data changes shape. `TaskResponse` is untouched, so all 44
  current tests should still pass unmodified — that is the check to run first.
- `README.md:293` names SQLite as the intended persistence layer and
  `backend/data/` exists for it. Whenever that lands, comments need a table with
  a foreign key to tasks and an `ON DELETE CASCADE` that reproduces detail 2
  above. Worth writing down now, while the reason is fresh.

## 7. Open questions

1. **Are comments editable or deletable?** v1 says no, which is convenient and
   probably wrong: a typo in a comment is the most ordinary thing in the world.
   Deciding this decides whether `updated_at` exists, and that is much cheaper
   to decide before the model ships than after.
2. **Who is `author`?** With no authentication (`docs/security-review.md` S2),
   `author` is a free-text string, so anyone can post as anyone. That is
   acceptable for a course project and unacceptable the moment this is shared.
   Does the field stay honest-but-unverified, or does the feature wait for auth?
3. **Can a `Done` task be commented on?** The status matrix
   (`app/business_rules.py:5–9`) works hard to protect workflow integrity, and
   comments are the first write path that does not consult it. My reading: yes,
   allow it — discussion after completion is the point — but it should be a
   recorded decision, not an accident of route ordering.
4. **Is there a cap on comments per task?** Unbounded append plus no
   authentication is finding S3 in a new place.

**Files read:** `AGENTS.md`, `app/main.py`, `app/models.py`, `app/storage.py`,
`app/business_rules.py`, `app/due_dates.py`, `tests/conftest.py`,
`tests/test_tasks.py`, `tests/test_midcourse.py`, `frontend/index.html`,
`README.md`, `docs/midcourse/prompt-log.md`,
`docs/module3_behavior_contract.md`, `docs/security-review.md`.

**Assumptions to verify:** that comments are per-task and never global; that
nobody needs comment counts on the board in v1; that "oldest first" is the
wanted order (nothing in the repo establishes a precedent — the board sorts
tasks by priority, not by time).

---

## Section critique

My grading of the repo-grounded plan above. Labels: **Right** (accurate about
the repo and safe to keep), **Missing** (a required detail is absent),
**Needs-Resequencing** (useful, but in the wrong order).

| Section | Label | Evidence | Minimal correction |
|---|---|---|---|
| Data Model | **Right** | Matches the actual conventions — models in `app/models.py`, `extra="forbid"` on all three existing models, validation via the `_validate_title` helper rather than `Field(max_length=...)`. The `comment_count` warning cites the real `model_dump()` round-trip at `app/storage.py:168–171`. | None. |
| API Routes | **Missing** | The 404 wording and the `200 []` choice are right, but nothing says what happens when `task_id` is not a UUID at all. Today `GET /tasks/{task_id}` types it as `str`, so garbage gives 404, not 422 — the plan should state that comments inherit that, rather than leaving the next reader to guess. | Add one line: `task_id` stays `str`, so a malformed id returns 404 like the existing routes. |
| Storage | **Right** | The `_reset()` and `delete_task` details are the two things that actually break, and both are traceable to real lines (`tests/conftest.py:8–12`, `app/storage.py:176–188`). This section is the clearest evidence the plan came out of this repo rather than out of a description of FastAPI. | None. |
| Tests | **Needs-Resequencing** | The list is good and the names match the house style, but the Break Test is buried at the end. In this repo the Break Test is what makes a suite trustworthy (`docs/break_test.md`, `docs/midcourse/verification.md:65–136`) — it is a design step, not a postscript. The baseline run of the existing 44 tests is also missing from this section and only appears under Migration Notes. | Move "record the baseline `44 passed`" to the top of this section and the Break Test directly under it, before the test names. |
| Frontend Changes | **Missing** | It names the functions to touch and the ones to leave alone, but says nothing about the *state* the panel needs: comments are fetched per task and the board already re-requests on every filter change. Without a decision, the modal will either refetch on every open or hold stale data. | Add: fetch comments when the edit modal opens, discard on close. No caching in v1. |
| Migration Notes | **Right** | Correctly says there is nothing to migrate and explains why, then records the SQLite/cascade consequence for later. Grounded in `README.md:293` and `backend/data/`. | None. |
| Open Questions | **Right** | Four real decisions, each tied to a specific file or finding rather than being generic "what about scale?" questions. Q3 is the one I would not have thought to ask. | None. |

---

## Generic vs repo-grounded

**The generic baseline.** Run first, in a separate thread with no repo access,
the same feature request produced a coherent eight-step plan: define the comment
data model, add a validation schema, decide storage behaviour, add API
endpoints, define error handling, update frontend behaviour, add tests, document
the feature. Its own "Assumptions this plan makes" section listed a database
with a migration, an ORM-style foreign key, a component-based frontend, and
authenticated users supplying the author. Every one of those four is false here:
the store is a dict, there is no ORM, the frontend is one static HTML file, and
there is no auth.

- **Biggest difference:** the generic plan describes what a comments feature is;
  the repo-grounded plan describes what would *break* — `_reset()` leaking
  comments into all 44 existing tests, `delete_task` orphaning them, and the
  `model_dump()` round-trip that already killed one derived field on this
  project.
- **The plan I would hand to a teammate:** the repo-grounded one, because its
  three storage details are the ones that would cost an afternoon to rediscover
  by debugging. The generic plan's section headings are fine; its content would
  have to be thrown away.
- **Where generic chat is enough:** deciding the *shape* of the thing before
  any code exists — is `author` free text or a user reference, are comments
  editable, should they be nested under tasks. Those are design questions, and
  the repo has no opinion on them yet. That is Module 1's work, not Module 4's.
