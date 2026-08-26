from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.due_dates import is_task_overdue
from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate

_tasks: dict[str, TaskResponse] = {}


def _stamp_overdue(task: TaskResponse) -> TaskResponse:
    """Return a copy of `task` with a freshly computed `is_overdue`.

    Called on every read path instead of storing the flag once at write time:
    a task written yesterday with tomorrow's due date becomes overdue the day
    after without anything touching the store.

    Args:
        task (TaskResponse): The stored task.

    Returns:
        TaskResponse: A copy — the stored object is not mutated.
    """
    return task.model_copy(
        update={"is_overdue": is_task_overdue(task.due_date, task.status)}
    )


def add_task(payload: TaskCreate) -> TaskResponse:
    """Store a new task.

    ``id`` is a UUID4 and both timestamps come from one
    ``datetime.now(timezone.utc)`` call, so ``created_at`` and ``updated_at``
    are identical on a freshly created task. An omitted description is stored
    as ``""``, never as ``None``.

    Args:
        payload (TaskCreate): The validated request body.

    Returns:
        TaskResponse: The stored task with ``is_overdue`` computed.
    """
    now = datetime.now(timezone.utc)
    task_id = str(uuid4())
    task = TaskResponse(
        id=task_id,
        title=payload.title,
        description=payload.description or "",
        status=payload.status,
        priority=payload.priority,
        assignee=payload.assignee,
        due_date=payload.due_date,
        created_at=now,
        updated_at=now,
    )
    _tasks[task_id] = task
    return _stamp_overdue(task)


def get_all_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee: Optional[str] = None,
    search: Optional[str] = None,
    overdue: Optional[bool] = None,
) -> list[TaskResponse]:
    """Return every task, narrowed by whichever filters were supplied.

    Mid-course Feature 2: the filters combine with AND — passing `status` and
    `priority` together returns only the tasks that match both. A filter left
    as None is simply not applied, so the existing `GET /tasks` behaviour is
    unchanged.

    Args:
        status (TaskStatus | None): Exact status match.
        priority (TaskPriority | None): Exact priority match.
        assignee (str | None): Exact match after stripping and case-folding;
            a whitespace-only value is ignored.
        search (str | None): Case-insensitive substring match on title and
            description; a whitespace-only value is ignored.
        overdue (bool | None): Match on the recomputed ``is_overdue`` flag.

    Returns:
        list[TaskResponse]: The matching tasks, each stamped with a fresh
        ``is_overdue``. Empty when nothing matches.
    """
    tasks = [_stamp_overdue(task) for task in _tasks.values()]

    if status is not None:
        tasks = [task for task in tasks if task.status == status]

    if priority is not None:
        tasks = [task for task in tasks if task.priority == priority]

    if assignee is not None:
        # Exact match, but case- and whitespace-insensitive: "Sarah" and
        # " sarah " should find the same tasks.
        wanted = assignee.strip().casefold()
        if wanted:
            tasks = [
                task
                for task in tasks
                if task.assignee is not None
                and task.assignee.strip().casefold() == wanted
            ]

    if search is not None:
        # A blank or whitespace-only search box means "no search", not
        # "match nothing" — otherwise clearing the input would empty the board.
        needle = search.strip().casefold()
        if needle:
            tasks = [
                task
                for task in tasks
                if needle in task.title.casefold()
                or needle in task.description.casefold()
            ]

    if overdue is not None:
        tasks = [task for task in tasks if task.is_overdue == overdue]

    return tasks


def get_task_by_id(task_id: str) -> Optional[TaskResponse]:
    """Look up one task.

    Args:
        task_id (str): The task id.

    Returns:
        TaskResponse | None: The task with ``is_overdue`` recomputed, or
        ``None`` when the id is unknown. Storage never raises HTTP errors —
        the route layer turns ``None`` into a 404.
    """
    task = _tasks.get(task_id)
    if task is None:
        return None
    return _stamp_overdue(task)


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    """Apply a partial update to a task.

    Only the keys the client actually sent are applied
    (``model_dump(exclude_unset=True)``). An empty body is a no-op that leaves
    ``updated_at`` untouched; any real change refreshes ``updated_at`` with a
    server-generated UTC timestamp. The merged task is revalidated through
    ``TaskResponse`` rather than mutated in place.

    This function does not check the status-transition rules — the route does
    that before calling it.

    Args:
        task_id (str): The task id.
        payload (TaskUpdate): The validated partial body.

    Returns:
        TaskResponse | None: The updated task with ``is_overdue`` recomputed,
        or ``None`` when the id is unknown.
    """
    existing = _tasks.get(task_id)
    if existing is None:
        return None
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return _stamp_overdue(existing)
    data = existing.model_dump()
    data.update(changes)
    data["updated_at"] = datetime.now(timezone.utc)
    updated = TaskResponse(**data)
    _tasks[task_id] = updated
    return _stamp_overdue(updated)


def delete_task(task_id: str) -> bool:
    """Remove a task from the store.

    Args:
        task_id (str): The task id.

    Returns:
        bool: ``True`` if a task was removed, ``False`` if the id was unknown.
    """
    if task_id not in _tasks:
        return False
    del _tasks[task_id]
    return True


def _reset() -> None:
    """Empty the store.

    Test-only. ``tests/conftest.py`` calls this in an autouse fixture before
    and after every test so the module-level dict cannot leak state between
    them.

    Returns:
        None
    """
    _tasks.clear()
