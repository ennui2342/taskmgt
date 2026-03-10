import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response

from .db import (
    init_db,
    close_db,
    db_counts,
    db_create_task,
    db_delete_task,
    db_get_task,
    db_list_tasks,
    db_locations,
    db_pipelines,
    db_tags,
    db_update_task,
)
from .filters import parse_filter
from .models import (
    Counts,
    FilterItem,
    FilterPatch,
    LocationCount,
    PipelineCount,
    TagCount,
    Task,
    TaskCreate,
    TaskPatch,
)
from .parser import parse_text, strip_tokens

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="aswarm Task API", lifespan=lifespan)


def _row_to_task(row: dict) -> Task:
    return Task(
        id=row["id"],
        text=row["text"],
        name=strip_tokens(row["text"]),
        status=row["status"],
        due=row.get("due"),
        priority=row.get("priority"),
        duration=row.get("duration"),
        tags=row["tags"] if isinstance(row["tags"], list) else json.loads(row["tags"] or "[]"),
        location=row.get("location"),
        assignee_agent=row.get("assignee_agent"),
        assignee_human=row.get("assignee_human"),
        source_pipeline=row.get("source_pipeline"),
        source_agent=row.get("source_agent"),
        created_at=row["created_at"],
        completed_at=row.get("completed_at"),
    )


# ── Tasks ─────────────────────────────────────────────────────────────────────

@app.post("/tasks", response_model=Task, status_code=201)
async def create_task(body: TaskCreate):
    parsed = parse_text(body.text)
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": str(uuid.uuid4()),
        "text": body.text,
        "status": "open",
        "due": parsed["due"],
        "priority": parsed["priority"],
        "duration": parsed["duration"],
        "tags": parsed["tags"],
        "location": parsed["location"],
        "assignee_agent": parsed["assignee_agent"],
        "assignee_human": parsed["assignee_human"],
        "source_pipeline": body.source_pipeline or parsed["source_pipeline"],
        "source_agent": body.source_agent or parsed["source_agent"],
        "created_at": now,
        "completed_at": None,
    }
    await db_create_task(row)
    row["tags"] = json.loads(row["tags"])
    return _row_to_task(row)


@app.get("/tasks", response_model=list[Task])
async def list_tasks(
    status: str = Query(default="open"),
    filter: str = Query(default=""),
):
    where, params = parse_filter(filter) if filter.strip() else ("status='open'", [])
    rows = await db_list_tasks(status, where, params)
    return [_row_to_task(r) for r in rows]


@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    row = await db_get_task(task_id)
    if row is None:
        raise HTTPException(404)
    return _row_to_task(row)


@app.patch("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, body: TaskPatch):
    existing = await db_get_task(task_id)
    if existing is None:
        raise HTTPException(404)

    fields: dict = {}

    if body.text is not None:
        parsed = parse_text(body.text)
        fields["text"] = body.text
        fields["due"] = parsed["due"]
        fields["priority"] = parsed["priority"]
        fields["duration"] = parsed["duration"]
        fields["tags"] = parsed["tags"]
        fields["location"] = parsed["location"]
        fields["assignee_agent"] = parsed["assignee_agent"]
        fields["assignee_human"] = parsed["assignee_human"]
        if parsed["has_source_token"]:
            fields["source_pipeline"] = parsed["source_pipeline"]
            fields["source_agent"] = parsed["source_agent"]

    if body.status == "closed":
        fields["status"] = "closed"
        fields["completed_at"] = datetime.now(timezone.utc).isoformat()
    elif body.status == "open":
        fields["status"] = "open"
        fields["completed_at"] = None

    await db_update_task(task_id, fields)
    row = await db_get_task(task_id)
    return _row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    deleted = await db_delete_task(task_id)
    if not deleted:
        raise HTTPException(404)
    return Response(status_code=204)


# ── Taxonomy ──────────────────────────────────────────────────────────────────

@app.get("/tags", response_model=list[TagCount])
async def tags():
    return await db_tags()


@app.get("/locations", response_model=list[LocationCount])
async def locations():
    return await db_locations()


@app.get("/pipelines", response_model=list[PipelineCount])
async def pipelines():
    return await db_pipelines()


@app.get("/counts", response_model=Counts)
async def counts():
    return await db_counts()


def _filters_path() -> Path:
    return Path(os.environ.get("FILTERS_PATH", "filters.json"))

def _read_filters() -> list:
    p = _filters_path()
    return json.loads(p.read_text()) if p.exists() else []

def _write_filters(filters: list) -> None:
    _filters_path().write_text(json.dumps(filters, indent=2))


@app.get("/filters", response_model=list[FilterItem])
async def list_filters():
    return _read_filters()


@app.post("/filters", response_model=FilterItem, status_code=201)
async def create_filter(body: FilterItem):
    filters = _read_filters()
    filters.append({"name": body.name, "filter": body.filter})
    _write_filters(filters)
    return filters[-1]


@app.patch("/filters/{idx}", response_model=FilterItem)
async def update_filter(idx: int, body: FilterPatch):
    filters = _read_filters()
    if idx < 0 or idx >= len(filters):
        raise HTTPException(404)
    if body.name is not None:
        filters[idx]["name"] = body.name
    if body.filter is not None:
        filters[idx]["filter"] = body.filter
    _write_filters(filters)
    return filters[idx]


@app.delete("/filters/{idx}", status_code=204)
async def delete_filter(idx: int):
    filters = _read_filters()
    if idx < 0 or idx >= len(filters):
        raise HTTPException(404)
    filters.pop(idx)
    _write_filters(filters)
    return Response(status_code=204)
