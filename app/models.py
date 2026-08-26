from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class TaskStatus(str, Enum):
    """The three task statuses.

    A ``str`` Enum on purpose: ``TaskStatus.DONE == "Done"`` is True, which is
    what lets ``app.due_dates`` compare against the plain string ``"Done"``
    without importing this module.
    """

    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    """The three task priorities. ``MEDIUM`` is the default on create."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


def _validate_title(value: str) -> str:
    """Normalise and check a task title.

    Args:
        value (str): The raw title from the request body.

    Returns:
        str: The title with surrounding whitespace removed. The stripped value
        is what gets stored, so ``"  Buy milk  "`` is stored as ``"Buy milk"``.

    Raises:
        ValueError: If the title is blank or whitespace-only, or if it exceeds
            200 characters after stripping. Pydantic converts this into a 422
            response naming the ``title`` field.
    """
    stripped = value.strip()
    if not stripped:
        raise ValueError("title cannot be blank")
    if len(stripped) > 200:
        raise ValueError("title cannot exceed 200 characters")
    return stripped


class TaskCreate(BaseModel):
    """Request body for ``POST /tasks``.

    ``extra="forbid"`` means an unknown key is a 422, not a silently ignored
    field. Server-owned values (``id``, ``created_at``, ``updated_at``,
    ``is_overdue``) are absent here by design, so a client cannot set them.
    """

    model_config = ConfigDict(extra="forbid")

    title: str
    description: Optional[str] = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    # Mid-course Feature 1. Optional, so every task created before this change
    # is still valid. Pydantic parses an ISO "YYYY-MM-DD" string and rejects
    # anything else with 422 — no hand-written date parsing needed.
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_must_be_valid(cls, value: str) -> str:
        """Apply the shared title rules on create.

        Args:
            value (str): The submitted title.

        Returns:
            str: The stripped title.

        Raises:
            ValueError: If the title is blank or longer than 200 characters.
        """
        return _validate_title(value)


class TaskUpdate(BaseModel):
    """Request body for ``PATCH /tasks/{task_id}``.

    Every field is optional. What matters is the difference between a key that
    is absent and a key sent as ``null``: ``storage.update_task`` uses
    ``model_dump(exclude_unset=True)``, so an absent key leaves the value alone
    while an explicit ``null`` clears it.
    """

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    # Sending `"due_date": null` explicitly clears the date; leaving the key out
    # of the body leaves it untouched. That difference is what `exclude_unset`
    # in storage.update_task preserves.
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_must_be_valid(cls, value: Optional[str]) -> Optional[str]:
        """Apply the shared title rules on update, skipping an absent title.

        Args:
            value (str | None): The submitted title, or ``None`` when the
                client did not send one.

        Returns:
            str | None: The stripped title, or ``None`` unchanged.

        Raises:
            ValueError: If a title was sent and is blank or longer than 200
                characters.
        """
        if value is None:
            return value
        return _validate_title(value)


class TaskResponse(BaseModel):
    """Response body for every task route.

    Also the shape stored in ``app.storage``, which is why ``extra="forbid"``
    matters here: ``storage.update_task`` round-trips a task through
    ``model_dump()`` and back into this model, so any key that appears in the
    dump but is not a declared field would raise.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    # Derived, never sent by the client: the storage layer recomputes it on
    # every read so it can never go stale as the calendar moves forward.
    is_overdue: bool = False
    created_at: datetime
    updated_at: datetime
