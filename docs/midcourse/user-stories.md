# User Stories — Mid-Course Feature Extension

Two features were added to the Module 1-3 Task Tracker:

- **Feature 1 — Due dates + overdue filter**
- **Feature 2 — Search + combined filters**

Both are visible and usable in the Kanban frontend.

---

## Feature 1 — Due dates + overdue filter

### F1-S1 — Give a task a deadline

**As a** team member, **I want** to set an optional due date when I create or
edit a task, **so that** the board shows when work is expected to be finished.

Acceptance criteria

- Creating a task with `"due_date": "2026-09-01"` returns 201 and the response
  echoes the same date.
- The field is optional: a task created without a due date returns 201 and
  `due_date` is `null`.
- An invalid date such as `"26-08-2026"` is rejected with 422 and the error
  body names `due_date`.

### F1-S2 — See at a glance which tasks are late

**As a** team member, **I want** an overdue task to stand out on its card,
**so that** I notice slipping work without opening every task.

Acceptance criteria

- A card with a due date in the past shows a red **Overdue &lt;date&gt;** pill.
- A card with a due date today or in the future shows a neutral
  **Due &lt;date&gt;** pill.
- A card with no due date shows no date pill at all.

### F1-S3 — Finished work stops being late

**As a** team member, **I want** a task I have already completed to stop being
reported as overdue, **so that** the Done column is not permanently red.

Acceptance criteria

- A task with a past due date moved to `Done` reports `is_overdue: false`.
- The same task reports `is_overdue: true` again if it is reopened to
  `InProgress`.

### F1-S4 — Move or remove a deadline

**As a** team member, **I want** to change or clear a due date from the edit
modal, **so that** a rescheduled task is not shown as late.

Acceptance criteria

- `PATCH {"due_date": "<future date>"}` returns 200 and `is_overdue` becomes
  `false`.
- `PATCH {"due_date": null}` returns 200 and clears the date.
- `PATCH {"title": "..."}` with no `due_date` key leaves the existing due date
  untouched.

### F1-S5 — Look at only the late work

**As a** team member, **I want** to filter the board down to overdue tasks,
**so that** I can triage what is late first.

Acceptance criteria

- `GET /tasks?overdue=true` returns only tasks whose `is_overdue` is `true`.
- `GET /tasks?overdue=false` returns only the tasks that are not overdue.
- Checking **Overdue only** on the board applies the same filter, and the three
  columns stay visible with their counts recalculated.

### AI assumptions corrected — Feature 1

1. **The overdue flag was first modelled as a Pydantic `computed_field` on
   `TaskResponse`.** It looks like the natural fit — the value is derived, so
   let the model derive it. Reviewing it against the existing code showed it
   would break every PATCH: `storage.update_task()` does
   `existing.model_dump()` and feeds the result back into `TaskResponse(**data)`
   under `extra="forbid"`, and Pydantic v2 includes computed fields in
   `model_dump()`. **Corrected** to a plain `is_overdue` field that
   `storage._stamp_overdue()` recomputes on every read — same freshness, no trap
   for the next person editing `update_task`.
2. **The overdue rule was going to be added to `app/business_rules.py`**, since
   that is where the status-transition rule already lives. That module imports
   `app.models`, and `models` would have needed the helper back — a circular
   import. **Corrected** to a standalone `app/due_dates.py` that imports nothing
   from the project, which is also why it compares `status == "Done"` as a
   string rather than against the `TaskStatus` enum.

---

## Feature 2 — Search + combined filters

### F2-S1 — Find a task by its words

**As a** team member, **I want** to type part of a task's title or description
into a search box, **so that** I can find one task on a busy board.

Acceptance criteria

- `GET /tasks?search=login` matches a task titled `Fix the LOGIN bug`
  (case-insensitive).
- The same search matches text that appears only in the description.
- A search with no matches returns **200** with `[]`, not 404.

### F2-S2 — Narrow the board to one person

**As a** team member, **I want** to filter by assignee, **so that** I can see
one person's workload.

Acceptance criteria

- `GET /tasks?assignee=sarah` matches a task assigned to `Sarah`.
- Surrounding whitespace is ignored: `"  sarah "` behaves like `"Sarah"`.
- Tasks with no assignee are excluded when an assignee filter is supplied.

### F2-S3 — Combine filters instead of choosing one

**As a** team member, **I want** filters to stack, **so that** I can ask for
"High-priority work assigned to Sarah that is overdue" in one step.

Acceptance criteria

- `?status=InProgress&priority=High` returns only tasks matching **both**.
- `?search=invoice&assignee=Sarah&overdue=true` returns only the task matching
  all three; near-misses on any one condition are excluded.
- An invalid value such as `?priority=Urgent` returns 422.

### F2-S4 — Clear the filters and get the board back

**As a** team member, **I want** an obvious way back to the unfiltered board,
**so that** I never get stuck looking at an empty screen.

Acceptance criteria

- A **Clear** button resets every control and reloads the full board.
- A blank or whitespace-only search box is treated as *no search*, not as a
  search that matches nothing.
- A summary line states which filters are active.

### F2-S5 — Empty columns still make sense while filtering

**As a** team member, **I want** the three columns to stay on screen when a
filter matches nothing, **so that** a filtered board never looks broken.

Acceptance criteria

- All three columns render with `(0)` when no task matches.
- The placeholder reads **No matching tasks** while a filter is active and
  **No tasks** when it is not.
- Empty columns remain valid drop targets.

### AI assumptions corrected — Feature 2

1. **Adding `due_date` silently broke an existing test, and the first proposed
   fix was to delete it.** `test_patch_unknown_field_returns_422` used
   `due_date` as its example of a field the API does not know about; Feature 1
   made that field real, so the test started failing with `assert 200 == 422`.
   Deleting it would have removed the only guard on `extra="forbid"` for PATCH.
   **Corrected:** the sample field was swapped for `estimated_hours` and the
   assertion left untouched, with a comment in the test recording why.
2. **The drag-and-drop handler was left refreshing the board locally after a
   successful move**, which was correct before filters existed. With
   *Overdue only* checked, dragging a card to Done makes it stop matching the
   filter, so it would have stayed on screen contradicting the filter summary.
   **Corrected:** `moveTask()` re-requests the board from the API when any
   filter is active, and keeps the original optimistic behaviour when none is.
