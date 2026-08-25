"""Mid-course project tests.

Feature 1 — Due dates + overdue filter
Feature 2 — Search + combined filters

These run alongside the Module 1-3 suite in `test_tasks.py` and reuse the same
`client` / `created_task` fixtures and the autouse storage reset from
`conftest.py`, so each test starts from an empty store.
"""

from datetime import date, datetime, timedelta, timezone

from app.due_dates import is_task_overdue

TODAY = datetime.now(timezone.utc).date()
YESTERDAY = TODAY - timedelta(days=1)
LAST_WEEK = TODAY - timedelta(days=7)
TOMORROW = TODAY + timedelta(days=1)


def _iso(value: date) -> str:
    return value.isoformat()


def _make(client, **fields):
    """Create a task and return its response body."""
    payload = {"title": "task"}
    payload.update(fields)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _advance_to_done(client, task_id):
    """Walk a task through the only legal path to Done: ToDo -> InProgress -> Done."""
    assert client.patch(f"/tasks/{task_id}", json={"status": "InProgress"}).status_code == 200
    assert client.patch(f"/tasks/{task_id}", json={"status": "Done"}).status_code == 200


# ---------------------------------------------------------------------------
# Feature 1 — due dates
# ---------------------------------------------------------------------------


def test_create_task_with_valid_due_date_returns_201_and_echoes_it(client):
    body = _make(client, title="Ship report", due_date=_iso(TOMORROW))

    assert body["due_date"] == _iso(TOMORROW)
    assert body["is_overdue"] is False


def test_create_task_with_invalid_due_date_format_returns_422(client):
    response = client.post("/tasks", json={"title": "x", "due_date": "26-08-2026"})

    assert response.status_code == 422
    assert any("due_date" in str(error.get("loc", "")) for error in response.json()["detail"])


def test_task_without_due_date_is_never_overdue(client, created_task):
    assert created_task["due_date"] is None
    assert created_task["is_overdue"] is False


def test_past_due_date_marks_task_overdue(client):
    body = _make(client, title="Late invoice", due_date=_iso(YESTERDAY))

    assert body["is_overdue"] is True


def test_due_date_today_is_not_yet_overdue(client):
    # The task still has the whole of today to be finished.
    body = _make(client, title="Due today", due_date=_iso(TODAY))

    assert body["is_overdue"] is False


def test_done_task_with_past_due_date_is_not_overdue(client):
    body = _make(client, title="Finished late", due_date=_iso(LAST_WEEK))
    assert body["is_overdue"] is True

    _advance_to_done(client, body["id"])

    response = client.get(f"/tasks/{body['id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "Done"
    assert response.json()["is_overdue"] is False


def test_patch_can_update_and_clear_the_due_date(client):
    body = _make(client, title="Movable deadline", due_date=_iso(YESTERDAY))
    task_id = body["id"]

    moved = client.patch(f"/tasks/{task_id}", json={"due_date": _iso(TOMORROW)})
    assert moved.status_code == 200
    assert moved.json()["due_date"] == _iso(TOMORROW)
    assert moved.json()["is_overdue"] is False

    cleared = client.patch(f"/tasks/{task_id}", json={"due_date": None})
    assert cleared.status_code == 200
    assert cleared.json()["due_date"] is None
    assert cleared.json()["is_overdue"] is False


def test_patch_unrelated_field_preserves_the_due_date(client):
    body = _make(client, title="Keep my date", due_date=_iso(TOMORROW))

    response = client.patch(f"/tasks/{body['id']}", json={"title": "Renamed"})

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"
    assert response.json()["due_date"] == _iso(TOMORROW)


def test_overdue_filter_returns_only_overdue_tasks(client):
    late = _make(client, title="Late", due_date=_iso(YESTERDAY))
    _make(client, title="Upcoming", due_date=_iso(TOMORROW))
    _make(client, title="No date")

    response = client.get("/tasks", params={"overdue": "true"})

    assert response.status_code == 200
    body = response.json()
    assert [task["id"] for task in body] == [late["id"]]


def test_overdue_filter_false_excludes_overdue_tasks(client):
    _make(client, title="Late", due_date=_iso(YESTERDAY))
    upcoming = _make(client, title="Upcoming", due_date=_iso(TOMORROW))

    response = client.get("/tasks", params={"overdue": "false"})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [upcoming["id"]]


def test_is_task_overdue_unit_rules():
    """The rule on its own, with an explicit `today` so the clock cannot flake."""
    reference = date(2026, 8, 25)

    assert is_task_overdue(date(2026, 8, 24), "ToDo", today=reference) is True
    assert is_task_overdue(date(2026, 8, 25), "ToDo", today=reference) is False
    assert is_task_overdue(date(2026, 8, 26), "ToDo", today=reference) is False
    assert is_task_overdue(date(2026, 8, 24), "Done", today=reference) is False
    assert is_task_overdue(None, "ToDo", today=reference) is False


# ---------------------------------------------------------------------------
# Feature 2 — search and combined filters
# ---------------------------------------------------------------------------


def test_search_matches_title_case_insensitively(client):
    wanted = _make(client, title="Fix the LOGIN bug")
    _make(client, title="Write release notes")

    response = client.get("/tasks", params={"search": "login"})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [wanted["id"]]


def test_search_also_matches_description(client):
    wanted = _make(client, title="Unrelated title", description="Refund the customer")
    _make(client, title="Another task", description="Nothing to see")

    response = client.get("/tasks", params={"search": "refund"})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [wanted["id"]]


def test_blank_search_is_ignored_and_returns_every_task(client):
    _make(client, title="One")
    _make(client, title="Two")

    response = client.get("/tasks", params={"search": "   "})

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_search_with_no_matches_returns_200_and_empty_list(client, created_task):
    response = client.get("/tasks", params={"search": "nothing-matches-this"})

    assert response.status_code == 200
    assert response.json() == []


def test_filter_by_assignee_is_case_insensitive(client):
    wanted = _make(client, title="Hers", assignee="Sarah")
    _make(client, title="His", assignee="Omar")

    response = client.get("/tasks", params={"assignee": "  sarah "})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [wanted["id"]]


def test_status_and_priority_combine_with_and(client):
    wanted = _make(client, title="Both", status="InProgress", priority="High")
    _make(client, title="Right status only", status="InProgress", priority="Low")
    _make(client, title="Right priority only", status="ToDo", priority="High")

    response = client.get("/tasks", params={"status": "InProgress", "priority": "High"})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [wanted["id"]]


def test_search_combines_with_assignee_and_overdue(client):
    wanted = _make(
        client,
        title="Chase the invoice",
        assignee="Sarah",
        due_date=_iso(YESTERDAY),
    )
    # Same words, same person, but not overdue.
    _make(client, title="Chase the invoice later", assignee="Sarah", due_date=_iso(TOMORROW))
    # Overdue and matching text, but a different assignee.
    _make(client, title="Chase the invoice", assignee="Omar", due_date=_iso(YESTERDAY))

    response = client.get(
        "/tasks",
        params={"search": "invoice", "assignee": "Sarah", "overdue": "true"},
    )

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [wanted["id"]]


def test_invalid_priority_filter_value_returns_422(client):
    response = client.get("/tasks", params={"priority": "Urgent"})

    assert response.status_code == 422
    assert any("priority" in str(error.get("loc", "")) for error in response.json()["detail"])


def test_invalid_overdue_filter_value_returns_422(client):
    response = client.get("/tasks", params={"overdue": "maybe"})

    assert response.status_code == 422
