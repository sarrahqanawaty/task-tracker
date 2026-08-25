# Reflection — Mid-Course Feature Extension

**Which tools, and for what.** I used a different assistant in each phase of this
course, and they were not interchangeable. ChatGPT and Claude did the text-heavy
work in Module 1 — user stories, the architecture comparison, the ADR, and the
initial scaffold. Cursor did Module 2, where the work was generating whole
backend layers from a strict specification: the Pydantic models, the in-memory
store, the five CRUD routes one prompt at a time, and the status-transition
rules. GitHub Copilot did Module 3, where the work was small edits inside a file
I already had open — the Kanban board, the modal, the refactor, and debugging
from console output. For this mid-course extension I worked with Claude with the
project folder connected, so it read the real files instead of being told about
them, which removed the whole category of errors where the assistant invents a
second `FastAPI()` instance because it cannot see the first one.

**Where AI clearly helped.** Generating the twenty new pytest tests in one pass.
I specified the fixtures to reuse, the naming, and the exact behaviour each test
had to pin, and the suite came back matching the existing `conftest.py` without
rework. Writing those by hand would have taken most of an evening. What made
them trustworthy was not that they passed — it was the Break Test. Disabling
`validate_status_transition` failed exactly one transition test, and replacing
the overdue comparison with `return False` failed exactly six of the nine
overdue tests while the three that do not depend on that comparison kept
passing. That precision is what tells me the tests are checking behaviour rather
than decorating the repository.

**Where it slowed me down.** GitHub's own "push an existing repository" snippet
contains `git branch -M main`. I was standing on my `mid-course-project` branch,
and running that block as printed would have renamed the branch I was supposed
to submit. It was not an AI hallucination — it was correct generic advice that
was wrong for my situation, which is the harder failure to notice, because
nothing about it looks suspicious.

**Where my own review changed the outcome.** I ran the existing suite before
touching anything and recorded `24 passed`. After adding `due_date`, one test
failed with `assert 200 == 422`. Because I had the baseline, I could tell this
was a collision with an old test rather than a flaw in my new ones:
`test_patch_unknown_field_returns_422` had used `due_date` as its example of an
unknown field, and Feature 1 made that field real. The quick fix on offer was to
delete the test. I refused it. The behaviour it protects — `extra="forbid"`
rejecting unknown fields with 422 — is still real and still worth a guard, so I
swapped the sample field to `estimated_hours`, left the assertion untouched, and
left a comment explaining the change. Without the baseline recorded first, I
would probably have assumed my own tests were wrong.
