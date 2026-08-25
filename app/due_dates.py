"""Mid-course Feature 1: due dates.

A tiny, pure module — the same shape as `business_rules.py`. It knows one rule
and imports nothing from the rest of the app, so it can be unit-tested on its
own and cannot create an import cycle with `models.py`.

Design decision (see docs/midcourse/mini-adr.md): "overdue" is computed in the
BACKEND, not in the browser. The rule then lives in one place, is covered by
pytest, and every client that talks to the API sees the same answer.
"""

from datetime import date, datetime, timezone
from typing import Optional

# Compared as a plain string on purpose: TaskStatus is a `str` Enum, so
# `TaskStatus.DONE == "Done"` is True. Keeping the comparison string-based is
# what lets this module stay free of any import from `app.models`.
DONE_STATUS = "Done"


def today_utc() -> date:
    """Today's date in UTC.

    Isolated in its own function so tests can pass an explicit `today` instead
    of depending on the machine clock.
    """
    return datetime.now(timezone.utc).date()


def is_task_overdue(
    due_date: Optional[date],
    status: str,
    today: Optional[date] = None,
) -> bool:
    """A task is overdue when it has a due date, that date is in the past, and
    the work is not finished.

    - No due date        -> never overdue (the field is optional).
    - Status is Done     -> never overdue, however old the due date is.
    - Due date == today  -> NOT overdue; the task still has the whole day.
    """
    if due_date is None:
        return False
    if status == DONE_STATUS:
        return False
    if today is None:
        today = today_utc()
    return due_date < today
