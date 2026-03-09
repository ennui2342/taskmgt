import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone

import pytest


_TAG_RE = re.compile(r"(?<![<+])#(\S+)")
_PRIO_RE = re.compile(r"!([123])\b")
_DUE_RE = re.compile(r"\^(\S+)")
_LOC_RE = re.compile(r"@(\S+)")
_AGENT_RE = re.compile(r"(?<!\+)\+(?!\+)(\S+)")
_HUMAN_RE = re.compile(r"\+\+(\S+)")
_DUR_RE = re.compile(r"=(\S+)")
_SRC_RE = re.compile(r"<(\S+)")


def _parse_text(text: str) -> dict:
    first_line = text.split("\n", 1)[0]
    tags = _TAG_RE.findall(first_line)
    prio_m = _PRIO_RE.search(first_line)
    due_m = _DUE_RE.search(first_line)
    loc_m = _LOC_RE.search(first_line)
    human_m = _HUMAN_RE.search(first_line)
    agent_m = _AGENT_RE.search(first_line)
    dur_m = _DUR_RE.search(first_line)
    src_m = _SRC_RE.search(first_line)

    due = None
    if due_m:
        raw = due_m.group(1)
        if "T" in raw or re.match(r"\d{4}-\d{2}-\d{2}$", raw):
            due = raw if "T" in raw else raw + "T00:00:00+00:00"
        else:
            due = raw + "T00:00:00+00:00"

    source_pipeline = None
    source_agent = None
    if src_m:
        parts = src_m.group(1).split(".", 1)
        source_pipeline = parts[0]
        source_agent = parts[1] if len(parts) > 1 else None

    return {
        "tags": json.dumps(tags),
        "priority": int(prio_m.group(1)) if prio_m else None,
        "due": due,
        "location": loc_m.group(1) if loc_m else None,
        "assignee_human": human_m.group(1) if human_m else None,
        "assignee_agent": agent_m.group(1) if agent_m else None,
        "duration": dur_m.group(1) if dur_m else None,
        "source_pipeline": source_pipeline,
        "source_agent": source_agent,
    }


_CREATE_SQL = """
    CREATE TABLE tasks (
        id              TEXT PRIMARY KEY,
        text            TEXT NOT NULL,
        status          TEXT NOT NULL DEFAULT 'open',
        due             TEXT,
        priority        INTEGER,
        duration        TEXT,
        tags            TEXT NOT NULL DEFAULT '[]',
        location        TEXT,
        assignee_agent  TEXT,
        assignee_human  TEXT,
        source_pipeline TEXT,
        source_agent    TEXT,
        created_at      TEXT NOT NULL,
        completed_at    TEXT
    )
"""


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "tasks.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(_CREATE_SQL)
    conn.commit()
    conn.close()

    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    from fastapi.testclient import TestClient
    from taskapi.main import app
    return TestClient(app)


@pytest.fixture
def insert(tmp_path, monkeypatch):
    db_path = tmp_path / "tasks.db"
    # Ensure DB exists (client fixture may not have run first; use same tmp_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(_CREATE_SQL)
        conn.commit()
    except Exception:
        pass  # already created by client fixture sharing same tmp_path

    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    def _insert(text: str, **kwargs):
        parsed = _parse_text(text)
        now = datetime.now(timezone.utc).isoformat()
        row = {
            "id": str(uuid.uuid4()),
            "text": text,
            "status": "open",
            "due": parsed["due"],
            "priority": parsed["priority"],
            "duration": parsed["duration"],
            "tags": parsed["tags"],
            "location": parsed["location"],
            "assignee_agent": parsed["assignee_agent"],
            "assignee_human": parsed["assignee_human"],
            "source_pipeline": parsed["source_pipeline"],
            "source_agent": parsed["source_agent"],
            "created_at": now,
            "completed_at": None,
        }
        row.update(kwargs)
        if isinstance(row.get("tags"), list):
            row["tags"] = json.dumps(row["tags"])
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [row[k] for k in (
                "id", "text", "status", "due", "priority", "duration", "tags",
                "location", "assignee_agent", "assignee_human",
                "source_pipeline", "source_agent", "created_at", "completed_at",
            )],
        )
        conn.commit()
        return row["id"]

    yield _insert
    conn.close()


@pytest.fixture
def client_with_insert(tmp_path, monkeypatch):
    """Combined fixture: returns (client, insert) sharing the same DB."""
    db_path = tmp_path / "tasks.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(_CREATE_SQL)
    conn.commit()

    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    def _insert(text: str, **kwargs):
        parsed = _parse_text(text)
        now = datetime.now(timezone.utc).isoformat()
        row = {
            "id": str(uuid.uuid4()),
            "text": text,
            "status": "open",
            "due": parsed["due"],
            "priority": parsed["priority"],
            "duration": parsed["duration"],
            "tags": parsed["tags"],
            "location": parsed["location"],
            "assignee_agent": parsed["assignee_agent"],
            "assignee_human": parsed["assignee_human"],
            "source_pipeline": parsed["source_pipeline"],
            "source_agent": parsed["source_agent"],
            "created_at": now,
            "completed_at": None,
        }
        row.update(kwargs)
        if isinstance(row.get("tags"), list):
            row["tags"] = json.dumps(row["tags"])
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [row[k] for k in (
                "id", "text", "status", "due", "priority", "duration", "tags",
                "location", "assignee_agent", "assignee_human",
                "source_pipeline", "source_agent", "created_at", "completed_at",
            )],
        )
        conn.commit()
        return row["id"]

    from fastapi.testclient import TestClient
    from taskapi.main import app
    with TestClient(app) as c:
        yield c, _insert
    conn.close()
