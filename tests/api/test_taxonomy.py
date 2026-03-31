"""Taxonomy endpoint tests."""
import pytest


# ── GET /tags ─────────────────────────────────────────────────────────────────

def test_tags_returns_list_with_count(client_with_insert):
    client, insert = client_with_insert
    insert("Task one #research #work")
    insert("Task two #research")
    r = client.get("/tags")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    research = next((t for t in data if t["tag"] == "research"), None)
    assert research is not None
    assert research["count"] == 2
    work = next((t for t in data if t["tag"] == "work"), None)
    assert work is not None
    assert work["count"] == 1


def test_tags_empty_when_no_tasks(client_with_insert):
    client, _ = client_with_insert
    r = client.get("/tags")
    assert r.json() == []


def test_tags_counts_only_open_tasks(client_with_insert):
    client, insert = client_with_insert
    insert("Open task #research")
    insert("Closed task #research", status="closed", completed_at="2024-01-01T00:00:00+00:00")
    r = client.get("/tags")
    data = r.json()
    research = next((t for t in data if t["tag"] == "research"), None)
    assert research is not None
    assert research["count"] == 1


# ── GET /locations ────────────────────────────────────────────────────────────

def test_locations_returns_list_with_count(client_with_insert):
    client, insert = client_with_insert
    insert("Desk task one @desk")
    insert("Desk task two @desk")
    insert("Home task @home")
    r = client.get("/locations")
    assert r.status_code == 200
    data = r.json()
    desk = next((l for l in data if l["location"] == "desk"), None)
    assert desk is not None
    assert desk["count"] == 2
    home = next((l for l in data if l["location"] == "home"), None)
    assert home is not None
    assert home["count"] == 1


def test_locations_empty_when_no_locations(client_with_insert):
    client, insert = client_with_insert
    insert("No location task")
    r = client.get("/locations")
    assert r.json() == []


def test_locations_counts_only_open(client_with_insert):
    client, insert = client_with_insert
    insert("Open @desk")
    insert("Closed @desk", status="closed", completed_at="2024-01-01T00:00:00+00:00")
    r = client.get("/locations")
    data = r.json()
    desk = next((l for l in data if l["location"] == "desk"), None)
    assert desk["count"] == 1


# ── GET /counts ───────────────────────────────────────────────────────────────

def test_counts_has_all_required_keys(client_with_insert):
    client, _ = client_with_insert
    r = client.get("/counts")
    assert r.status_code == 200
    data = r.json()
    assert "all" in data
    assert "inbox" in data
    assert "today" in data
    assert "overdue" in data
    assert "wait" in data
    assert "started" in data


def test_counts_inbox_equals_open_tasks_with_no_tags(client_with_insert):
    client, insert = client_with_insert
    insert("Inbox task one")
    insert("Inbox task two")
    insert("Tagged task #research")
    r = client.get("/counts")
    data = r.json()
    assert data["inbox"] == 2
    assert data["all"] == 3


def test_counts_all_open_tasks(client_with_insert):
    client, insert = client_with_insert
    insert("Open one")
    insert("Open two")
    insert("Closed", status="closed", completed_at="2024-01-01T00:00:00+00:00")
    r = client.get("/counts")
    assert r.json()["all"] == 2


def test_counts_today(client_with_insert):
    from datetime import datetime, timezone
    client, insert = client_with_insert
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    insert("Today task", due=f"{today}T12:00:00+00:00")
    insert("No due task")
    r = client.get("/counts")
    assert r.json()["today"] == 1


def test_counts_overdue(client_with_insert):
    from datetime import datetime, timezone, timedelta
    client, insert = client_with_insert
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    insert("Overdue task", due=f"{yesterday}T12:00:00+00:00")
    insert("No due task")
    r = client.get("/counts")
    assert r.json()["overdue"] == 1


def test_counts_wait(client_with_insert):
    client, insert = client_with_insert
    insert("Waiting for approval", status="wait")
    insert("Also waiting", status="wait")
    insert("Not waiting #read")
    r = client.get("/counts")
    assert r.json()["wait"] == 2


def test_counts_started(client_with_insert):
    client, insert = client_with_insert
    insert("In progress task", status="started")
    insert("Not started yet")
    r = client.get("/counts")
    assert r.json()["started"] == 1
