from __future__ import annotations

from pydantic import BaseModel


class TaskCreate(BaseModel):
    text: str


class TaskPatch(BaseModel):
    text: str | None = None
    status: str | None = None


class Task(BaseModel):
    id: str
    text: str
    name: str
    status: str
    due: str | None
    priority: int | None
    duration: str | None
    tags: list[str]
    location: str | None
    assignee_agent: str | None
    assignee_human: str | None
    created_at: str
    completed_at: str | None


class TagCount(BaseModel):
    tag: str
    count: int


class LocationCount(BaseModel):
    location: str
    count: int


class Counts(BaseModel):
    all: int
    inbox: int
    today: int
    overdue: int
    closed: int
    wait: int
    started: int


class FilterItem(BaseModel):
    name: str
    filter: str


class FilterPatch(BaseModel):
    name: str | None = None
    filter: str | None = None
