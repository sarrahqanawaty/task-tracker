# Break Test — Module 2 (Prompt D3)

## Why a Break Test exists

A passing test suite proves the tests ran. It does not prove they check
anything. A test that asserts nothing meaningful passes on correct code *and*
on broken code — it is decoration, not protection.

The Break Test settles the question: deliberately break one piece of
production code, and see whether the tests notice. If the expected tests fail,
they are trustworthy. If everything still passes, the tests are weak and the
green suite was false confidence.

The rule that makes this safe: **break production code, never the tests, and
always restore afterwards.**

---

## The cycle

1. Record the baseline (all tests passing).
2. Introduce one deliberate break.
3. Predict which tests should fail — write the prediction down *before*
   running pytest.
4. Run pytest and compare against the prediction.
5. Restore the code.
6. Confirm the suite is green again.

---

## Break Test 1 — disable the status-transition rule

### Baseline

```
.\.venv\Scripts\python.exe -m pytest -q
```

```
17 passed, 2 warnings in 0.21s
```

### The break

In `app/main.py`, inside the `PATCH /tasks/{task_id}` route, comment out the
call to the business rule:

```python
    if payload.status is not None:
        existing = storage.get_task_by_id(task_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        # BREAK TEST — temporarily disabled on purpose. Restore this line.
        # validate_status_transition(existing.status, payload.status)
```

The route still works. It still returns 200 and still updates the task. The
only thing missing is the rule that says *which* status changes are legal — so
any transition now succeeds.

### Prediction (written before running)

Two tests should fail, both asserting 422:

- `test_patch_invalid_transition_todo_to_done_returns_422`
- `test_patch_same_status_returns_422`

The other 15 should still pass — they do not touch transition rules.

### Actual result

```
.............FF..                                                        [100%]
E   assert 200 == 422
     +  where 200 = <Response [200 OK]>.status_code
tests/test_tasks.py:102: assert 200 == 422
E   assert 200 == 422
     +  where 200 = <Response [200 OK]>.status_code
tests/test_tasks.py:107: assert 200 == 422

FAILED tests/test_tasks.py::test_patch_invalid_transition_todo_to_done_returns_422
FAILED tests/test_tasks.py::test_patch_same_status_returns_422
2 failed, 15 passed in 0.19s
```

Prediction matched exactly: 2 failed, 15 passed, and the two failures are the
two predicted tests.

### What this proves

`assert 200 == 422` is the sentence that matters. With the rule disabled the
API accepted `ToDo -> Done` and `InProgress -> InProgress`, returning 200 where
the tests demanded 422. The tests were not merely checking that PATCH responds
— they were checking *which* transitions the API refuses.

The 15 passing tests are equally informative: the break was correctly scoped.
Creating, listing, reading, deleting, and 404 handling are genuinely
independent of the transition rule, so a bug in one does not produce noise in
the others.

### Restore

Uncomment the line, then confirm:

```
.\.venv\Scripts\python.exe -m pytest -q
```

```
17 passed, 2 warnings in 0.19s
```

Restored and green. **Break Test cycle complete.**

---

## Verdict

| Question | Answer |
|---|---|
| Did the expected tests fail? | Yes — both, and only those two |
| Did any test pass that should have failed? | No |
| Did an unexpected test fail? | No |
| Are the transition tests trustworthy? | Yes |
| Do any tests need strengthening? | Not for this break |

---

## Further breaks worth trying

Each one isolates a different guarantee. Run them one at a time, restoring
between each.

| Break | File | Predicted failures |
|---|---|---|
| Change DELETE's `status_code` to 200 | `app/main.py` | `test_delete_existing_returns_204_no_body` |
| Change POST's `status_code` to 200 | `app/main.py` | `test_create_task_valid_returns_201_with_full_body`, plus every test using the `created_task` fixture |
| Return `None` instead of raising 404 in `get_task` | `app/main.py` | `test_get_task_by_id_not_found_returns_404_with_detail` |
| Drop `extra="forbid"` from `TaskCreate` | `app/models.py` | `test_create_task_unknown_field_returns_422` |
| Make the title validator accept blank strings | `app/models.py` | `test_create_task_blank_title_returns_422` |
| Ignore the filter arguments in `get_all_tasks` | `app/storage.py` | `test_list_tasks_filter_by_priority_returns_only_matches` |

A break that causes **no** failure is the interesting result — it marks a
behavior nothing is guarding, and points at a test worth adding.
