# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1 — builder: install dependencies into a virtual environment.
# Nothing from this stage reaches the final image except the venv itself.
# ---------------------------------------------------------------------------
FROM python:3.14-slim AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt ./

# A venv rather than a system install: the runtime stage copies one directory
# and inherits nothing else from the builder.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 — runtime: same slim base, no build tooling, no test runner.
# ---------------------------------------------------------------------------
FROM python:3.14-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

# Non-root from here on. Created before the COPYs so ownership can be set in
# the same layer instead of with a second `chown -R` pass.
RUN useradd --create-home --uid 10001 app

WORKDIR /app

COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --chown=app:app app/ ./app/

USER app

EXPOSE 8000

# `python -c` rather than curl: curl is not in the slim image and installing it
# would add a package the app never uses.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]

# No --reload in a container: the reloader watches the filesystem and spawns a
# second process, which is wrong for an image and hides the real PID 1.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
