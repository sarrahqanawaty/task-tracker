# Prompt Log — Mid-Course Feature Extension

**Assistant used for this extension:** Claude (Cowork), with the project folder
connected so it could read the real files rather than be told about them.
Modules 2 and 3 used Cursor and GitHub Copilot; those logs are in
`docs/module3_prompt_log.md` and `docs/prompt_comparison_log.md`.

Each entry records the prompt, what came back, and what was accepted, edited or
rejected.

---

## P0 — The weak prompt, and the same request written as a specification

### Weak version (what I actually asked first)

> Help me with the mid-course project.

**What came back:** questions, not code — which two features, which assistant,
what the brief actually required, and a warning that the folder had no git
repository at all. Nothing was implementable from this prompt.

**Why it was weak:** no context files, no feature choice, no constraints, no
output format. It is the "fix the form" prompt from Module 3 in a different
costume: it names a goal and no specification.

### Strong version (what actually produced code)

> You are a senior Python backend engineer working in my existing Task Tracker
> repo. Context files: `app/main.py`, `app/models.py`, `app/storage.py`,
> `app/business_rules.py`, `tests/test_tasks.py`, `frontend/index.html`.
>
> Add two scoped features on the branch `mid-course-project`:
> **(1) due dates + overdue filter**, **(2) search + combined filters**.
>
> Constraints: keep the in-memory store; no new runtime dependencies; no
> database, auth, or build step; do not change the status-transition matrix in
> `business_rules.py`; do not break the Module 3 behaviour contract; all 24
> existing tests must still pass.
>
> Output: the complete replacement files, plus a new pytest file, and nothing
> else.

**Difference in the result:** the weak prompt produced a conversation; the
strong one produced files that could be run and tested. The lesson is the one
from Module 1 — the model was the same, the specification was not.

---

## Feature 1 — Due dates + overdue filter

### P1.1 — Model and validation

> Add an optional `due_date` to `TaskCreate`, `TaskUpdate` and `TaskResponse` in
> `@app/models.py`. Use `datetime.date`, default `None`, and let Pydantic do the
> parsing so a malformed date returns 422 without any hand-written date code.
> Do not change the title validator, the enums, or `extra="forbid"`. Do not add
> a required field.

**Returned:** the three model changes, with `due_date: Optional[date] = None`
and no new validator.

**Accepted:** all of it. Letting Pydantic own the parsing is what makes
`"26-08-2026"` fail with a 422 that names the field, with no code of my own.

**Edited:** added the comment explaining that sending `"due_date": null`
explicitly clears the date while omitting the key leaves it alone — the
`exclude_unset` distinction is invisible from the model definition and someone
will otherwise change it by accident.

### P1.2 — Where the overdue rule lives

> Implement "overdue" as a business rule, not a UI detail. Put it in a new
> module `app/due_dates.py` with one pure function
> `is_task_overdue(due_date, status, today=None)`. Rules: no due date is never
> overdue; a Done task is never overdue; a date equal to today is NOT overdue.
> The module must not import anything from `app.models`.

**Returned:** two options — a Pydantic `computed_field` on `TaskResponse`, or a
standalone module plus a stamping helper in `storage`.

**Rejected:** the computed-field option. `storage.update_task()` does
`existing.model_dump()` and feeds the result back into `TaskResponse(**data)`
under `extra="forbid"`; Pydantic v2 includes computed fields in `model_dump()`,
so every PATCH would have raised a validation error. The suggested workaround —
an explicit `exclude={"is_overdue"}` — hides a trap in a line nobody reads.

**Accepted:** the standalone module, with `storage._stamp_overdue()` recomputing
the flag on every read path so it can never go stale.

**Edited:** the first draft placed the function in `business_rules.py` next to
the transition matrix. That module imports `app.models`, and `models` would have
needed the helper back — a circular import. Moving it to its own module fixed
it, and is why the function compares `status == "Done"` as a plain string.

### P1.3 — Rendering it on the card

> In `@frontend/index.html`, show the due date on each card: a red
> `Overdue <date>` pill when the API says `is_overdue` is true, a neutral
> `Due <date>` pill otherwise, and nothing when there is no due date. Read the
> flag from the response — do not compute it in JavaScript. Add a `type="date"`
> field to the modal, wired into both create and edit. Do not touch
> `renderBoard()`'s sorting, the drag-and-drop handlers, or the modal dismissal
> behaviour.

**Returned:** the pill markup, the CSS, the modal field, and the `due_date`
entry in the save payload.

**Accepted:** all of it, after checking against the Module 3 contract — the
sorting comparator, the four dismissal paths, and the same-status guard in
`saveTask()` were untouched.

**Edited:** the empty date input was sending `""`, which Pydantic rejects as a
malformed date. Changed to `getField("fDueDate") || null` so an empty field
clears the date instead of failing with 422.

---

## Feature 2 — Search + combined filters

### P2.1 — Server-side filtering

> Extend `storage.get_all_tasks()` and the `GET /tasks` route to accept
> `assignee`, `search` and `overdue` in addition to the existing `status` and
> `priority`. Filters combine with AND. A filter that is not supplied is not
> applied. `search` is a case-insensitive substring match on title and
> description; `assignee` is a case- and whitespace-insensitive exact match.
> Do not add a query language, do not add sorting, do not change the response
> shape.

**Returned:** the filter chain in `storage`, the new query parameters on the
route, and `Query(...)` descriptions so the parameters are documented in
`/docs`.

**Accepted:** the chain and the parameters.

**Rejected:** an unrequested extra — a single `q=` parameter with a small query
syntax (`assignee:sarah overdue:true`). It is a parser, which means it needs its
own tests, and the brief warns specifically against the ambitious feature that
only half works.

### P2.2 — The blank-input edge case

> A whitespace-only search term must mean "no filter", not "match nothing" —
> otherwise clearing the search box empties the board. Handle it in both places:
> drop the parameter in the browser before building the query, and ignore it
> again in `storage`. Add a test that proves a whitespace-only search returns
> every task.

**Returned:** the `.strip()` guards on both sides and
`test_blank_search_is_ignored_and_returns_every_task`.

**Accepted:** all of it. Guarding on both sides is deliberate belt-and-braces:
the browser guard keeps the request clean, the storage guard keeps the API
correct for any other client.

### P2.3 — The filter bar

> Add a filter bar above the board in `@frontend/index.html`: a search input, a
> priority select, an assignee input, an "Overdue only" checkbox, and a Clear
> button. Every change re-requests `GET /tasks` with the matching query string —
> no client-side filtering. Debounce the text inputs. Keep the three columns
> visible when nothing matches, and change the empty placeholder to
> "No matching tasks" while a filter is active. Do not change the columns, the
> counts logic, or the drag-and-drop code.

**Returned:** the markup, `buildFilterQuery()`, a 250 ms debounce,
`renderFilterSummary()`, and `clearFilters()`.

**Accepted:** the structure. Building the query with `URLSearchParams` instead
of string concatenation is what makes an assignee with a space in it work.

**Edited:** the generated `moveTask()` was left untouched, which was correct
before filters existed but wrong now — with *Overdue only* checked, dragging a
card to Done makes it stop matching the filter while it stays on screen. Added a
re-request after a successful move **only when a filter is active**, so the
original optimistic-update-and-rollback behaviour from Module 3 is unchanged on
the unfiltered board.

---

## P3 — The regression, and the fix I refused

After the model change, the baseline suite failed:

```
FAILED tests/test_tasks.py::test_patch_unknown_field_returns_422 - assert 200 == 422
```

> `test_patch_unknown_field_returns_422` now fails with `assert 200 == 422`
> because it used `due_date` as its example of an unknown field, and Feature 1
> made that field real. Diagnose the source, and do not weaken the assertion.

**Returned, and rejected:** deleting the test as obsolete. It is not obsolete —
its intent is *`extra="forbid"` rejects unknown fields with 422*, and that
behaviour still exists and is still worth a guard. Deleting it would have
removed the only PATCH-side check on `extra="forbid"`.

**Accepted after editing:** swap the sample field to `estimated_hours`, which is
genuinely unknown, and leave the `== 422` assertion exactly as it was. A comment
in the test records what changed and why, so the next reader does not think the
test was quietly relaxed.

This is the Module 3 rule in practice: when a test fails, fix the source or the
example — never the assertion.
