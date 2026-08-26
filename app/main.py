"""Task Tracker API — project skeleton.

Creates the FastAPI application instance and exposes a /health endpoint
plus task create.
"""

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from typing import Optional

from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate
from app import storage
from app.business_rules import validate_status_transition

# Loads variables from a .env file at the project root, if one exists.
# Values already present in the real environment are not overwritten.
load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(
    title="Task Tracker API",
    description="A minimal REST API for tracking tasks.",
    version="0.2.0",
)

# Module 3 (Prompt B4): the browser blocks fetch() from the frontend page to
# this API unless the API answers with CORS headers. Only the local frontend
# origins are allowed — no wildcard, no credentials, no other middleware.
ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Report that the service is alive.

    Returns:
        dict[str, str]: ``{"status": "ok", "timestamp": <ISO-8601 UTC string>}``.
        The timestamp is generated per request, so it differs every call.

    Example:
        ``GET /health`` -> ``200``::

            {"status": "ok", "timestamp": "2026-08-26T09:15:42.123456+00:00"}
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    """Create a task.

    Validation happens in ``TaskCreate`` before this function runs: a blank or
    over-long title, an unknown status or priority, a malformed ``due_date`` or
    any unknown field is rejected by FastAPI with 422.

    Args:
        payload (TaskCreate): The validated request body.

    Returns:
        TaskResponse: The stored task, with a server-generated ``id``,
        ``created_at`` and ``updated_at``, and a freshly computed
        ``is_overdue``. Answered with HTTP 201.

    Example:
        ``POST /tasks`` with ``{"title": "Buy milk"}`` -> ``201`` with
        ``status`` ``"ToDo"``, ``priority`` ``"Medium"`` and ``description``
        ``""``.
    """
    return storage.add_task(payload)


@app.get("/tasks", response_model=list[TaskResponse], tags=["tasks"])
def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    # Mid-course Feature 2: these three are additive. Every filter left out
    # behaves exactly as before, and supplying several combines them with AND.
    assignee: Optional[str] = None,
    search: Optional[str] = Query(
        default=None,
        max_length=200,
        description="Case-insensitive substring match on title and description.",
    ),
    overdue: Optional[bool] = Query(
        default=None,
        description="true = only overdue tasks, false = only tasks that are not overdue.",
    ),
) -> list[TaskResponse]:
    """List tasks, narrowed by whichever filters were supplied.

    Filters combine with AND. A filter that is not supplied is not applied, so
    a bare ``GET /tasks`` returns everything.

    Args:
        status (TaskStatus | None): Exact status match.
        priority (TaskPriority | None): Exact priority match.
        assignee (str | None): Exact match, case- and whitespace-insensitive.
            A blank or whitespace-only value is ignored.
        search (str | None): Case-insensitive substring match on title and
            description, max 200 characters. A blank or whitespace-only value
            is ignored — it means "no filter", not "match nothing".
        overdue (bool | None): ``true`` returns only overdue tasks, ``false``
            only tasks that are not overdue.

    Returns:
        list[TaskResponse]: Matching tasks, each with ``is_overdue``
        recomputed. An empty list when nothing matches — never 404.

    Example:
        ``GET /tasks?search=invoice&assignee=Sarah&overdue=true`` -> ``200``
        with the tasks that satisfy all three conditions.
    """
    return storage.get_all_tasks(
        status=status,
        priority=priority,
        assignee=assignee,
        search=search,
        overdue=overdue,
    )


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: str) -> TaskResponse:
    """Return one task by id.

    Args:
        task_id (str): The task id from the path. Typed as ``str``, not as a
            UUID, so a malformed id is a lookup miss rather than a 422.

    Returns:
        TaskResponse: The task, with ``is_overdue`` recomputed.

    Raises:
        HTTPException: 404 with detail ``"Task with id {task_id} not found"``
            when no task has that id.
    """
    task = storage.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def update_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    """Partially update a task.

    Only the fields present in the body are changed; an omitted key is left
    untouched, while an explicit ``null`` clears the value. An empty body is a
    successful no-op that leaves ``updated_at`` unchanged.

    The status-transition rule runs **only** when the body carries ``status``,
    and the task is looked up first, so a request for a missing id answers 404
    rather than a transition error.

    Args:
        task_id (str): The task id from the path.
        payload (TaskUpdate): The validated partial body.

    Returns:
        TaskResponse: The updated task, with ``is_overdue`` recomputed.

    Raises:
        HTTPException: 404 with detail ``"Task with id {task_id} not found"``
            when no task has that id; 422 from
            ``business_rules.validate_status_transition`` when the requested
            status change is not in the allowed set.

    Example:
        ``PATCH /tasks/{id}`` with ``{"status": "Done"}`` on a ``ToDo`` task ->
        ``422``; the same body on an ``InProgress`` task -> ``200``.
    """
    if payload.status is not None:
        existing = storage.get_task_by_id(task_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        validate_status_transition(existing.status, payload.status)
    updated = storage.update_task(task_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return updated


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: str) -> None:
    """Delete a task.

    Deletion ignores the status-transition rules: any task can be deleted from
    any status.

    Args:
        task_id (str): The task id from the path.

    Returns:
        None: Answered with HTTP 204 and an empty body.

    Raises:
        HTTPException: 404 with detail ``"Task with id {task_id} not found"``
            when no task has that id.
    """
    if not storage.delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    import uvicorn

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=PORT,
        reload=(APP_ENV == "development"),
    )
