"""Search/filter endpoint tests."""
import pytest
from datetime import datetime, timezone, timedelta


def test_filter_priority_1(client_with_insert):
    client, insert = client_with_insert
    insert("High priority !1")
    insert("Medium priority !2")
    insert("No priority")
    r = client.get("/tasks?filter=!1")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["priority"] == 1


def test_filter_priority_2(client_with_insert):
    client, insert = client_with_insert
    insert("High priority !1")
    insert("Medium priority !2")
    insert("No priority")
    r = client.get("/tasks?filter=!2")
    results = r.json()
    assert len(results) == 1
    assert results[0]["priority"] == 2


def test_filter_priority_3(client_with_insert):
    client, insert = client_with_insert
    insert("High priority !1")
    insert("Low priority !3")
    r = client.get("/tasks?filter=!3")
    results = r.json()
    assert len(results) == 1
    assert results[0]["priority"] == 3


def test_filter_by_tag(client_with_insert):
    client, insert = client_with_insert
    insert("Research task #research")
    insert("Work task #work")
    insert("No tag task")
    r = client.get("/tasks", params={"filter": "#research"})
    results = r.json()
    assert len(results) == 1
    assert "research" in results[0]["tags"]


def test_filter_by_location(client_with_insert):
    client, insert = client_with_insert
    insert("Desk task @desk")
    insert("Home task @home")
    insert("No location task")
    r = client.get("/tasks?filter=@desk")
    results = r.json()
    assert len(results) == 1
    assert results[0]["location"] == "desk"


def test_filter_by_agent(client_with_insert):
    client, insert = client_with_insert
    insert("Agent task +paper.analyser")
    insert("Other task")
    r = client.get("/tasks", params={"filter": "+paper.analyser"})
    results = r.json()
    assert len(results) == 1
    assert results[0]["assignee_agent"] == "paper.analyser"


def test_filter_by_human(client_with_insert):
    client, insert = client_with_insert
    insert("Alice task ++alice")
    insert("Other task")
    r = client.get("/tasks", params={"filter": "++alice"})
    results = r.json()
    assert len(results) == 1
    assert results[0]["assignee_human"] == "alice"


def test_filter_by_due_today(client_with_insert):
    client, insert = client_with_insert
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    insert("Today task", due=f"{today}T12:00:00+00:00")
    insert("Yesterday task", due=f"{yesterday}T12:00:00+00:00")
    insert("No due task")
    r = client.get("/tasks?filter=^today")
    results = r.json()
    assert len(results) == 1
    assert today in results[0]["due"]


def test_filter_by_overdue(client_with_insert):
    client, insert = client_with_insert
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    insert("Overdue task", due=f"{yesterday}T12:00:00+00:00")
    insert("Future task", due=f"{tomorrow}T12:00:00+00:00")
    insert("No due task")
    r = client.get("/tasks?filter=^overdue")
    results = r.json()
    assert len(results) == 1
    assert yesterday in results[0]["due"]


def test_filter_multiple_tokens_anded(client_with_insert):
    client, insert = client_with_insert
    insert("Research high priority !1 #research")
    insert("Research low priority !2 #research")
    insert("High priority no tag !1")
    r = client.get("/tasks", params={"filter": "!1 #research"})
    results = r.json()
    assert len(results) == 1
    assert results[0]["priority"] == 1
    assert "research" in results[0]["tags"]


def test_filter_empty_returns_all_open(client_with_insert):
    client, insert = client_with_insert
    insert("Task one")
    insert("Task two")
    insert("Closed task", status="closed", completed_at="2024-01-01T00:00:00+00:00")
    r = client.get("/tasks?filter=")
    results = r.json()
    assert len(results) == 2
    assert all(t["status"] == "open" for t in results)


def test_filter_no_matches_returns_empty(client_with_insert):
    client, insert = client_with_insert
    insert("No priority task")
    r = client.get("/tasks?filter=!1")
    results = r.json()
    assert results == []
