"""Unit tests for parse_text, inject_source_timestamp, and strip_tokens."""
import pytest
from taskapi.parser import inject_source_timestamp, parse_text, strip_tokens


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


# ── inject_source_timestamp ───────────────────────────────────────────────────

def test_inject_stamps_existing_source_token():
    """<source token without timestamp gets stamped."""
    result = inject_source_timestamp("Task <cli.ennui2342", "2026-03-31T10:00:00+00:00")
    assert result == "Task <cli.ennui2342:2026-03-31T10:00:00Z"

def test_inject_leaves_already_stamped_token():
    """<source:timestamp already present — leave as-is."""
    text = "Task <cli.ennui2342:2026-03-31T10:00:00Z"
    assert inject_source_timestamp(text, "2026-04-01T00:00:00+00:00") == text

def test_inject_adds_bare_timestamp_when_no_source():
    """No <source token — inject <:timestamp."""
    result = inject_source_timestamp("Task with no source", "2026-03-31T10:00:00+00:00")
    assert result == "Task with no source <:2026-03-31T10:00:00Z"

def test_inject_handles_multi_layer_source():
    """Three-layer provenance string preserved intact."""
    result = inject_source_timestamp("Task <cli.claude-code.ennui2342", "2026-03-31T10:00:00+00:00")
    assert result == "Task <cli.claude-code.ennui2342:2026-03-31T10:00:00Z"


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
