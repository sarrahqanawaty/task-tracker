# Mini-ADR — Mid-Course Feature Extension

Status: accepted · Branch: `mid-course-project` · Baseline: `main` (Modules 1-3)

Written before the code was generated, and left unchanged afterwards except for
the "What actually happened" note at the end.

---

## Context

The Module 1-3 Task Tracker is a FastAPI backend with an in-memory store, a
`business_rules.py` module holding the status-transition matrix, a vanilla-JS
Kanban board, and 24 passing pytest tests. Two scoped features had to be added
end-to-end without disturbing any of that.

Constraints carried over from the earlier modules: no database, no
authentication, no build step, no new runtime dependencies, and the Module 3
behaviour contract must still pass afterwards.

---

## Decision 1 — Add `due_date` as an optional field, not a required one

`due_date: Optional[date] = None` on `TaskCreate`, `TaskUpdate` and
`TaskResponse`.

**Why:** every task created before this change has no due date. Making the field
required would have invalidated the existing fixtures and forced a migration
step that an in-memory store cannot express. Optional keeps all 24 existing
tests meaningful.

**Alternative rejected:** storing the deadline as a `datetime` with a time
component. The board only ever shows a day, and a time would have forced a
timezone decision that is out of scope for a learning project.

---

## Decision 2 — Compute "overdue" in the backend, not in the browser

A new module `app/due_dates.py` owns one function,
`is_task_overdue(due_date, status, today=None)`. `storage` recomputes the flag
on every read and the API returns it as `is_overdue`.

**Why:** "overdue" is a business rule, and Module 2 taught that business rules
belong in their own layer where pytest can reach them. Computing it in
`buildCard()` would have hidden it from the test suite entirely and forced any
future client to reimplement it.

**Why recomputed on read rather than stored:** a task written today with
tomorrow's date must become overdue the day after on its own. A value written
once into the store would silently go stale.

**Why a separate module rather than adding to `business_rules.py`:**
`business_rules.py` imports `app.models`, and `models` would have had to import
the overdue helper — a circular import. Keeping `due_dates.py` free of any
project import avoids the cycle and keeps the function trivially unit-testable.
This is why the function compares `status == "Done"` as a plain string rather
than against the `TaskStatus` enum.

**Alternatives the assistant proposed and I rejected:**

| Proposal | Why rejected |
|---|---|
| A Pydantic `@computed_field` on `TaskResponse` | Computed fields are included in `model_dump()`, which `storage.update_task()` feeds straight back into `TaskResponse(**data)` under `extra="forbid"`. It would have broken every PATCH, and the workaround (an explicit `exclude=`) is a trap for the next person. |
| A background job that stamps tasks overdue at midnight | No scheduler in this project, and it introduces state that can be wrong between runs. |
| An `overdue` boolean the client sets | Makes the client the authority on a rule the server enforces. |

---

## Decision 3 — Filter on the server, one query parameter per control

`GET /tasks` gained `assignee`, `search` and `overdue` alongside the existing
`status` and `priority`. They combine with AND. Any parameter left out is not
applied.

**Why:** the board's column counts come from what the API returned. If the
browser filtered a full list locally, the counts, the API and the tests could
disagree, and none of the new behaviour would be covered by pytest. Server-side
filtering made all nine of the Feature 2 tests possible.

**Alternative rejected:** a single `q=` parameter with a small query syntax
(`assignee:sarah overdue:true`). More impressive, but it means writing and
testing a parser — clearly the "ambitious feature that works only partly" the
brief warns about.

---

## Decision 4 — Blank means "no filter", never "match nothing"

A whitespace-only search term or assignee is dropped before the query is built,
and ignored again in `storage`.

**Why:** the opposite behaviour makes clearing the search box empty the board,
which reads as a bug. The distinction is pinned by
`test_blank_search_is_ignored_and_returns_every_task`.

---

## Decision 5 — Fix the source, not the test, when the regression appeared

Adding `due_date` made an existing Module 3 test fail:
`test_patch_unknown_field_returns_422` used `due_date` as its example of a field
the API does not know about, and that field is now real.

The assistant's first suggestion was to delete the test. Rejected. The test's
intent — *`extra="forbid"` rejects unknown fields with 422* — is still valid and
still worth protecting; only its sample field name had gone out of date. The
field was swapped for `estimated_hours`, which is genuinely unknown, and the
assertion was left exactly as it was. A comment in the test records why.

---

## Scope explicitly excluded

Recurring due dates, reminders or notifications, saved filter presets, sorting
by due date, bulk edits, and persisting the filter state in the URL. Each was
suggested at some point; each is a separate feature rather than a part of these
two.

---

## What actually happened

All five decisions survived implementation. The one surprise was Decision 5:
the regression was not predicted, it was found by running the existing suite
after the model change. That is the argument for running the baseline first —
without `24 passed` recorded beforehand, the failure would have looked like a
flaw in the new tests rather than a collision with an old one.
