"""Module 2 API test suite for the Task Tracker.

Covers CRUD behavior, validation, status-transition business rules, and
delete behavior. Proven meaningful via the Break Test documented in
docs/midcourse/verification.md.
"""


# ---- POST /tasks ----

def test_create_task_valid_returns_201_with_full_body(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Write report",
            "description": "Quarterly report",
            "priority": "High",
            "assignee": "aya",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Write report"
    assert body["status"] == "ToDo"
    assert body["priority"] == "High"
    assert "id" in body and "created_at" in body and "updated_at" in body


def test_create_task_missing_title_returns_422(client):
    response = client.post("/tasks", json={})
    assert response.status_code == 422


def test_create_task_blank_title_returns_422(client):
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 422


def test_create_task_invalid_priority_returns_422(client):
    response = client.post("/tasks", json={"title": "Task", "priority": "Urgent"})
    assert response.status_code == 422


def test_create_task_unknown_field_returns_422(client):
    response = client.post("/tasks", json={"title": "Task", "extra": "nope"})
    assert response.status_code == 422


# ---- GET /tasks ----

def test_list_tasks_empty_returns_200_and_empty_list(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_status_no_match_returns_200_and_empty_list(client, created_task):
    response = client.get("/tasks", params={"status": "Done"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_priority_returns_only_matches(client):
    client.post("/tasks", json={"title": "Low one", "priority": "Low"})
    client.post("/tasks", json={"title": "High one", "priority": "High"})
    response = client.get("/tasks", params={"priority": "High"})
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["High one"]


# ---- GET /tasks/{id} ----

def test_get_task_by_id_returns_task(client, created_task):
    response = client.get(f"/tasks/{created_task['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created_task["id"]


def test_get_task_by_id_not_found_returns_404_with_detail(client):
    response = client.get("/tasks/does-not-exist")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---- PATCH /tasks/{id} ----

def test_patch_partial_update_keeps_other_fields(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"title": "Updated title"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated title"
    assert body["priority"] == created_task["priority"]


def test_patch_not_found_returns_404(client):
    response = client.patch("/tasks/does-not-exist", json={"title": "x"})
    assert response.status_code == 404


def test_patch_valid_transition_todo_to_inprogress_returns_200(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"status": "InProgress"})
    assert response.status_code == 200
    assert response.json()["status"] == "InProgress"


def test_patch_invalid_transition_todo_to_done_returns_422(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"status": "Done"})
    assert response.status_code == 422


def test_patch_same_status_returns_422(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"status": "ToDo"})
    assert response.status_code == 422


# ---- DELETE /tasks/{id} ----

def test_delete_existing_returns_204_no_body(client, created_task):
    response = client.delete(f"/tasks/{created_task['id']}")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_returns_404(client):
    response = client.delete("/tasks/does-not-exist")
    assert response.status_code == 404


# ---- Due dates + overdue filter (mid-course feature) ----

def test_create_task_valid_due_date_returns_201_and_not_overdue(client):
    response = client.post(
        "/tasks",
        json={"title": "Future task", "due_date": "2099-01-01T00:00:00Z"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["due_date"].startswith("2099-01-01")
    assert body["overdue"] is False


def test_create_task_invalid_due_date_format_returns_422(client):
    response = client.post(
        "/tasks",
        json={"title": "Bad date task", "due_date": "not-a-real-date"},
    )
    assert response.status_code == 422


def test_overdue_detection_true_for_past_due_todo_task_false_once_done(client):
    create = client.post(
        "/tasks",
        json={"title": "Past due task", "due_date": "2000-01-01T00:00:00Z"},
    )
    assert create.status_code == 201
    task_id = create.json()["id"]
    assert create.json()["overdue"] is True

    # A Done task is not considered overdue even if its due date has passed.
    client.patch(f"/tasks/{task_id}", json={"status": "InProgress"})
    done = client.patch(f"/tasks/{task_id}", json={"status": "Done"})
    assert done.status_code == 200
    assert done.json()["overdue"] is False


def test_patch_updates_due_date(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"due_date": "2099-06-15T12:00:00Z"},
    )
    assert response.status_code == 200
    assert response.json()["due_date"].startswith("2099-06-15")


def test_filter_overdue_returns_only_overdue_tasks(client):
    client.post("/tasks", json={"title": "Overdue", "due_date": "2000-01-01T00:00:00Z"})
    client.post("/tasks", json={"title": "Not overdue", "due_date": "2099-01-01T00:00:00Z"})
    client.post("/tasks", json={"title": "No due date"})

    response = client.get("/tasks", params={"overdue": "true"})
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Overdue"]
