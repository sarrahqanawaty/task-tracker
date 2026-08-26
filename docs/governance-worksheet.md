# Governance Retrospective — AI-Assisted Coding

A reconstruction of what I actually shared with AI tools during this course and
what I actually accepted back, using the logs in `docs/` as evidence rather
than memory.

Risk rubric used throughout:

- **Low** — public code, course toy-project code, no sensitive data, no
  proprietary logic.
- **Medium** — private but non-sensitive code, internal implementation detail,
  or non-public context with no secrets and no PII.
- **High** — credentials, tokens, secrets, production config, real user data,
  or code I am not authorised to share.

---

## 1. What I shared with AI

| Item shared | Where / evidence | Risk | Reason | Safer future version | Ambiguity to resolve |
|---|---|---|---|---|---|
| The Task Tracker source files as prompt context — `app/main.py`, `app/models.py`, `app/storage.py`, `app/business_rules.py`, `tests/test_tasks.py`, `frontend/index.html` | `docs/midcourse/prompt-log.md:29–42` names them explicitly | **Low** | Course toy project, public repo, no customer data and no proprietary logic. | No change — this is exactly the sharing that made the output usable. | None |
| **The whole project folder, connected to the assistant** (mid-course extension, and again for Module 5) | `docs/midcourse/prompt-log.md:3–4`, `docs/midcourse/reflection.md:11–14` | **Medium** | Connecting a folder is a much wider grant than pasting a file: it includes `.env`, `.git/`, and anything I later drop in the directory, and I approved it once for an open-ended session. | Keep the folder connection — it is what removed the invented-`FastAPI()` class of error — but check what is *in* the folder before connecting, and keep secrets out of the tree, not just out of git. | None. The `.env` here holds only `PORT` and `APP_ENV`, so nothing sensitive was exposed. That was luck, not design. |
| Full pytest failure output, pasted verbatim | `docs/midcourse/prompt-log.md:186–192`; the current run prints `C:\Users\Lenovo\Desktop\aub\task-tracker\app\main.py:198` | **Low → Medium** | The stack lines carry my Windows username and my local directory layout. Harmless here; the same habit at work pastes an internal path structure into a third-party service. | Paste the assertion line and the test name; trim the absolute path prefix. Never trim the assertion itself. | None |
| My own first name as sample data (`assignee=Sarah`) | `README.md:269`, `app/storage.py:96` | **Low** | It is my name in my own public repo, so it is my disclosure to make — but it is still real personal data sitting in a committed file and in every prompt that included that file. | Use `alice` / `bob` for fixtures and examples. Costs nothing and keeps the habit clean for a repo where the name would not be mine. | None |
| Git state: branch names, `git status`, the remote URL | Module 5 smoke test; `docs/midcourse/reflection.md:27–32` | **Low** | Public repo metadata. | No change. | None |
| The course brief and the Module 5 prompt library (the instructor's material) | This module's prompts | **Ambiguous** | It is not my material. Sharing it with a model is redistribution of someone else's content, even if the content is instructional. | Paste the specific task I am doing, not the whole document, unless the material is published openly. | **Unresolved:** I do not know the licence or redistribution terms of the course PDF. Worth asking before pasting the next one. |
| Credentials, tokens, API keys, production config, customer data | — | **None shared** | Nothing of this kind exists in this project; `.env` is git-ignored and holds two non-secret values. | — | None |

Ordered by which habit to change first: **(1)** what is in the folder before I
connect it, **(2)** trimming absolute paths out of pasted logs, **(3)** using
neutral names in fixtures.

---

## 2. What I received from AI

| Received | Tool / module | Accepted, edited or rejected | Can I explain it? |
|---|---|---|---|
| Pydantic models, in-memory storage, the five CRUD routes, the transition matrix | Cursor, Module 2 | Accepted after `python -m tests.verify_a` (8/8) and `verify_transitions` (`200,200,422,200,422,200`) — `docs/reflection_log.md:5–11` | Yes |
| A second `FastAPI()` instance and its own `Task` model, from the vague `POST /tasks` prompt | Cursor, Module 2 | **Rejected.** It would have silently removed `/health` — `docs/prompt_comparison_log.md`, `docs/reflection_log.md:32–37` | Yes — that is why I caught it |
| The Kanban board, modal, drag-and-drop and rollback | GitHub Copilot, Module 3 | Accepted, then edited | Yes |
| The sort tie-break `Number(a.id) - Number(b.id)` | GitHub Copilot, Module 3 | **Edited.** Ids are UUID strings, so `Number()` is `NaN` and the comparison did nothing — `docs/module3_debug_log.md:60–69` | Yes. Found by reading, not by a crash |
| `due_date` on the three models, `app/due_dates.py`, the filter chain, the filter bar, 20 pytest tests | Claude with the folder connected, mid-course | Accepted, with four edits recorded in `docs/midcourse/prompt-log.md` | Mostly — see §3 |
| The `computed_field` option for `is_overdue` | mid-course | **Rejected.** `model_dump()` includes computed fields, and `update_task` feeds that dump back into `TaskResponse(**data)` under `extra="forbid"` — every PATCH would have 422'd | Yes |
| A `q=` mini query language (`assignee:sarah overdue:true`) | mid-course | **Rejected** as unrequested scope — it is a parser, and it needs its own tests | Yes |
| "Delete the obsolete test" for `test_patch_unknown_field_returns_422` | mid-course | **Rejected.** The behaviour it guards is still real; I swapped the sample field to `estimated_hours` and left the assertion untouched — `docs/midcourse/prompt-log.md:194–202` | Yes |
| GitHub's own "push an existing repository" snippet containing `git branch -M main` | GitHub docs, mid-course | **Rejected.** Correct generic advice, wrong for me — I was standing on `mid-course-project` — `docs/midcourse/reflection.md:27–32` | Yes |
| The Module 5 security audit table | Module 5 | Graded: 5 Valid, 1 False Positive, 2 Noise — `docs/security-review.md` | Yes |

The pattern in this table: everything I rejected, I rejected because I had a
baseline or a rule to check it against. Nothing was rejected on instinct.

---

## 3. One generated block, traced line by line

The block I could not fully explain is `storage.update_task` — the mid-course
prompt log calls its `exclude_unset` behaviour "invisible from the model
definition", which is a polite way of saying I accepted it and moved on.

```python
def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    existing = _tasks.get(task_id)
    if existing is None:
        return None
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return _stamp_overdue(existing)
    data = existing.model_dump()
    data.update(changes)
    data["updated_at"] = datetime.now(timezone.utc)
    updated = TaskResponse(**data)
    _tasks[task_id] = updated
    return _stamp_overdue(updated)
```

| Line(s) | What it does | Why it is there | What could break | Do I own this yet? |
|---|---|---|---|---|
| `existing = _tasks.get(task_id)` / `if existing is None: return None` | Looks the task up and returns `None` for a miss. | Storage returns `None`; the route turns that into the 404 (`app/main.py:201`). Keeping HTTP out of storage is why `business_rules.py` is the only non-route module that raises `HTTPException`. | Returning a falsy sentinel instead of `None` — a task object is always truthy, but `if not existing` would be a subtle trap for a future empty-ish type. | **Yes** |
| `changes = payload.model_dump(exclude_unset=True)` | Dumps only the keys the client actually sent — not the ones defaulting to `None`. | This one line is the whole PATCH semantic. Every field on `TaskUpdate` defaults to `None`, so without `exclude_unset` a request sending only `{"title": ...}` would also send `description=None`, `status=None`, `due_date=None` and wipe them. | Swapping in `exclude_none=True` looks equivalent and is not: it would silently drop `{"due_date": null}`, so clearing a due date would stop working. | **Now yes.** This is the line I had accepted on trust. |
| `if not changes: return _stamp_overdue(existing)` | An empty body is a successful no-op. | `tests/test_tasks.py:152` pins it: PATCH `{}` returns 200 and `updated_at` is unchanged. The board's modal can send an empty diff. | Falling through instead would bump `updated_at` on every empty save and fail that test. | **Yes** |
| `data = existing.model_dump()` / `data.update(changes)` | Full current state as a dict, then the changed keys layered on top. | Merge-then-revalidate: the result goes back through `TaskResponse`, so the update is validated rather than assigned field by field. | `TaskResponse` sets `extra="forbid"`, so **any field that appears in `model_dump()` but is not a real model field raises**. This is exactly why the `computed_field` version of `is_overdue` was rejected. A future computed field re-opens the trap. | **Now yes** |
| `data["updated_at"] = datetime.now(timezone.utc)` | Server-owned timestamp. | Always UTC and always server-side — the client cannot set it, because `TaskUpdate` has no such field and `extra="forbid"` rejects it. | Trusting a client-supplied timestamp; or using `datetime.now()` without `timezone.utc`, making it naive and inconsistent with `created_at`. | **Yes** |
| `updated = TaskResponse(**data)` / `_tasks[task_id] = updated` | Revalidates and replaces the stored object. | Replacement rather than mutation keeps stored objects immutable, so a reference handed out earlier cannot change under a caller. | Nothing enforces atomicity across these lines — finding **S6** in `docs/security-review.md`. Two concurrent PATCHes can lose one update. | **Now yes** — I did not see this until the security review |
| `return _stamp_overdue(updated)` | Recomputes `is_overdue` on the way out. | The flag is derived, never stored, so it cannot go stale as the calendar moves (`app/due_dates.py`). | Storing the flag at write time instead — a task would stay "on time" forever after the date passed. | **Yes** |

Three lines I would check before committing this code again:
`exclude_unset`, the `model_dump()` round-trip under `extra="forbid"`, and the
non-atomic write.
