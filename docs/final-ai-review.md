# Final AI Review and Ownership Evidence

Branch: `final-project` · Date: 2026-08-26

## AGENTS.md guardrails

| Guardrail | Present | Where |
|---|---|---|
| Repo-specific stack and commands | **yes** | §1–2: Python 3.14.0, FastAPI 0.141.1, Pydantic 2.13.4, Uvicorn 0.52.4, pytest 9.1.1, httpx 0.28.1; `pytest -v`, `uvicorn app.main:app --reload --port 8000`, the two Docker commands, and the note that `pytest.ini` is what makes the bare `pytest` work |
| Docs-first / read-first guardrail | **yes** | §4: inspect the relevant files before proposing anything, show the diff before applying, and put review and evidence work in `docs/` |
| Unexpected `app/` / `frontend/` edits rule | **yes** | §4: do not modify `app/`, `frontend/`, `backend/` or `tests/` without explicit approval of one specific small change; an unexpected edit to those directories is a diff I reject, and any change that is made must be explained here |
| Business rules stated as implemented, not as imagined | **yes** | §3: the full transition matrix including that same-to-same is rejected, and that the rule runs only when the PATCH body carries `status` |

## AI code review mini-log

**Diff reviewed:** the delivery layer added on top of the app —
`.github/workflows/ci.yml`, `Dockerfile`, `.dockerignore`,
`requirements-dev.txt`, the README rewrite, and the docstring pass across
`app/`. Full log of all eight comments in `docs/module4/ai-review-log.md`;
the four that mattered are here.

| AI comment | Grade | Reason | Verification or decision |
|---|---|---|---|
| `.dockerignore` excludes `backend/`, but the README presents `uvicorn backend.main:app` as an equivalent run command — inside the container that module does not exist. | **Useful** | Nothing is broken (`CMD` is `app.main:app`), but the README implied the alias works everywhere, and it does not. | Opened `.dockerignore` and confirmed `backend` is excluded. **Fixed the README**: the Docker section now says `backend/` is not in the image and the alias is local-only. |
| `requirements.lock.txt` no longer describes the environment the tests run in, now that pytest and httpx come from `requirements-dev.txt`. | **Useful** | The lockfile lists 19 runtime packages and neither pytest nor httpx, while the venv has both. | Checked the file. **Fixed the README**: it now calls it the resolved *runtime* tree. |
| `ENV APP_ENV=production` in the Dockerfile has no effect, because `APP_ENV` is only used to set `reload` inside the `if __name__ == "__main__"` block, which the container never executes. | **Noise** | True — I read `app/main.py` and the claim holds — but it changes nothing and costs nothing. | **No change.** It documents intent, and removing it would invite someone to put `--reload` back. |
| Excluding `tests` in `.dockerignore` means CI cannot run the test suite. | **Wrong** | `.dockerignore` filters the Docker build context only. CI runs on the GitHub checkout — `ci.yml` never calls `docker build`. | Checked `ci.yml` end to end. **Rejected.** Acting on it would have shipped the test suite into the runtime image for no reason. |

## AI security mini-review

Read-only review of the repository. All nine findings and their grades are in
`docs/security-review.md`; three representative ones here, with the file
evidence I used to grade them.

| Finding | File evidence | Grade | Reason | Next action |
|---|---|---|---|---|
| `description` and `assignee` accept strings of unbounded length on both create and update. | `app/models.py:63`, `:66` (`TaskCreate`) and `:101`, `:104` (`TaskUpdate`) carry no constraint, while `title` is capped at 200 by `_validate_title` (`app/models.py:47`). | **Valid** | The asymmetry is the tell: whoever bounded `title` meant to bound input, so the two unbounded fields are an oversight. A 10 MB description is accepted today and stored for the life of the process. | Backlog: `Field(max_length=…)` on both fields plus a 422 test. Not applied here — the final project does not change `app/`. |
| No authentication or authorization on any route: any caller can read, modify or delete any task. | `app/main.py:70–223` — six plain route decorators, no dependency, no key, no session. | **Valid, as scope** | Real, but it is a recorded decision rather than a defect: `README.md` lists authentication as intentionally excluded and the app binds to `127.0.0.1`. | Keep documented. It becomes the highest-severity item the day this is deployed anywhere other than localhost. |
| `innerHTML` is used when rendering board columns, so a task title could inject markup (stored XSS). | `frontend/index.html:526`, `:531`. | **False Positive** | I opened both lines. `:526` assigns a constant empty-state string and `:531` assigns `""`; neither touches task data. Every task-derived value goes through `textContent` (`:554` title, `:560` description, `:569` priority, `:577` due pill) and cards are built with `createElement` (`:543`). | None. The pattern matched; the data flow did not. |

## Manual security check

I checked one risk the AI review did not raise, and it turned into the only
security change in this branch.

**What I checked.** Whether `.gitignore` actually protects environment files,
rather than protecting the one filename I happened to use.

**What I found.** It covered exactly two spellings:

```
$ git check-ignore -v .env
.gitignore:13:.env    .env

$ git check-ignore -v .env.production
(no output — not ignored)
```

`.env.production` and `.env.staging` would have been committed. The current
`.env` holds only `PORT` and `APP_ENV`, so nothing has leaked — but that is
luck, not a rule. The safeguard was a filename match.

**Why it matters.** Every other secrets control in this repo is downstream of
this one. `.dockerignore` keeps `.env` out of the image, and the security
review's "no secrets" row is true today; both are worthless the moment someone
adds a real value to a file whose name does not happen to be `.env`.

**What I did.** Replaced the two lines with a pattern plus an explicit
re-include, and verified the result instead of assuming it:

```
.env*
!.env.example
```

```
.env            IGNORED
.env.local      IGNORED
.env.production IGNORED
.env.staging    IGNORED
.env.example    not ignored     <- still committed as the template
```

This is a repository-configuration change. No file under `app/`, `frontend/`,
`backend/` or `tests/` was modified on this branch.

## One AI output I rejected or corrected

**The suggestion.** The security audit reported a Medium-severity stored-XSS
risk: "`innerHTML` is used when rendering board columns — task titles could
inject markup", pointing at `frontend/index.html:526` and `:531`, with the
suggested fix "replace with `textContent` / DOM construction".

**Why I did not accept it.** It is a real pattern and a real vulnerability
class, and it names two real lines — which is exactly why it was tempting. I
opened them. Line 526 assigns a constant empty-state string and line 531
assigns `""`. Neither one carries task data. The values that *do* come from a
task are already set with `textContent` at lines 554, 560, 569 and 577, and the
cards themselves are built with `createElement` at line 543. The finding
matched on the presence of `innerHTML` and never followed the data.

**What I did instead.** Graded it **False Positive** in
`docs/security-review.md` with the line-by-line reason above, and made no code
change. Applying the "fix" would have edited working frontend code to remove a
risk that was not there — and it would have left me believing the board had
been vulnerable, which would have made every later judgement about that file
worse.

**A second one, briefly.** The review also claimed that excluding `tests` in
`.dockerignore` breaks CI. Rejected: CI runs on the GitHub checkout, not inside
the image. Acting on it would have put the test suite into the runtime image.

## Three AI usage rules

1. **Never paste** credentials, tokens, production config, or a real person's
   data into an AI tool — and treat *connecting a project folder* as pasting
   everything inside it, including `.env` and `.git/`. Before connecting one,
   look at what is in it.
2. **Always verify** by running the thing, not by reading the answer: record a
   baseline test run before AI changes anything, open the file and line behind
   every finding before grading it, and check a documented command by executing
   it rather than by re-reading it. The `pytest -v` bug survived several
   careful readings of the README and died the first time a clean machine ran it.
3. **Record AI contributions** in a prompt or review log naming the tool, the
   suggestion, and whether I accepted, edited, or rejected it — and never drop
   the rejections. An accepted suggestion is visible in the diff; a rejected one
   leaves no trace anywhere else.

## Ownership statement

I am comfortable submitting this repository as my own work because I can point
at the evidence behind every part of it and explain the decisions that are not
obvious. I ran the app, the tests, the container and the CI workflow myself,
and the numbers in `docs/release-evidence.md` are copied from those runs rather
than from what the tools told me to expect — including the DELETE that returns
204 with a zero-byte body and the container that answers `app` to `whoami`. I
graded the AI output rather than accepting it: five of nine security findings
valid, one a false positive I can explain line by line, and two review comments
I refused because acting on them would have made the repo worse. Two of the
three real problems in this release came from checking rather than reading —
the documented `pytest -v` command that had never worked from a clean checkout,
and the `.gitignore` that protected one filename instead of a pattern. Where I
chose to deviate from the course instructions I said so and gave the reason:
Python 3.14 instead of 3.11 because that is what this project is built and
verified on, and a separate `requirements-dev.txt` so the runtime image does
not ship a test runner.
