# Module 3 Debugging Log and Reflection (Prompt R1)

Built from what was actually observed in this repository — the browser, the
Network results, and the pytest output recorded below. Nothing here is a
predicted result.

---

## Debugging log — entry 1: the modal rejected edits that changed nothing

**What failed.** Editing a task without touching its status returned 422. The
modal always put `status` into the PATCH body, so a To Do task was sent
`{"status": "ToDo"}` — a same-to-same transition, which
`app/business_rules.py` refuses by design.

**Evidence.** Sending the pre-fix body from the page:

```
PATCH http://localhost:8000/tasks/{id}  ->  422
{"detail": "Invalid status transition from ToDo to ToDo.
            Allowed transitions: ['Done->InProgress', 'InProgress->Done', 'ToDo->InProgress']"}
```

**Root-cause diagnosis.** The backend rule is correct and was not the bug. The
frontend was reporting a status *change* on every save, when it should only
report one when the value actually changed.

**Accepted or rejected.** Accepted the frontend fix, rejected the tempting
backend fix. Relaxing `VALID_TRANSITIONS` to permit same-to-same would have
made the symptom disappear and deleted a real rule — and two Module 2 tests
would have gone red. `saveTask()` now deletes `status` from the payload when it
matches the task's current status, and
`test_patch_title_only_on_done_task_returns_200` locks the behavior in.

---

## Debugging log — entry 2: deliberate break in the PATCH route

**What I intentionally broke.** In `app/main.py`, replaced the guard
`if payload.status is not None:` with `if True:` so the transition rule ran on
every PATCH, including requests that carry no status.

**Failing tests and one-line summary.** Three failures, exactly as predicted:
`test_patch_partial_update_keeps_other_fields`,
`test_patch_empty_body_returns_200_and_leaves_task_unchanged`, and
`test_patch_title_only_on_done_task_returns_200` — every test that PATCHes
without a status, while all 21 status-carrying tests still passed.

**AI assistant's root-cause diagnosis.** The guard is what separates "the client
asked to change status" from "the client sent a partial update"; without it,
`validate_status_transition` compares the existing status against a missing one
and no title-only edit can succeed.

**Accepted or rejected, and why.** Restored the guard immediately — the break
was a test of the tests, not a proposed change. The suite returned to
`24 passed`. Full record in `docs/module3_break_test.md`.

---

## Debugging log — entry 3: sorting bug found by reading, not by crashing

**What failed.** Nothing visibly. The tie-break in `renderBoard` was
`Number(a.id) - Number(b.id)`, but ids are UUID strings generated in
`app/storage.py`, so `Number()` returns `NaN` and the comparison silently did
nothing. Two cards of the same priority had no defined order.

**Root cause and fix.** Replaced the numeric tie-break with `created_at`, then
`id`, compared as strings. This is the kind of bug that never throws — it only
produces a board that reorders itself for no reason.

---

## Reflection

The assistant was most useful when it was given the real files and the exact
rules: enum values, the three legal transitions, and the endpoints. With those
in the prompt it produced the drag-and-drop layer — optimistic move, PATCH,
rollback on rejection — close to correct on the first pass. Where it needed
correcting was at the seams between frontend and backend rather than inside
either one: the modal happily sent an unchanged `status`, which the backend was
right to reject with 422, and the first version of the drag error reused the
board's load error with a "Retry" button that made no sense after a rollback.

Checking behavior in the browser is what turned those from opinions into facts.
The four UI states were confirmed one at a time — a slowed `fetch` to catch the
loading banner, a stopped `uvicorn` to see the error state and the working Retry
button, and a drag onto Done to watch the card roll back with the server's own
message displayed. The same discipline applied to the tests: the suite went from
17 to 24, and each new group was proved by breaking the source it guards and
predicting which tests would fail before running pytest — one failure predicted
and one seen for the transition rule, three predicted and three seen for the
partial-update guard.

The habit worth keeping is the behavior contract. Writing down the ten things
that must not change *before* editing a working board turned "did I break
anything?" into a ten-line checklist that could actually be re-run, and it is
what caught the Retry-button regression while it was still cosmetic instead of
after submission.

---

## Short version (for submission)

I built the Kanban board's remaining Module 3 layers on the Module 2 API:
CORS for the local frontend origins, the four UI states, drag-and-drop that
PATCHes with an optimistic update and rolls back on rejection, and a
create/edit modal with client-side title trimming and visible server 422s.
Three real bugs surfaced. The modal sent `status` on every save, so editing a
task without changing its status returned *Invalid status transition from ToDo
to ToDo*; I fixed the frontend rather than relaxing the backend rule, because
the rule was correct and two existing tests depended on it. The priority
tie-break compared UUID ids with `Number()`, which silently produced `NaN`. And
my first drag-error message offered a "Retry" button that made no sense after a
rollback. I added seven PATCH tests (17 → 24 passing) and proved them by
deliberate source breakage: predicting one failure for the transition rule and
three for the partial-update guard, and seeing exactly those. The habit I am
carrying forward is writing the behavior contract before refactoring, so
"nothing broke" becomes a checklist I can actually re-run.
