# My Personal AI Usage Rules

Three rules, built only from `docs/governance-worksheet.md` and the course logs
it cites. Each one has to be concrete enough that a teammate could look at
something I did and say whether it broke the rule.

## Rule 1 — What I will never paste

**I will never paste a secret-bearing file, a credential, or a real person's
data into an AI tool — and I will check what is inside a folder before I
connect one, because connecting a folder shares everything in it, including
`.env` and `.git/`.**

*Evidence:* I connected the whole project folder for the mid-course extension
and again for Module 5 (`docs/midcourse/prompt-log.md:3–4`). Nothing leaked,
because `.env` happens to hold only `PORT` and `APP_ENV` — that was luck, not a
decision. The security review then showed `.gitignore` covers `.env` but not
`.env.production` (finding M1), so the safeguard I was relying on is thinner
than I thought.

*Test of the rule:* before connecting a folder, `ls -a` it and open anything
named like config. If I would not paste the file, I do not connect the folder.

## Rule 2 — What I will always verify before accepting

**I will not accept generated code I cannot explain line by line, and I will
record a baseline test run before I let AI change anything.**

*Evidence:* two rejections came straight out of this. The `computed_field`
version of `is_overdue` would have 422'd every PATCH, because `model_dump()`
includes computed fields and `update_task` feeds that dump back through
`extra="forbid"` — I could only see that by reading `storage.update_task`
carefully. And after adding `due_date`, `test_patch_unknown_field_returns_422`
failed with `assert 200 == 422`; because I had recorded `24 passed` first
(`docs/midcourse/verification.md:8`), I knew it was a collision with an old
test and not a flaw in my new ones. Without the baseline I would have assumed
my tests were wrong and deleted one.

*Test of the rule:* if I cannot say what a line does, why it is written that
way, and what breaks without it, it does not get committed.

## Rule 3 — How I will record AI contributions

**Every AI-assisted change gets a prompt-log entry naming the tool, the prompt,
and what I accepted, edited, or rejected — and the "rejected" entries are the
ones that must never be dropped.**

*Evidence:* `docs/midcourse/prompt-log.md` and `docs/module3_prompt_log.md`
are the only reason this governance retrospective was possible at all. The
entries that carried the most information a month later were the refusals: the
`q=` query language I turned down as unrequested scope, the "delete the
obsolete test" suggestion, and GitHub's `git branch -M main` snippet that would
have renamed the branch I was submitting (`docs/midcourse/reflection.md:27–32`).
An accepted suggestion is visible in the diff; a rejected one leaves no trace
anywhere else.

*Test of the rule:* if a reviewer asks "why is this written this way?" and the
answer is in a log entry rather than in my memory, the rule held.

---

## Sharpening pass

| Rule | What was still vague in the first draft | Revised into |
|---|---|---|
| 1 | "Do not paste sensitive data" — no way to tell whether an action violated it. | Named the artefact (secret-bearing file, credential, real person's data) and added the folder-connection check, which is the actual thing I did. |
| 2 | "Always review AI code" — everyone agrees and nobody can fail it. | Two testable conditions: explain it line by line, and record a baseline run first. |
| 3 | "Keep track of AI usage" — no format, no trigger. | Named the artefact (prompt-log entry), the fields (tool, prompt, accepted/edited/rejected), and the part that gets dropped first (the refusals). |

Re-read on **2026-09-25** and ask whether I actually followed these, or whether
the rules need to change.
