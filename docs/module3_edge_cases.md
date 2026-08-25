# PATCH Edge Cases (Prompts E1 and E2)

## Already covered before Module 3

`tests/test_tasks.py` already asserted four PATCH behaviors:

- partial update keeps the other fields
- unknown id returns 404
- `ToDo -> InProgress` returns 200
- `ToDo -> Done` and same-to-same return 422

The frontend now hits PATCH on every drag and on every edit, so the gaps below
matter more than they did in Module 2.

## The six uncovered scenarios (Prompt E1)

1. **A Done task is dragged back to To Do.**
   Category: business logic
   Expected status: 422
   Why it matters: the board shows Done cards next to To Do, so this is the
   easiest illegal drag for a user to attempt, and the card must roll back.

2. **PATCH carries a field the model does not define, such as `due_date`.**
   Category: validation
   Expected status: 422
   Why it matters: `TaskUpdate` uses `extra="forbid"`. A future frontend field
   sent by mistake must be rejected loudly instead of silently ignored.

3. **PATCH sends a status value outside the enum, such as `Archived`.**
   Category: validation
   Expected status: 422
   Why it matters: the drag code builds the body from `data-status`; a typo in
   the markup would produce exactly this request.

4. **PATCH sends a whitespace-only title.**
   Category: validation
   Expected status: 422
   Why it matters: the modal trims client-side, but the server is the real
   guard — the client check is a convenience, not the rule.

5. **PATCH sends an empty body `{}`.**
   Category: malformed
   Expected status: 200, task unchanged
   Why it matters: an edit where nothing changed must not corrupt the task or
   bump `updated_at`.

6. **PATCH targets a missing id *and* an illegal status in the same request.**
   Category: not found
   Expected status: 404, not 422
   Why it matters: it pins the order of the two checks. A task that no longer
   exists must answer "not found" rather than lecturing about transitions.

**Ranked for the drag-and-drop/modal frontend:** 1 → 6 → 3 → 5 → 4 → 2.
Scenario 1 is a real user action; 2 only happens if the code is wrong.

## Scenarios that became tests (Prompt E2)

One test per scenario, using the existing `client` and `created_task` fixtures:

| Scenario | Test function |
|---|---|
| 1 | `test_patch_done_to_todo_returns_422` |
| 2 | `test_patch_unknown_field_returns_422` |
| 3 | `test_patch_invalid_status_value_returns_422` |
| 4 | `test_patch_blank_title_returns_422` |
| 5 | `test_patch_empty_body_returns_200_and_leaves_task_unchanged` |
| 6 | `test_patch_missing_id_with_status_returns_404_not_422` |

A seventh test was added from the frontend work rather than from the E1 list:
`test_patch_title_only_on_done_task_returns_200`. The modal must be able to
rename a Done task, and that only works because the route skips transition
validation when `status` is absent from the body.

Each assertion checks the status code **and** the response content — the
message text for business-rule failures, the `loc` field for validation
failures — so a test cannot pass merely because "some error happened".

## Result

```
.\.venv\Scripts\python.exe -m pytest -q
```

```
24 passed, 3 warnings in 0.22s
```

17 before Module 3, 24 after. The break tests that prove these are meaningful
are in `docs/module3_break_test.md`.
