# Module 2 Reflection Log (Prompt E2)

## Verification evidence

| Check | Command | Result |
|---|---|---|
| Data model | `python -m tests.verify_a` | 8 of 8 PASS |
| CRUD endpoints | `curl` + Swagger UI | `/health` 200; `POST /tasks` 201; all five routes present in `/openapi.json` |
| Transition matrix | `python -m tests.verify_transitions` | `200, 200, 422, 200, 422, 200` — matches expected pattern |
| Pytest | `python -m pytest -q` | 17 passed, 2 warnings |
| Break Test | commented out `validate_status_transition(...)` | 2 failed, 15 passed — exactly the two predicted transition tests |

---

## Reflection

I built the Task Tracker backend in the module's order — data model, then the
five CRUD endpoints one at a time, then the status-transition rule — and
verified each part before starting the next. The data model verification passed
8 of 8 checks, the transition matrix produced the expected
`200, 200, 422, 200, 422, 200` pattern, and the pytest suite finished at 17
passed. The Break Test was the step that taught me the most: after I commented
out `validate_status_transition(...)` in the PATCH route, exactly two tests
failed — `test_patch_invalid_transition_todo_to_done_returns_422` and
`test_patch_same_status_returns_422` — both with `assert 200 == 422`, which
proved those tests were checking the business rule itself rather than just
confirming the endpoint responds.

The editor AI was strongest at generating the mechanical layers quickly once I
gave it exact names: the enums, field validators, and storage function
signatures came back matching the specification without rework. What I had to
verify carefully was everything the prompt did not pin down. Comparing the
vague `POST /tasks` prompt against the strict one showed the vague version
creating a second `FastAPI()` instance and its own `Task` model — code that
looks correct in isolation but would have silently removed my `/health`
endpoint. That is the habit I am taking forward: attach the real files, name
the exact route, status code, and models, and treat every generated block as a
draft to be checked rather than an answer to be applied.

---

## Short version (for submission)

I built and verified the Task Tracker backend in the module's order, checking
each part before moving on: 8 of 8 data-model checks passed, the transition
matrix produced the expected `200, 200, 422, 200, 422, 200`, and pytest
finished at 17 passed. The Break Test proved the suite was meaningful — after I
disabled `validate_status_transition(...)`, exactly the two predicted
transition tests failed with `assert 200 == 422`, and the remaining 15 passed.
The AI was fast and accurate at generating the model and storage layers once I
specified exact names and signatures, but comparing a vague `POST /tasks`
prompt to a strict one showed the vague version inventing its own model and a
second `FastAPI()` instance that would have removed my `/health` route. My main
takeaway is that the specificity of the prompt, and my own verification after
it, are what make AI-generated backend code trustworthy.
