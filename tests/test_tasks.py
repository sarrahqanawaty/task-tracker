def test_create_task_valid_returns_201_with_full_body(client):
    response = client.post("/tasks", json={"title": "Buy milk"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["description"] == ""
    assert body["status"] == "ToDo"
    assert body["priority"] == "Medium"
    assert body["assignee"] is None
    assert isinstance(body["id"], str) and body["id"]
    assert "created_at" in body
    assert "updated_at" in body


def test_create_task_missing_title_returns_422(client):
    response = client.post("/tasks", json={"description": "no title"})
    assert response.status_code == 422


def test_create_task_blank_title_returns_422(client):
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 422


def test_create_task_invalid_priority_returns_422(client):
    response = client.post("/tasks", json={"title": "x", "priority": "Urgent"})
    assert response.status_code == 422


def test_create_task_unknown_field_returns_422(client):
    response = client.post("/tasks", json={"title": "x", "made_up": "value"})
    assert response.status_code == 422


def test_list_tasks_empty_returns_200_and_empty_list(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_status_no_match_returns_200_and_empty_list(client, created_task):
    response = client.get("/tasks", params={"status": "Done"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_priority_returns_only_matches(client):
    high = client.post("/tasks", json={"title": "high", "priority": "High"}).json()
    client.post("/tasks", json={"title": "low", "priority": "Low"})
    response = client.get("/tasks", params={"priority": "High"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == high["id"]
    assert body[0]["priority"] == "High"


def test_get_task_by_id_returns_task(client, created_task):
    response = client.get(f"/tasks/{created_task['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created_task["id"]
    assert response.json()["title"] == "fixture task"


def test_get_task_by_id_not_found_returns_404_with_detail(client):
    missing_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/tasks/{missing_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {missing_id} not found"


def test_patch_partial_update_keeps_other_fields(client, created_task):
    task_id = created_task["id"]
    response = client.patch(f"/tasks/{task_id}", json={"title": "updated title"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "updated title"
    assert body["status"] == created_task["status"]
    assert body["priority"] == created_task["priority"]
    assert body["description"] == created_task["description"]
    assert body["assignee"] == created_task["assignee"]
    assert body["id"] == task_id


def test_patch_not_found_returns_404(client):
    missing_id = "00000000-0000-0000-0000-000000000000"
    response = client.patch(f"/tasks/{missing_id}", json={"title": "nope"})
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {missing_id} not found"


def test_patch_valid_transition_todo_to_inprogress_returns_200(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}", json={"status": "InProgress"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "InProgress"


def test_patch_invalid_transition_todo_to_done_returns_422(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"status": "Done"})
    assert response.status_code == 422


def test_patch_same_status_returns_422(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"status": "ToDo"})
    assert response.status_code == 422


# --- Module 3 (Prompt E2): PATCH edge cases the drag-and-drop board relies on ---


def test_patch_done_to_todo_returns_422(client, created_task):
    task_id = created_task["id"]
    client.patch(f"/tasks/{task_id}", json={"status": "InProgress"})
    client.patch(f"/tasks/{task_id}", json={"status": "Done"})

    response = client.patch(f"/tasks/{task_id}", json={"status": "ToDo"})

    assert response.status_code == 422
    assert "Invalid status transition from Done to ToDo" in response.json()["detail"]


def test_patch_unknown_field_returns_422(client, created_task):
    # Mid-course update: this test used "due_date" as its example of a field the
    # API does not know about. Feature 1 made due_date a real, accepted field, so
    # the example was swapped for one that is still genuinely unknown. The intent
    # ("extra=forbid rejects unknown fields with 422") and the assertion are
    # unchanged — only the sample field name moved.
    response = client.patch(f"/tasks/{created_task['id']}", json={"estimated_hours": 3})

    assert response.status_code == 422
    body = response.json()
    assert any("estimated_hours" in str(error.get("loc", "")) for error in body["detail"])


def test_patch_invalid_status_value_returns_422(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"status": "Archived"})

    assert response.status_code == 422
    body = response.json()
    assert any("status" in str(error.get("loc", "")) for error in body["detail"])


def test_patch_blank_title_returns_422(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"title": "   "})

    assert response.status_code == 422
    assert "title cannot be blank" in str(response.json()["detail"])


def test_patch_empty_body_returns_200_and_leaves_task_unchanged(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == created_task["title"]
    assert body["status"] == created_task["status"]
    assert body["updated_at"] == created_task["updated_at"]


def test_patch_missing_id_with_status_returns_404_not_422(client):
    missing_id = "00000000-0000-0000-0000-000000000000"

    # "Done" would be an illegal transition for a real ToDo task; a missing task
    # must still answer 404, so the id check has to run before the rule check.
    response = client.patch(f"/tasks/{missing_id}", json={"status": "Done"})

    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {missing_id} not found"


def test_patch_title_only_on_done_task_returns_200(client, created_task):
    task_id = created_task["id"]
    client.patch(f"/tasks/{task_id}", json={"status": "InProgress"})
    client.patch(f"/tasks/{task_id}", json={"status": "Done"})

    # The modal omits status when it did not change, so a Done task must stay
    # editable even though Done -> Done is a rejected transition.
    response = client.patch(f"/tasks/{task_id}", json={"title": "renamed while done"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "renamed while done"
    assert body["status"] == "Done"


def test_delete_existing_returns_204_no_body(client, created_task):
    response = client.delete(f"/tasks/{created_task['id']}")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_returns_404(client):
    missing_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/tasks/{missing_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Task with id {missing_id} not found"
