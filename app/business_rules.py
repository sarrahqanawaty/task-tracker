from fastapi import HTTPException, status

from app.models import TaskStatus

VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset({
    (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
    (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
    (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
})


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    """Reject a status change that is not in ``VALID_TRANSITIONS``.

    The allowed moves are ``ToDo -> InProgress``, ``InProgress -> Done`` and
    ``Done -> InProgress``. Everything else is rejected, including a
    same-to-same move such as ``ToDo -> ToDo`` and any backward move such as
    ``Done -> ToDo``.

    Args:
        current (TaskStatus): The task's stored status.
        new (TaskStatus): The status requested by the client.

    Returns:
        None: Returns nothing when the transition is allowed.

    Raises:
        HTTPException: 422 whose ``detail`` names both statuses and lists the
            allowed transitions, e.g. ``"Invalid status transition from Done to
            ToDo. Allowed transitions: [...]"``.
    """
    # Same -> same is invalid. Anything not in VALID_TRANSITIONS is invalid.
    if (current, new) not in VALID_TRANSITIONS:
        allowed = sorted({f"{f.value}->{t.value}" for f, t in VALID_TRANSITIONS})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status transition from {current.value} to {new.value}. Allowed transitions: {allowed}",
        )
