# Break Test — Module 3 (Prompt E3)

Module 2 proved the transition tests with one deliberate break. The same rule
applies to the tests added in Module 3: **a test is trusted only when it fails
for the bug it claims to catch.** Break production code, never the test, and
always restore.

Baseline before both breaks:

```
.\.venv\Scripts\python.exe -m pytest -q
```

```
24 passed, 3 warnings in 0.22s
```

---

## Break 1 — allow the illegal `Done -> ToDo` transition

### The break

In `app/business_rules.py`, add one pair to the allowed set:

```python
VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset({
    (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
    (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
    (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
    (TaskStatus.DONE, TaskStatus.TODO),  # BREAK TEST — temporary. Remove this line.
})
```

Nothing else changes. The route still validates; the rule simply now says the
move is legal.

### Prediction (written before running)

Exactly one test should fail — `test_patch_done_to_todo_returns_422` — with
`assert 200 == 422`. No other test touches `Done -> ToDo`.

### Actual result

```
>       assert response.status_code == 422
E       assert 200 == 422
E        +  where 200 = <Response [200 OK]>.status_code
FAILED tests/test_tasks.py::test_patch_done_to_todo_returns_422 - assert 200 ...
1 failed, 23 passed, 2 warnings in 0.27s
```

Prediction matched exactly: one failure, and it was the predicted one.

### What this proves

The test is not just checking that PATCH answers. It is checking *which*
direction the API refuses — the same guarantee the board's rollback depends on.
If this rule were ever relaxed by accident, the suite would say so.

### Restore

Remove the added line, then:

```
24 passed, 3 warnings in 0.17s
```

---

## Break 2 — always run the transition check, even without a status

### The break

In `app/main.py`, inside `PATCH /tasks/{task_id}`, replace the guard so the
transition rule runs on every request:

```python
    if True:  # BREAK TEST — was: if payload.status is not None. Restore.
        existing = storage.get_task_by_id(task_id)
```

This is the subtle kind of break the module warns about: the code still reads
sensibly, and every status-changing request still behaves correctly. Only
requests that *omit* status are affected.

### Prediction (written before running)

Three tests should fail — every test that PATCHes without a `status` field:

- `test_patch_partial_update_keeps_other_fields` (title-only PATCH)
- `test_patch_empty_body_returns_200_and_leaves_task_unchanged` (empty body)
- `test_patch_title_only_on_done_task_returns_200` (rename a Done task)

The status-changing tests should keep passing, because for them the guard was
true anyway.

### Actual result

```
FAILED tests/test_tasks.py::test_patch_partial_update_keeps_other_fields - At...
FAILED tests/test_tasks.py::test_patch_empty_body_returns_200_and_leaves_task_unchanged
FAILED tests/test_tasks.py::test_patch_title_only_on_done_task_returns_200
3 failed, 21 passed, 6 warnings in 1.76s
```

Prediction matched: three failures, exactly the three predicted, and 21 passes.

### What this proves

`test_patch_title_only_on_done_task_returns_200` is the test that guards a real
frontend flow — editing the title of a Done card. Before this break test existed,
nothing in the suite would have noticed if the guard disappeared; the board
would simply have started rejecting edits on Done tasks with a confusing 422.
The two older PATCH tests failing alongside it also confirms the break was
correctly scoped rather than accidentally global.

### Restore

Put `if payload.status is not None:` back, then:

```
24 passed, 3 warnings in 0.17s
```

---

## Verdict

| Question | Break 1 | Break 2 |
|---|---|---|
| Did the predicted tests fail? | Yes — the one predicted | Yes — the three predicted |
| Did any test pass that should have failed? | No | No |
| Did an unexpected test fail? | No | No |
| Suite restored to green afterwards? | Yes, 24 passed | Yes, 24 passed |

Both new-test groups are trustworthy. The suite is green because the code is
correct, not because the assertions are weak.
