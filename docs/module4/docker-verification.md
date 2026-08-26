# Docker Verification and Security Log

Module 4, Part 4.3. "The build succeeded" is not the check. The checks are:
does it answer, and who is it running as.

Image: `task-tracker:dev` · Container: `tt-dev`

## Commands and expected evidence

| # | Command | What proves it passed |
|---|---|---|
| 1 | `docker build -t task-tracker:dev .` | Build completes; the final stage is `runtime`, so no build tooling is in the shipped layers. |
| 2 | `docker run -d --name tt-dev -p 8000:8000 task-tracker:dev` | Container id printed; `docker ps` shows it `Up` with `0.0.0.0:8000->8000/tcp`. |
| 3 | `curl.exe http://127.0.0.1:8000/health` | HTTP 200 and `{"status":"ok","timestamp":"…"}` — the app is actually serving, not just the container running. |
| 4 | `docker exec tt-dev whoami` | Prints **`app`**. If it prints `root`, the `USER app` line is missing or placed after `CMD`. |
| 5 | `docker exec tt-dev ls -a /app` | Shows `app/` and nothing else — no `.env`, no `.git`, no `tests`, no `docs`. |
| 6 | `docker images task-tracker:dev` | Records the image size, for comparison if the base image is ever changed. |
| 7 | `docker inspect --format "{{.State.Health.Status}}" tt-dev` | `healthy` once the start period has elapsed — proves the `HEALTHCHECK` line actually runs. |
| 8 | `docker rm -f tt-dev` | Cleanup. `docker ps` no longer lists it. |

## Static inspection (done)

These do not need a running daemon and were checked by reading the files.

| Check | Result | Evidence |
|---|---|---|
| Base image pinned, not `python:latest` | **Pass** | `FROM python:3.14-slim` in both stages — matches the project's actual Python version. |
| Multi-stage build | **Pass** | `builder` installs into `/opt/venv`; `runtime` copies only that venv and `app/`. |
| Non-root user, created and switched to before `CMD` | **Pass** | `RUN useradd --create-home --uid 10001 app`, then `USER app`, then `EXPOSE`/`HEALTHCHECK`/`CMD`. |
| No secrets baked in | **Pass** | No `COPY .env`, no `ENV` carrying a credential, no `ARG` used as a secret. The only `ENV`s are `PATH`, two Python flags and `APP_ENV`. |
| No `--reload` in `CMD` | **Pass** | `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`. |
| `.dockerignore` excludes `.env`, `.git`, virtualenvs, caches | **Pass** | All present, plus `.env.*` with `!.env.example`, `.github`, `tests`, `docs`, `frontend`, `backend`, `node_modules`, editor and OS files. |
| Runtime image contains only what it needs | **Pass** | Only `app/` is copied. Tests, docs, the frontend and `requirements-dev.txt` are excluded, so no test runner ships in the image. |

## Security log

1. **Non-root:** the container runs as `app` (uid 10001), created in the
   runtime stage and switched to before `CMD`, so nothing after that line runs
   with root privileges.
2. **Slim base:** `python:3.14-slim` in both stages, and the builder's compiler
   layers never reach the final image — only `/opt/venv` is copied forward.
3. **No baked secrets:** `.env` and `.env.*` are excluded from the build
   context by `.dockerignore` (with `.env.example` deliberately re-included),
   and no `ENV`, `ARG` or `COPY` line carries a credential.

## Runtime evidence — collected

Real terminal output, 2026-08-26.

**1. Build**

```
$ docker build -t task-tracker:dev .
#13 68.82 Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.14.2
          click-8.5.0 fastapi-0.141.1 h11-0.16.0 httptools-0.8.0 idna-3.19 pydantic-2.13.4
          pydantic-core-2.46.4 python-dotenv-1.2.3 pyyaml-6.0.3 starlette-1.6.0
          typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.52.4 uvloop-0.22.1
          watchfiles-1.2.0 websockets-17.0.1
#15 [runtime 4/5] COPY --from=builder --chown=app:app /opt/venv /opt/venv   DONE 0.3s
#16 [runtime 5/5] COPY --chown=app:app app/ ./app/                          DONE 0.1s
#17 naming to docker.io/library/task-tracker:dev done
```

Only two `COPY` lines reach the runtime stage — the virtualenv and `app/`.

**2. Run**

```
$ docker run -d --name tt-dev -p 8000:8000 task-tracker:dev
65753d7465e263af45ce57a9c5c98699c7639827c04d76d24c55c82c5c650c40

$ docker ps --filter name=tt-dev --format "{{.Names}}  {{.Status}}  {{.Ports}}"
tt-dev  Up Less than a second (health: starting)  0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

**3. The app answers**

```
$ curl.exe -s -i http://127.0.0.1:8000/health
HTTP/1.1 200 OK
server: uvicorn
content-type: application/json

{"status":"ok","timestamp":"2026-08-26T14:31:08.581700+00:00"}
```

**4. Not root**

```
$ docker exec tt-dev whoami
app

$ docker exec tt-dev id
uid=10001(app) gid=10001(app) groups=10001(app)
```

**5. Nothing else shipped**

```
$ docker exec tt-dev ls -a /app
.  ..  app

$ docker exec tt-dev find / -maxdepth 3 -name ".env" -o -maxdepth 3 -name ".git" -o -maxdepth 3 -name "tests"
(no output)

$ docker exec tt-dev sh -c '/opt/venv/bin/pip list | grep -icE "pytest|httpx"'
0
```

The `find` returning nothing and the `pip list` count of `0` are the two checks
that prove `.dockerignore` and the split requirements files did what they were
written for: no secrets, no repository history, no test suite and no test runner
inside the image.

**6. Size and health**

```
$ docker images task-tracker:dev --format "{{.Repository}}:{{.Tag}}  {{.Size}}"
task-tracker:dev  251MB

$ docker inspect --format "{{.State.Health.Status}}" tt-dev
healthy
```

`healthy` is the `HEALTHCHECK` line proving itself — the container polled its
own `/health` and the probe passed, so that instruction is not decoration.

**7. Cleanup**

```
$ docker rm -f tt-dev
tt-dev

$ docker ps --filter name=tt-dev --format "{{.Names}}"
(no output)
```

## Result

All eight checks pass. The two that mattered most were `whoami` → `app` and the
empty `find` — a build that succeeded while running as root, or while carrying
`.env` into a layer, would have looked exactly the same up to step 3.
