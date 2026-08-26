# Technical Note — Dockerfile design

**Status:** accepted · **Scope:** Module 4 delivery layer · **Date:** 2026-08-26

## Context

Until Module 4 the Task Tracker only ran one way: a virtualenv on my laptop,
`uvicorn app.main:app --reload`, Python 3.14. That is fine while I am the only
person running it and useless the moment anyone else needs to. The repo had no
statement of what the app needs at runtime that a person could execute — only
prose in a README, which is a promise, not a guarantee.

The module asked for a container. The interesting part is not that a container
exists; it is that a Dockerfile is the most security-sensitive file AI generates
in this course, and it can build successfully while running as root, shipping
the test suite, or copying `.env` into a layer that anyone who pulls the image
can read.

## Decision

A two-stage build on `python:3.14-slim`. The builder installs `requirements.txt`
into a virtualenv at `/opt/venv`. The runtime stage starts from the same slim
base, creates a non-root user `app` (uid 10001), copies **only** `/opt/venv`
and `app/`, switches to `USER app` before `CMD`, exposes 8000, and runs
`uvicorn app.main:app --host 0.0.0.0 --port 8000` with no `--reload`. A
`HEALTHCHECK` calls `/health` with `python -c` rather than curl, which is not in
the slim image.

Alongside it, `.dockerignore` keeps `.env`, `.env.*`, `.git`, `.github`,
virtualenvs, caches, `tests`, `docs`, `frontend` and `backend` out of the build
context entirely, and test dependencies were split into `requirements-dev.txt`
so the runtime image cannot acquire a test runner by accident.

## Alternatives considered

**A single-stage build.** Shorter and easier to read, and for a project with
four pure-Python dependencies it would produce an image of a similar size —
`fastapi`, `pydantic`, `uvicorn` and `python-dotenv` need no compiler. I
rejected it anyway, because the property I want is not "small today" but "the
runtime stage cannot inherit anything I did not name". The first C-extension
dependency this project adds would silently drag build tooling into the image
in the single-stage version, and nothing would fail to warn me.

**Keeping one `requirements.txt` with pytest and httpx in it.** This is the
obvious fix when CI cannot import pytest, and it is what I first reached for. It
means the shipped image contains a test runner it will never run, and it erases
the distinction between what the app needs and what my workflow needs. Splitting
the file cost one extra file and made both CI and the Dockerfile say exactly
what they mean.

**`python:3.14-alpine` instead of slim.** Smaller. Also musl instead of glibc,
which is a category of debugging I do not want to learn during a course module
about verification. Slim was the boring answer and the right one.

## Trade-offs

The split requirements files are the trade-off I am least comfortable with. CI
installs `requirements-dev.txt` and the image installs `requirements.txt`, which
means **the dependency set the tests run against is not the dependency set that
ships.** Nothing in the pipeline proves that the runtime-only set can even
import the app. That gap is real, it is my doing, and I chose it because the
alternative — a test runner inside the production image — is a worse thing to
be wrong about.

Second trade-off: `.dockerignore` excludes `backend/`, so the
`uvicorn backend.main:app` alias that the README offers for local use does not
exist inside the container. I could have copied `backend/` in for consistency.
I decided that two ways to start the same app is a convenience for me and a
question for everyone else, and that the image should have exactly one entry
point. I added a sentence to the README instead of a directory to the image.

Third: the health check spends a Python interpreter start-up every 30 seconds
to avoid installing curl. For an app this size that is cheap, and it keeps the
package list at zero additions. If this image ever ran somewhere that cared
about idle CPU, that is the first line I would revisit.

## Consequences

- The image is reproducible in a way the README never was: the Python version,
  the four pinned dependencies and the start command are all executable facts
  rather than instructions someone has to follow correctly.
- `docker exec tt-dev whoami` is now a check anyone can run in one line, and it
  either prints `app` or the build regressed. That is a much better test than
  reading the Dockerfile and believing it.
- Adding a runtime dependency now requires touching `requirements.txt`
  deliberately, which is the point.
- The container is **not** deployment. There is no TLS, no reverse proxy, no
  rate limiting, no process supervision, no persistence — the tasks still live
  in a dict and vanish with the container.

## Open questions

1. Should CI build the image? It would close the gap in the first trade-off —
   a job that runs `docker build` and then `docker run` plus a `/health` curl
   would prove the runtime-only dependency set actually works. I left it out
   because Module 4's CI scope is "run the tests", and I did not want to hide a
   second decision inside a workflow file.
2. What happens to this design when SQLite lands? A container with an in-memory
   store is stateless by accident. The moment `backend/data/` holds a real file,
   the image needs a volume and a decision about who owns that path — and the
   non-root user I just created is exactly who will fail to write to it.
3. Is pinning the base image by tag enough? `python:3.14-slim` moves when the
   upstream image is rebuilt. Pinning by digest would make builds truly
   reproducible and would also mean I stop receiving base-image security
   patches unless I update the digest by hand. I have not decided which of
   those two failures I prefer.

## If I started this over

I would do this differently by writing the security checks first — non-root,
no secrets in context, no test runner in the image — and only then asking for a
Dockerfile, instead of generating one and inspecting it afterwards. The
inspection worked, but every check I ran was a check I could have specified up
front, and the one thing I nearly missed (that `requirements.txt` alone cannot
run the tests) surfaced from CI, not from my reading.

---

Referenced from the [README](../../README.md#run-with-docker). Verification
commands and evidence: [`docs/module4/docker-verification.md`](../module4/docker-verification.md).
