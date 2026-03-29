import json
import os
from datetime import datetime, timezone
from typing import Any

import aiosqlite

_conn: aiosqlite.Connection | None = None
_conn_path: str | None = None


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


async def _get_db() -> aiosqlite.Connection:
    """Return the persistent connection, creating it if needed.

    Path-aware: if DATABASE_PATH changes (as it does between test runs)
    the old connection is closed and a fresh one opened.
    """
    global _conn, _conn_path
    current_path = _db_path()
    if _conn is None or _conn_path != current_path:
        if _conn is not None:
            await _conn.close()
        _conn = await aiosqlite.connect(current_path)
        _conn.row_factory = aiosqlite.Row
        _conn_path = current_path
    return _conn


async def init_db() -> None:
    await _get_db()


async def close_db() -> None:
    global _conn, _conn_path
    if _conn is not None:
        await _conn.close()
        _conn = None
        _conn_path = None


_ORDER = "ORDER BY priority IS NULL, priority, created_at"


async def db_list_tasks(status: str, where: str, params: list) -> list[dict]:
    if status == "closed":
        where = where.replace("status='open'", "status='closed'")
    elif status == "all":
        where = where.replace("status='open' AND ", "").replace("status='open'", "1=1")

    db = await _get_db()
    async with db.execute(f"SELECT * FROM tasks WHERE {where} {_ORDER}", params) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


async def db_get_task(task_id: str) -> dict | None:
    db = await _get_db()
    async with db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row) if row else None


async def db_create_task(row: dict) -> dict:
    db = await _get_db()
    await db.execute(
        "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [row[k] for k in (
            "id", "text", "status", "due", "priority", "duration", "tags",
            "location", "assignee_agent", "assignee_human",
            "source_pipeline", "source_agent", "created_at", "completed_at",
        )],
    )
    await db.commit()
    return row


async def db_update_task(task_id: str, fields: dict) -> bool:
    if not fields:
        return True
    db = await _get_db()
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [task_id]
    await db.execute(f"UPDATE tasks SET {sets} WHERE id=?", vals)
    await db.commit()
    return db.total_changes > 0


async def db_delete_task(task_id: str) -> bool:
    db = await _get_db()
    await db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    await db.commit()
    return db.total_changes > 0


async def db_tags() -> list[dict]:
    sql = (
        "SELECT json_each.value AS tag, "
        "SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) AS count "
        "FROM tasks, json_each(tags) "
        "GROUP BY json_each.value ORDER BY json_each.value"
    )
    db = await _get_db()
    async with db.execute(sql) as cur:
        rows = await cur.fetchall()
    return [{"tag": r[0], "count": r[1]} for r in rows]


async def db_locations() -> list[dict]:
    sql = (
        "SELECT location, "
        "SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) AS count "
        "FROM tasks "
        "WHERE location IS NOT NULL "
        "GROUP BY location ORDER BY location"
    )
    db = await _get_db()
    async with db.execute(sql) as cur:
        rows = await cur.fetchall()
    return [{"location": r[0], "count": r[1]} for r in rows]


async def db_pipelines() -> list[dict]:
    sql = (
        "SELECT source_pipeline, COUNT(*) AS count FROM tasks "
        "WHERE status='open' AND source_pipeline IS NOT NULL "
        "GROUP BY source_pipeline ORDER BY source_pipeline"
    )
    db = await _get_db()
    async with db.execute(sql) as cur:
        rows = await cur.fetchall()
    return [{"pipeline": r[0], "count": r[1]} for r in rows]


async def db_counts() -> dict:
    today_start, today_end = _today_bounds()
    db = await _get_db()

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
        "closed": await count("SELECT count(*) FROM tasks WHERE status='closed'"),
    }
