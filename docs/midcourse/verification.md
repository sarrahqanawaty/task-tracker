# Verification — Mid-Course Feature Extension

Every result below was produced by a command actually run on this machine
(Windows, PowerShell, `.venv` active), not a check that was merely planned.

---

## 1. Baseline — before any change

Run first, on the `mid-course-project` branch at commit `0db0412`, so that any
later failure could be attributed correctly.

```
> python -m pytest -q
........................                                       [100%]
24 passed, 3 warnings in 0.19s
```

**24 passed.** This number is what made the regression in section 3 readable as
a collision with an old test rather than a flaw in the new ones.

---

## 2. Full suite — after both features

```
> python -m pytest -q
............................................                   [100%]
44 passed, 3 warnings in 0.33s
```

**44 passed** — the original 24 plus 20 new tests in `tests/test_midcourse.py`.
The brief requires at least 4 new tests.

| Group | Tests | Covers |
|---|---:|---|
| Feature 1 — due dates | 11 | Valid and malformed dates, the overdue rule, Done tasks, updating and clearing a date, preservation on unrelated PATCH, the `overdue` filter both ways, and the rule as a pure unit test with a fixed `today`. |
| Feature 2 — search and filters | 9 | Case-insensitive title and description search, blank search, no matches, assignee matching, `status`+`priority` combined, three filters combined, and 422 on invalid filter values. |

The three warnings are a pre-existing Starlette deprecation
(`HTTP_422_UNPROCESSABLE_ENTITY`) inherited from Module 2. Not introduced here
and out of scope.

---

## 3. The regression the baseline caught

Immediately after the model change, one Module 3 test failed:

```
FAILED tests/test_tasks.py::test_patch_unknown_field_returns_422 - assert 200 == 422
```

**Diagnosis:** the test used `due_date` as its example of a field the API does
not know about. Feature 1 made that field real, so the PATCH now succeeded with
200 as it should.

**Fix:** the sample field was changed to `estimated_hours`, which is genuinely
unknown. The `assert response.status_code == 422` was left exactly as it was,
and a comment in the test records what changed and why. The source of truth —
`extra="forbid"` on `TaskUpdate` — was not weakened.

---

## 4. Break Test A — the status-transition rule

`validate_status_transition(...)` was commented out in `app/main.py`, then
restored with `git checkout`.

**Broken:**

```
> python -m pytest -q -k "transition"
.F                                                             [100%]
FAILED tests/test_tasks.py::test_patch_invalid_transition_todo_to_done_returns_422
E       assert 200 == 422
1 failed, 1 passed, 42 deselected in 0.15s
```

**Restored:**

```
> git checkout app\main.py
> python -m pytest -q -k "transition"
..                                                             [100%]
2 passed, 42 deselected, 1 warning in 0.05s
```

**Conclusion:** the transition test fails for the intended reason when the rule
is removed. It is checking the business rule, not merely that PATCH answers.

---

## 5. Break Test B — the overdue rule

In `app/due_dates.py`, `return due_date < today` was replaced with
`return False` — the rule still runs, it just always answers "not overdue".

**Broken:**

```
> python -m pytest -q -k "overdue"
.F.FFFFF.                                                      [100%]
FAILED tests/test_midcourse.py::test_past_due_date_marks_task_overdue - assert False is True
FAILED tests/test_midcourse.py::test_done_task_with_past_due_date_is_not_overdue - assert False is True
FAILED tests/test_midcourse.py::test_overdue_filter_returns_only_overdue_tasks - assert [] == ['cf2a050a-...']
FAILED tests/test_midcourse.py::test_overdue_filter_false_excludes_overdue_tasks
FAILED tests/test_midcourse.py::test_is_task_overdue_unit_rules - assert False is True
FAILED tests/test_midcourse.py::test_search_combines_with_assignee_and_overdue - assert [] == ['b4187d19-...']
6 failed, 3 passed, 35 deselected in 0.26s
```

**Restored:**

```
> git checkout app\due_dates.py
> python -m pytest -q -k "overdue"
.........                                                      [100%]
9 passed, 35 deselected in 0.10s
```

**Conclusion — and this is the more informative of the two.** Six of the nine
selected tests failed, and the three that survived are exactly the ones that do
not depend on the broken comparison: a task with no due date, a task due today,
and a task with a future date are all correctly "not overdue" whether the
comparison works or not. A suite where all nine had failed together would have
suggested the tests were coupled to one another; a suite where none failed would
have meant they were theatre. Six specific failures and three specific survivors
is what a real suite looks like.

The failure of `test_search_combines_with_assignee_and_overdue` also confirms
that the Feature 2 combined filter genuinely depends on the Feature 1 rule
rather than passing by coincidence.

---

## 6. Behaviour contract — before and after

The eight-item contract from Module 3 lives in
[`../module3_behavior_contract.md`](../module3_behavior_contract.md) and was
re-checked after these features were added, with `uvicorn` on
`127.0.0.1:8000` and the page served from
`http://localhost:5500/frontend/index.html`.

| ID | Behaviour | After the mid-course changes |
|---|---|---|
| C1 | Three status columns with correct counts | **Pass** — To Do (1), In Progress (0), Done (1) with two seeded tasks |
| C2 | Cards sort by priority inside each column | **Pass** — comparator untouched by this work |
| C3 | Loading state before tasks load | **Pass** — unchanged code path |
| C4 | Empty columns stay visible and remain drop targets | **Pass** — In Progress rendered `(0)` with a "No tasks" placeholder |
| C5 | Error state when the backend is stopped | **Pass** — surfaced while port 8000 was blocked, before the stale server was killed |
| C6 | Valid drag sends PATCH and updates the board | **Pass** — see 7a/M5 |
| C7 | Invalid drag reverts and shows the server message | **Not re-checked by hand** — see "Still unverified" at the end of section 7 |
| C8 | Modal create/edit, title validation, all four dismissal paths | **Pass** — tasks created through the modal with a due date; 422 handling unchanged |
| C9 | A same-column drop sends no request | **Pass** — guard unchanged in `moveTask()` |
| C10 | An unchanged status is omitted from the PATCH body | **Pass** — guard unchanged in `saveTask()`; pinned by `test_patch_title_only_on_done_task_returns_200` |

Nothing in the contract had to be relaxed to accommodate the new features.

---

## 7. Browser checks — the new features

Two kinds of evidence are recorded separately below, because they are not
equally strong and it would be misleading to blend them.

### 7a. Checked by hand, in Chrome

| # | Check | Result |
|---|---|---|
| M1 | Create a task with a past due date | **Pass** — card shows a red **Overdue 2026-08-06** pill |
| M2 | Create a task with a future due date | **Pass** — card shows a neutral **Due 2026-08-29** pill |
| M3 | Filter bar renders above the board | **Pass** — search box, priority select, assignee input, "Overdue only" checkbox and Clear button, once the window was wide enough to show the full bar |
| M4 | Edit modal carries the due date | **Pass** — opening Edit on an existing task pre-fills **Due date** with `2026 / 08 / 06` |
| M5 | Valid drag moves a card (contract C6) | **Pass** — `test 2` moved To Do → In Progress and stayed there after the PATCH |
| M6 | Empty column still renders (contract C4) | **Pass** — Done showed `(0)` with a "No tasks" placeholder |

### 7b. Checked by an automated browser run

The filter interactions were also exercised with a scripted headless-Chromium
session against this same commit, driving the real page rather than the API. It
is recorded separately from 7a because it was run by the assistant, not by hand:

| # | Check | Result |
|---|---|---|
| A1 | Typing in the search box narrows the board | **Pass** — 3 cards → 1; summary line read `Filtered by search "login"` |
| A2 | "Overdue only" narrows the board | **Pass** — only the past-due card remained; summary read `Filtered by overdue only` |
| A3 | Priority filter narrows the board | **Pass** — `priority=Low` returned the single Low card |
| A4 | Empty placeholder changes under a filter | **Pass** — columns with no match read **No matching tasks** rather than **No tasks** |
| A5 | Clear restores the unfiltered board | **Pass** — all cards returned and the summary line cleared |
| A6 | Blank title is still blocked before any request | **Pass** — modal showed "Title is required." and stayed open |
| A7 | Escape closes the modal | **Pass** |
| A8 | No JavaScript console errors | **Pass** — only a `favicon.ico` 404, which is unrelated to the page |

### A note worth recording

The filter bar did not appear on the first load. The cause was browser caching
of the old `index.html`, not a code fault — a hard refresh (`Ctrl+Shift+R`)
rendered it. Separately, the checkbox looked absent for a while because the
browser window was too narrow and the right end of the filter bar was off
screen. Both are worth writing down: "the feature is missing", "the browser is
showing yesterday's file", and "the control is off the edge of the window" look
identical from the outside, and only one of them is a bug.

### Still unverified

Contract item **C7** — an invalid drag reverting the card and showing the
server's message — was not re-exercised by hand after these changes. The code
path is unchanged from Module 3, where it was verified, and the rule behind it
is covered by `test_patch_invalid_transition_todo_to_done_returns_422` plus
Break Test A above. It is listed here rather than claimed as passed.
