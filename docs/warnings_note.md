# Warning Triage (Prompt O1)

The pytest suite passes but prints warnings. This note classifies them before
changing anything, which is the point of O1 — warning cleanup is not a Module 2
learning goal, and "fix every warning" is a good way to break working code.

## The warning

```
tests/test_tasks.py::test_patch_invalid_transition_todo_to_done_returns_422
tests/test_tasks.py::test_patch_same_status_returns_422
  app/main.py:69: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY'
  is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
```

It appears twice — once per test that triggers an invalid transition — but it
is one warning from one line.

## In plain language

`422` is the HTTP status code for "I understood your request, but I refuse to
process it." Starlette (the layer FastAPI is built on) has always exposed a
constant for it named `HTTP_422_UNPROCESSABLE_ENTITY`. The official name of the
code was changed to **Unprocessable Content**, so Starlette renamed its
constant to `HTTP_422_UNPROCESSABLE_CONTENT` and marked the old name
deprecated.

Both constants are the number `422`. Nothing about the API's behavior differs.
The warning is Starlette saying "this spelling will go away in a future
version," not "this is wrong."

## Where it comes from

`app/business_rules.py`, inside `validate_status_transition`:

```python
raise HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    ...
)
```

The traceback points at `app/main.py:69` — the line that *calls*
`validate_status_transition` — because that is where the call originates. The
deprecated constant itself is in `business_rules.py`.

## Classification

| Warning | Classification |
|---|---|
| `StarletteDeprecationWarning` on `HTTP_422_UNPROCESSABLE_ENTITY` | **Safe to ignore for this module** |

Three reasons:

1. **Correctness is unaffected.** The response is 422 either way, and the tests
   asserting 422 pass.
2. **Prompt C1 specifies this constant by name.** The module's own
   specification says `status_code=status.HTTP_422_UNPROCESSABLE_ENTITY`.
   Changing it would make the code diverge from the assignment.
3. **It is a rename, not a behavior change.** There is no hidden bug being
   reported.

## If you did want to fix it

One line in `app/business_rules.py`:

```python
status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
```

Do not do this for the Module 2 submission — see reason 2 above. It is the
right change once the module no longer pins the older name.

## Note for the reflection log

> The suite passed with one deprecation warning: Starlette renamed
> `HTTP_422_UNPROCESSABLE_ENTITY` to `HTTP_422_UNPROCESSABLE_CONTENT`. I left it
> unchanged because both constants produce the same 422 response and Prompt C1
> specifies the older name explicitly. I classified it as safe to ignore rather
> than refactoring working code to silence a cosmetic warning.
