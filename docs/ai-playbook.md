# My AI Coding Playbook

Written after five modules and the final release check on one repo. Every rule
here comes from something that actually happened in `task-tracker`, not from
what I think good practice sounds like.

## When I reach for AI first

- **Mechanical layers I can specify exactly.** The twenty mid-course pytest
  tests came back in one pass matching `conftest.py` with no rework, because I
  named the fixtures, the naming pattern and the behaviour each test had to
  pin. That would have taken most of an evening by hand.
- **A second reading of code I already wrote.** The security audit found the
  compound memory issue (unbounded field × unauthenticated write × unbounded
  store) that I had read past twice.
- **Explaining someone else's decision back to me** — including my own from
  three weeks ago. Tracing `storage.update_task` line by line is what taught me
  that `exclude_unset` is the entire PATCH semantic, not a detail.

## When I do not reach for AI

- **When I have not run the thing yet.** Asking before I have output is how I
  get a plausible answer to the wrong question.
- **When the decision is about scope.** The `q=` mini query language was good
  code answering a request I never made.
- **When the advice has to fit my situation, not the general case.** GitHub's
  own snippet told me to run `git branch -M main` while I was standing on
  `mid-course-project`. Not a hallucination — correct generic advice, wrong for
  me, and that is the harder failure to see.
- **When the question is "does this actually work?"** No amount of asking
  replaces running it. `pytest -v` was in my README, and it had never worked
  from a clean checkout.

## My non-negotiables

1. **Record the baseline before AI changes anything.** `24 passed`, written
   down, is the only reason I knew that `assert 200 == 422` was an old test
   colliding with a new field and not a flaw in my new tests.
2. **Fix the source or the example — never the assertion.** I was offered
   "delete the obsolete test" and refused; the behaviour it guards
   (`extra="forbid"` rejects unknown fields) is still real.
3. **Check what is in the folder before I connect it.** Connecting a project
   folder shares `.env` and `.git/` too. Nothing leaked here because my `.env`
   holds `PORT` and `APP_ENV` — luck, not design.
4. **If I cannot explain a line, it does not get committed.** The
   `computed_field` version of `is_overdue` looked cleaner and would have 422'd
   every PATCH.
5. **Protect the secret with a pattern, not with a filename.** `.gitignore`
   listed `.env` and `.env.local`; `git check-ignore -v .env.production`
   returned nothing. Nothing had leaked, because the only env file I ever made
   happened to be spelled the way the rule expected.

## My review rules

- **Grade, do not accept.** Nine AI security findings came back polished; five
  were Valid, one was a False Positive that named two `innerHTML` lines which
  turned out to be constant strings, and two were true-but-unactionable. The
  fluency of the report says nothing about the ratio.
- **Do my own pass with the AI output closed.** Everything the audit missed
  needed two files held together at once — what `DELETE` means next to the
  transition matrix, what UTC means to someone in Beirut, that `ALLOWED_ORIGINS`
  has no test protecting it.
- **Verify the claim, not the conclusion.** When the audit said concurrent
  PATCHes can lose an update, I checked that the routes are `def` and not
  `async def` before believing it.
- **Check a documented command by running it, not by reading it.** The two
  real problems in the release check — the broken `pytest -v` and the
  `.gitignore` gap — both came from executing something, and neither would have
  survived to be found if I had trusted a careful re-read.
- **Log the refusals.** Accepted suggestions show up in the diff on their own;
  rejected ones leave no trace anywhere except the prompt log.

## What I am still figuring out

- How much context is enough. Strategy B was the most complete and also the
  longest and the most trusting of its own inputs; C was the most honest and
  knew the least. I have a rule now (`docs/architecture.md`) but not much
  practice with it.
- Where the line is between "course-scope decision" and "vulnerability I am
  choosing not to see". `no authentication` sits on that line in every document
  I wrote this module.
- Whether my prompt logs stay this detailed once nobody is grading them.
- How much of my verification is habit and how much was the course watching. The
  `pytest -v` bug sat in the README through two modules of "careful reading"
  before a CI runner found it in forty seconds.

## Decision Card

- For a new feature I reach for: **Cursor**, with the real files attached and
  the routes, status codes and models named — that combination is what produced
  the whole Module 2 backend without inventing a second `FastAPI()` instance.
- For a code review I reach for: **a repo-connected agent with a review pane
  and diffs I approve one at a time** — because review is where I most need to
  see what it read before I read what it concluded.
- For debugging I reach for: **GitHub Copilot in the open file, plus the actual
  failure text.** Entry 1 of `docs/module3_debug_log.md` was solved by pasting
  the real 422 body; entry 3 was solved by reading, not by asking.
- For infrastructure I reach for: **general chat, and then I check it against
  my own situation** — the `git branch -M main` near-miss is the entire reason
  for this answer.
- I will never paste **credentials, tokens, or a real person's data** into an
  AI tool — and I now count *connecting a folder* as pasting everything in it.
- My one rule is: **if I cannot say what a line does, why it is written that
  way, and what breaks without it, I do not own it — so I do not commit it.**

---

**Re-read on 2026-09-25** and answer honestly: am I still doing this, or have
the rules quietly changed?
