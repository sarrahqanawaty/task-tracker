# Prompt Comparison Log — POST /tasks (Prompt E1)

Comparing a vague prompt against a strict one for the same task: adding
`POST /tasks` to this project.

**How the weak output was obtained:** the vague prompt below was answered by an
AI assistant with no project files attached — the same conditions a student
would create by typing it into a fresh chat. The improved output is the code
actually in `app/main.py`, produced from the strict prompt (Prompt B1).

---

## The two prompts

**Weak prompt**

> Write a POST /tasks endpoint using FastAPI.

**Improved prompt (B1, abbreviated)**

> You are a senior Python backend engineer. Add ONE route to my existing
> FastAPI app.
>
> Context files: `@app/main.py`, `@app/models.py`, `@app/storage.py`
>
> Exact specification: route `POST /tasks`; status code 201 via
> `status.HTTP_201_CREATED`; tags `["tasks"]`; request body `TaskCreate`;
> response model `TaskResponse`; behavior: call `storage.add_task(payload)` and
> return the result directly.
>
> DO NOT create a new `FastAPI()` instance. DO NOT generate UUIDs or timestamps
> in the route. DO NOT add manual validation. DO NOT add try/except. DO NOT add
> any other route.

---

## Weak output

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI()

class Task(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

tasks = []

@app.post("/tasks")
def create_task(task: Task):
    new_task = {"id": str(uuid.uuid4()), **task.dict()}
    tasks.append(new_task)
    return {"message": "Task created", "task": new_task}
```

### Weak output observations

1. **It created a second `FastAPI()` instance.** Dropped into `app/main.py`
   this shadows the real app, and every existing route — including `/health` —
   silently disappears.
2. **It invented its own model.** `Task` with a `completed: bool` field. The
   project's `TaskStatus` enum (ToDo / InProgress / Done) and `TaskPriority`
   do not exist in its version, so the three-state workflow is gone.
3. **It returned the default 200, not 201.** No `status_code` argument at all.
4. **It used a plain list and generated the id in the route.** The project's
   `storage.py` layer is bypassed entirely, and id creation moves into the
   route where it does not belong.
5. **It wrapped the result in a message envelope.** `{"message": ..., "task":
   ...}` instead of returning the task object, so no `response_model` and an
   unpredictable body shape.
6. **It used Pydantic v1 syntax.** `.dict()` is deprecated in v2 — the project
   pins Pydantic 2.13.4.

---

## Improved output

```python
@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    return storage.add_task(payload)
```

### Improved output observations

1. **Two lines of logic.** Everything else — validation, id, timestamps — is
   handled by the layers that own it.
2. **Uses the existing `app`.** No new instance, so `/health` and every other
   route survive.
3. **201 stated explicitly** via `status.HTTP_201_CREATED`.
4. **Real project models.** `TaskCreate` in, `TaskResponse` out, so the enums
   and the `extra="forbid"` rules apply automatically.
5. **`tags=["tasks"]`** groups the route in Swagger.
6. **No try/except.** Errors surface as real HTTP status codes rather than
   being swallowed.

---

## Comparison

| Prompt difference | Weak output risk | Improved output benefit | What I learned |
|---|---|---|---|
| Attaching real files vs. no context | Invents `Task`, `completed`, a new `tasks` list — none exist here | Uses `TaskCreate`, `TaskResponse`, `storage.add_task` | Without attached files the AI writes a generic tutorial, not my project |
| Naming the exact status code | Returns 200; a REST client cannot tell "created" from "fetched" | Returns 201 as the spec requires | Status codes are part of the contract and must be stated |
| Saying "use the existing app instance" | New `FastAPI()` deletes `/health` and every other route | One app, all routes intact | The most destructive AI mistakes are silent ones |
| Naming the storage layer | Ids created in the route; a parallel `tasks` list appears | `storage.add_task` stays the single source of truth | Naming the layer keeps responsibilities where they belong |
| Specifying `response_model` | Ad-hoc `{"message": ...}` envelope | Predictable `TaskResponse` shape, documented in Swagger | The response shape needs specifying or the AI invents one |
| Explicit DO NOT list | Pydantic v1 `.dict()`, manual id generation | Constraints respected | DO NOT rules block known failure modes before they happen |

---

## Conclusion

The weak prompt did not produce *worse-looking* code — it produced plausible
code for a different project. It reads fine in isolation, which is exactly what
makes it dangerous: applying it would have deleted `/health` and split task
storage into two places, and nothing about the snippet warns you.

The strict prompt's value is not politeness or length. It is that every line
of the output is checkable against something I specified in advance.
