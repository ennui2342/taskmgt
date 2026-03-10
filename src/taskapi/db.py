import json
import os
from datetime import datetime, timezone
from typing import Any

import aiosqlite

_conn: aiosqlite.Connection | None = None


def _db_path() -> str:
    return os.environ["DATABASE_PATH"]


def _row_to_dict(row: aiosqlite.Row) -> dict[str, Any]:
    d = dict(row)
    d["tags"] = json.loads(d.get("tags") or "[]")
    return d


def _today_bounds() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
    return start, end


def _db() -> aiosqlite.Connection:
    assert _conn is not None, "Database not initialised"
    return _conn


async def init_db() -> None:
    global _conn
    _conn = await aiosqlite.connect(_db_path())
    _conn.row_factory = aiosqlite.Row


async def close_db() -> None:
    global _conn
    if _conn:
        await _conn.close()
        _conn = None


_ORDER = "ORDER BY priority IS NULL, priority, created_at"


async def db_list_tasks(status: str, where: str, params: list) -> list[dict]:
    if status == "closed":
        where = where.replace("status='open'", "status='closed'")
    elif status == "all":
        where = where.replace("status='open' AND ", "").replace("status='open'", "1=1")

    async with _db().execute(f"SELECT * FROM tasks WHERE {where} {_ORDER}", params) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


async def db_get_task(task_id: str) -> dict | None:
    async with _db().execute("SELECT * FROM tasks WHERE id=?", (task_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row) if row else None


async def db_create_task(row: dict) -> dict:
    await _db().execute(
        "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [row[k] for k in (
            "id", "text", "status", "due", "priority", "duration", "tags",
            "location", "assignee_agent", "assignee_human",
            "source_pipeline", "source_agent", "created_at", "completed_at",
        )],
    )
    await _db().commit()
    return row


async def db_update_task(task_id: str, fields: dict) -> bool:
    if not fields:
        return True
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [task_id]
    await _db().execute(f"UPDATE tasks SET {sets} WHERE id=?", vals)
    await _db().commit()
    return _db().total_changes > 0


async def db_delete_task(task_id: str) -> bool:
    await _db().execute("DELETE FROM tasks WHERE id=?", (task_id,))
    await _db().commit()
    return _db().total_changes > 0


async def db_tags() -> list[dict]:
    sql = (
        "SELECT json_each.value AS tag, COUNT(*) AS count "
        "FROM tasks, json_each(tags) "
        "WHERE status='open' "
        "GROUP BY json_each.value ORDER BY json_each.value"
    )
    async with _db().execute(sql) as cur:
        rows = await cur.fetchall()
    return [{"tag": r[0], "count": r[1]} for r in rows]


async def db_locations() -> list[dict]:
    sql = (
        "SELECT location, COUNT(*) AS count FROM tasks "
        "WHERE status='open' AND location IS NOT NULL "
        "GROUP BY location ORDER BY location"
    )
    async with _db().execute(sql) as cur:
        rows = await cur.fetchall()
    return [{"location": r[0], "count": r[1]} for r in rows]


async def db_pipelines() -> list[dict]:
    sql = (
        "SELECT source_pipeline, COUNT(*) AS count FROM tasks "
        "WHERE status='open' AND source_pipeline IS NOT NULL "
        "GROUP BY source_pipeline ORDER BY source_pipeline"
    )
    async with _db().execute(sql) as cur:
        rows = await cur.fetchall()
    return [{"pipeline": r[0], "count": r[1]} for r in rows]


async def db_counts() -> dict:
    today_start, today_end = _today_bounds()
    db = _db()

    async def count(sql: str, params: tuple = ()) -> int:
        async with db.execute(sql, params) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

    return {
        "all": await count("SELECT count(*) FROM tasks WHERE status='open'"),
        "inbox": await count("SELECT count(*) FROM tasks WHERE status='open' AND tags='[]'"),
        "today": await count(
            "SELECT count(*) FROM tasks WHERE status='open' AND due BETWEEN ? AND ?",
            (today_start, today_end),
        ),
        "overdue": await count(
            "SELECT count(*) FROM tasks WHERE status='open' AND due IS NOT NULL AND due < ?",
            (today_start,),
        ),
    }
