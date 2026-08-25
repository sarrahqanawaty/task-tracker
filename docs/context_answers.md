# Tool Setup Answers (Prompts T0.1 and T0.2)

These two prompts produce explanation, not code. Their purpose is to prove the
assistant is reading the real project rather than guessing. The answers below
were produced by reading `app/main.py` and the surrounding files directly.

---

## T0.1 — Explain the existing `/health` endpoint

**1. Route path and HTTP method**

`GET /health`, declared with `@app.get("/health", tags=["system"])` in
`app/main.py`. The `tags=["system"]` argument groups it separately from the
task routes in Swagger UI.

**2. What the route returns**

A JSON object with two string fields:

```json
{"status": "ok", "timestamp": "2026-08-24T10:11:56.539286+00:00"}
```

`status` is the constant `"ok"`. `timestamp` is generated per request with
`datetime.now(timezone.utc).isoformat()`, so it is the current UTC time in
ISO 8601 format and differs on every call. There is no `status_code` argument
on the decorator, so FastAPI's default 200 applies.

**3. Does it use the existing FastAPI app instance?**

Yes. There is exactly one `FastAPI()` instance in the project, created at
module level in `app/main.py` as `app`, and every route — `/health` and all
five task routes — is registered on it with `@app.<method>`. No second instance
exists anywhere.

**4. One command to verify it returns HTTP 200**

With the server running:

```
curl.exe -i http://127.0.0.1:8000/health
```

The first response line should read `HTTP/1.1 200 OK`. In a browser, visiting
`http://127.0.0.1:8000/health` shows the JSON body, and
`http://127.0.0.1:8000/docs` lists the route in Swagger UI where it can be
called with **Try it out**.

---

## T0.2 — Confirm project context

**1. Current FastAPI app variable name**

`app`, defined in `app/main.py`:

```python
app = FastAPI(
    title="Task Tracker API",
    description="A minimal REST API for tracking tasks.",
    version="0.1.0",
)
```

**2. Existing routes**

| Method | Path | Tags |
|---|---|---|
| GET | `/health` | `system` |
| POST | `/tasks` | `tasks` |
| GET | `/tasks` | `tasks` |
| GET | `/tasks/{task_id}` | `tasks` |
| PATCH | `/tasks/{task_id}` | `tasks` |
| DELETE | `/tasks/{task_id}` | `tasks` |

**3. Do `models.py`, `storage.py`, and a tests directory exist?**

All three exist:

- `app/models.py` — the enums and the three Pydantic models
- `app/storage.py` — the in-memory dict and its six functions
- `app/business_rules.py` — the transition rules
- `tests/` — `conftest.py`, `test_tasks.py`, `verify_a.py`,
  `verify_transitions.py`

**4. Imports and structure to preserve**

- **One app instance.** `app` in `app/main.py`. Never create a second
  `FastAPI()`.
- **`backend/main.py` is a thin re-export** that imports `app` from
  `app.main`, so the older `uvicorn backend.main:app` command still works.
  It holds no routes of its own.
- **`load_dotenv()` runs before** `APP_ENV` and `PORT` are read, so the `.env`
  file is loaded first.
- **Layer boundaries:** routes call `storage` functions; `storage` generates
  `id`, `created_at`, and `updated_at`; `business_rules` owns transition
  validation. Routes should not generate ids or timestamps themselves.
- **Pydantic v2 only** — `ConfigDict` and `field_validator`, never `@validator`,
  `class Config`, or `.dict()`.

---

## Checklist before applying AI-generated code

1. Does it create a new `FastAPI()` instance? If yes, reject it.
2. Does it import from `app.models` and `app.storage`, or invent its own
   models and lists?
3. Is the status code explicit and correct — 201 for POST, 204 for DELETE?
4. Does it generate ids or timestamps in the route instead of in storage?
5. Is it Pydantic v2 syntax throughout?
6. Does it touch routes it was not asked to touch?
7. Does it wrap storage calls in `try/except` to hide errors?
