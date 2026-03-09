"""CRUD endpoint tests."""
import pytest


# ── POST /tasks ───────────────────────────────────────────────────────────────

def test_create_returns_201(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Buy milk"})
    assert r.status_code == 201


def test_create_has_id(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Buy milk"})
    assert "id" in r.json()
    assert len(r.json()["id"]) == 36  # uuid


def test_create_has_created_at(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Buy milk"})
    assert r.json()["created_at"] is not None


def test_create_status_open(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Buy milk"})
    assert r.json()["status"] == "open"


def test_create_parses_priority(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Urgent task !1"})
    assert r.json()["priority"] == 1


def test_create_parses_tags(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Research paper #research #work"})
    assert set(r.json()["tags"]) == {"research", "work"}


def test_create_parses_location(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Do work @desk"})
    assert r.json()["location"] == "desk"


def test_create_parses_due(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Deadline ^2024-01-15"})
    assert r.json()["due"] is not None
    assert "2024-01-15" in r.json()["due"]


def test_create_parses_assignee_agent(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Analyse paper +paper.analyser"})
    assert r.json()["assignee_agent"] == "paper.analyser"


def test_create_parses_assignee_human(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Review ++alice"})
    assert r.json()["assignee_human"] == "alice"


def test_create_no_tokens_has_null_fields(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Simple task"})
    data = r.json()
    assert data["priority"] is None
    assert data["tags"] == []
    assert data["location"] is None
    assert data["due"] is None
    assert data["assignee_agent"] is None
    assert data["assignee_human"] is None


def test_create_source_pipeline_override(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "From pipeline", "source_pipeline": "rtm", "source_agent": "import"})
    assert r.json()["source_pipeline"] == "rtm"
    assert r.json()["source_agent"] == "import"


def test_create_name_strips_tokens(client_with_insert):
    client, _ = client_with_insert
    r = client.post("/tasks", json={"text": "Buy milk !1 #shopping @store"})
    assert r.json()["name"] == "Buy milk"


# ── GET /tasks/{id} ───────────────────────────────────────────────────────────

def test_get_returns_task(client_with_insert):
    client, insert = client_with_insert
    task_id = insert("Read book #reading")
    r = client.get(f"/tasks/{task_id}")
    assert r.status_code == 200
    assert r.json()["id"] == task_id


def test_get_404_for_missing(client_with_insert):
    client, _ = client_with_insert
    r = client.get("/tasks/nonexistent-id")
    assert r.status_code == 404


# ── GET /tasks ────────────────────────────────────────────────────────────────

def test_list_returns_open_by_default(client_with_insert):
    client, insert = client_with_insert
    insert("Open task")
    insert("Closed task", status="closed", completed_at="2024-01-01T00:00:00+00:00")
    r = client.get("/tasks")
    assert r.status_code == 200
    statuses = [t["status"] for t in r.json()]
    assert all(s == "open" for s in statuses)
    assert len(statuses) == 1


def test_list_status_all_includes_closed(client_with_insert):
    client, insert = client_with_insert
    insert("Open task")
    insert("Closed task", status="closed", completed_at="2024-01-01T00:00:00+00:00")
    r = client.get("/tasks?status=all")
    statuses = [t["status"] for t in r.json()]
    assert "open" in statuses
    assert "closed" in statuses


def test_list_status_closed(client_with_insert):
    client, insert = client_with_insert
    insert("Open task")
    insert("Closed task", status="closed", completed_at="2024-01-01T00:00:00+00:00")
    r = client.get("/tasks?status=closed")
    statuses = [t["status"] for t in r.json()]
    assert all(s == "closed" for s in statuses)
    assert len(statuses) == 1


def test_list_ordered_priority_null_last(client_with_insert):
    client, insert = client_with_insert
    insert("No priority task")
    insert("High priority !1")
    insert("Medium priority !2")
    r = client.get("/tasks")
    priorities = [t["priority"] for t in r.json()]
    # nulls should be last
    none_idx = [i for i, p in enumerate(priorities) if p is None]
    non_none_idx = [i for i, p in enumerate(priorities) if p is not None]
    if none_idx and non_none_idx:
        assert max(non_none_idx) < min(none_idx)


# ── PATCH /tasks/{id} ─────────────────────────────────────────────────────────

def test_update_text_reparses_fields(client_with_insert):
    client, insert = client_with_insert
    task_id = insert("Original task")
    r = client.patch(f"/tasks/{task_id}", json={"text": "Updated task !2 #newtag"})
    assert r.status_code == 200
    data = r.json()
    assert data["priority"] == 2
    assert "newtag" in data["tags"]


def test_update_status_closed_sets_completed_at(client_with_insert):
    client, insert = client_with_insert
    task_id = insert("Task to close")
    r = client.patch(f"/tasks/{task_id}", json={"status": "closed"})
    assert r.status_code == 200
    assert r.json()["completed_at"] is not None
    assert r.json()["status"] == "closed"


def test_update_status_open_clears_completed_at(client_with_insert):
    client, insert = client_with_insert
    task_id = insert("Closed task", status="closed", completed_at="2024-01-01T00:00:00+00:00")
    r = client.patch(f"/tasks/{task_id}", json={"status": "open"})
    assert r.status_code == 200
    assert r.json()["completed_at"] is None
    assert r.json()["status"] == "open"


def test_update_404_for_missing(client_with_insert):
    client, _ = client_with_insert
    r = client.patch("/tasks/nonexistent-id", json={"status": "closed"})
    assert r.status_code == 404


def test_update_preserves_created_at(client_with_insert):
    client, insert = client_with_insert
    task_id = insert("Original task")
    original = client.get(f"/tasks/{task_id}").json()
    client.patch(f"/tasks/{task_id}", json={"text": "New text"})
    updated = client.get(f"/tasks/{task_id}").json()
    assert updated["created_at"] == original["created_at"]


def test_update_preserves_source_when_no_src_token(client_with_insert):
    client, insert = client_with_insert
    task_id = insert("Task <rtm.import")
    client.patch(f"/tasks/{task_id}", json={"text": "Updated text no source"})
    updated = client.get(f"/tasks/{task_id}").json()
    assert updated["source_pipeline"] == "rtm"
    assert updated["source_agent"] == "import"


def test_update_text_and_status_combined(client_with_insert):
    client, insert = client_with_insert
    task_id = insert("Original task")
    r = client.patch(f"/tasks/{task_id}", json={"text": "Updated !3", "status": "closed"})
    assert r.status_code == 200
    data = r.json()
    assert data["priority"] == 3
    assert data["status"] == "closed"
    assert data["completed_at"] is not None


# ── DELETE /tasks/{id} ────────────────────────────────────────────────────────

def test_delete_returns_204(client_with_insert):
    client, insert = client_with_insert
    task_id = insert("Task to delete")
    r = client.delete(f"/tasks/{task_id}")
    assert r.status_code == 204


def test_delete_task_gone(client_with_insert):
    client, insert = client_with_insert
    task_id = insert("Task to delete")
    client.delete(f"/tasks/{task_id}")
    r = client.get(f"/tasks/{task_id}")
    assert r.status_code == 404


def test_delete_404_for_missing(client_with_insert):
    client, _ = client_with_insert
    r = client.delete("/tasks/nonexistent-id")
    assert r.status_code == 404
