from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


def _validate_title(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("title cannot be blank")
    if len(stripped) > 200:
        raise ValueError("title cannot exceed 200 characters")
    return stripped


class TaskCreate(BaseModel):
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
        return _validate_title(value)


class TaskUpdate(BaseModel):
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
        if value is None:
            return value
        return _validate_title(value)


class TaskResponse(BaseModel):
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
