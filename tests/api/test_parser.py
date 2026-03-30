"""Unit tests for parse_text and strip_tokens — Phase 1 (red until parser.py updated)."""
import pytest
from taskapi.parser import parse_text, strip_tokens


# ── §status token ─────────────────────────────────────────────────────────────

def test_parse_status_open():
    assert parse_text("Task §open")["status"] == "open"

def test_parse_status_wait():
    assert parse_text("Task §wait")["status"] == "wait"

def test_parse_status_started():
    assert parse_text("Task §started")["status"] == "started"

def test_parse_status_closed():
    assert parse_text("Task §closed")["status"] == "closed"

def test_parse_status_default_when_absent():
    assert parse_text("Task no status token")["status"] == "open"

def test_parse_status_only_on_first_line():
    result = parse_text("Task\n* §wait is a note")
    assert result["status"] == "open"


# ── > completion token ────────────────────────────────────────────────────────

def test_parse_completed_at_bare_timestamp():
    r = parse_text("Task >:2026-03-30T14:00:00+00:00")
    assert r["completed_at"] == "2026-03-30T14:00:00+00:00"

def test_parse_completed_at_with_actor():
    r = parse_text("Task >pipeline.agent:2026-03-30T14:00:00+00:00")
    assert r["completed_at"] == "2026-03-30T14:00:00+00:00"

def test_parse_completed_at_absent():
    assert parse_text("Task no completion")["completed_at"] is None

def test_parse_completed_at_only_on_first_line():
    r = parse_text("Task\n* >:2026-03-30T14:00:00+00:00 is a note")
    assert r["completed_at"] is None


# ── < source token with timestamp ─────────────────────────────────────────────

def test_parse_source_with_timestamp():
    r = parse_text("Task <rtm.import:2026-03-30T14:00:00+00:00")
    assert r["source_pipeline"] == "rtm"
    assert r["source_agent"] == "import"

def test_parse_source_without_timestamp_still_works():
    """Backward-compatibility: old format <pipeline.agent (no timestamp)."""
    r = parse_text("Task <rtm.import")
    assert r["source_pipeline"] == "rtm"
    assert r["source_agent"] == "import"

def test_parse_source_pipeline_only_with_timestamp():
    r = parse_text("Task <ci:2026-03-30T14:00:00+00:00")
    assert r["source_pipeline"] == "ci"
    assert r["source_agent"] is None

def test_parse_source_bare_colon_timestamp():
    """<:timestamp — no actor (human create), just timestamp."""
    r = parse_text("Task <:2026-03-30T14:00:00+00:00")
    assert r["source_pipeline"] is None
    assert r["source_agent"] is None


# ── strip_tokens ──────────────────────────────────────────────────────────────

def test_strip_tokens_removes_status_token():
    assert strip_tokens("Task §wait") == "Task"

def test_strip_tokens_removes_completion_token():
    assert strip_tokens("Task >:2026-03-30T14:00:00+00:00") == "Task"

def test_strip_tokens_removes_source_with_timestamp():
    assert strip_tokens("Task <rtm.import:2026-03-30T14:00:00+00:00") == "Task"

def test_strip_tokens_removes_status_alongside_other_tokens():
    assert strip_tokens("Buy milk §wait !1 #chores") == "Buy milk"

def test_strip_tokens_leaves_annotation_lines():
    result = strip_tokens("Task §wait\n* a note")
    assert result == "Task"
