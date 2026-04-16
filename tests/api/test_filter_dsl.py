"""Unit tests for DSL (Polish notation) filter parsing.

All tests in Phase 1 are written RED — they call parse_filter() directly
with decoded DSL strings and will fail until the DSL parser is implemented
in Phase 2.
"""
import pytest
from taskapi.filters import parse_filter

TAG_SUBQUERY = "id IN (SELECT t.id FROM tasks t, json_each(t.tags) WHERE json_each.value=?)"


# ── Phase 1 DSL tests (red until Phase 2) ────────────────────────────────────

def test_dsl_single_atom_tag():
    where, params = parse_filter("(#next)")
    assert TAG_SUBQUERY in where
    assert params == ["next"]


def test_dsl_single_atom_priority():
    where, params = parse_filter("(!1)")
    assert "priority=?" in where
    assert params == [1]


def test_dsl_single_atom_location():
    where, params = parse_filter("(@home)")
    assert "location=?" in where
    assert params == ["home"]


def test_dsl_and_two_tags():
    where, params = parse_filter("(&(#next)(#read))")
    assert where.count("json_each.value=?") == 2
    assert set(params) == {"next", "read"}
    assert " AND " in where


def test_dsl_or_two_tags():
    where, params = parse_filter("(|(#next)(#read))")
    assert where.count("json_each.value=?") == 2
    assert set(params) == {"next", "read"}
    assert " OR " in where


def test_dsl_or_wrapped_in_parens():
    """OR block must be parenthesised to avoid polluting the outer AND chain."""
    where, params = parse_filter("(|(#next)(#read))")
    # Strip the always-present status clause to inspect just the DSL part
    dsl_part = where.replace("status!='closed'", "").strip(" AND").strip()
    assert dsl_part.startswith("(") and dsl_part.endswith(")")


def test_dsl_not_tag():
    where, params = parse_filter("(!(#next))")
    assert "NOT" in where.upper()
    assert params == ["next"]


def test_dsl_not_wraps_subquery():
    where, params = parse_filter("(!(#next))")
    assert "NOT (" in where or "NOT(" in where


def test_dsl_variadic_and_three():
    where, params = parse_filter("(&(#a)(#b)(#c))")
    assert where.count("json_each.value=?") == 3
    assert set(params) == {"a", "b", "c"}
    assert " AND " in where


def test_dsl_compound_and_with_nested_or():
    where, params = parse_filter("(&(#next)(|(#read)(#write)))")
    assert "next" in params
    assert "read" in params
    assert "write" in params
    # Top-level join is AND; inner OR is present
    assert " AND " in where
    assert " OR " in where


def test_dsl_mixed_atom_types():
    where, params = parse_filter("(&(#next)(@home)(!1))")
    assert TAG_SUBQUERY in where
    assert "location=?" in where
    assert "priority=?" in where
    assert "next" in params
    assert "home" in params
    assert 1 in params


def test_dsl_special_atom_inbox():
    where, params = parse_filter("(^inbox)")
    assert "tags='[]'" in where


def test_dsl_special_atom_today():
    where, params = parse_filter("(^today)")
    assert "due BETWEEN ? AND ?" in where
    assert len(params) == 2


def test_dsl_special_atom_overdue():
    where, params = parse_filter("(^overdue)")
    assert "due IS NOT NULL AND due < ?" in where
    assert len(params) == 1


def test_dsl_and_with_special_atom():
    where, params = parse_filter("(&(#next)(^today))")
    assert TAG_SUBQUERY in where
    assert "due BETWEEN ? AND ?" in where
    assert "next" in params


# ── Legacy regression guard (must stay green throughout) ─────────────────────

def test_legacy_single_tag():
    where, params = parse_filter("#next")
    assert TAG_SUBQUERY in where
    assert params == ["next"]


def test_legacy_multiple_tokens_and():
    where, params = parse_filter("#next @home")
    assert TAG_SUBQUERY in where
    assert "location=?" in where
    assert "next" in params
    assert "home" in params
    assert " AND " in where


def test_legacy_priority():
    where, params = parse_filter("!1")
    assert "priority=?" in where
    assert params == [1]


def test_legacy_special_inbox():
    where, params = parse_filter("^inbox")
    assert "tags='[]'" in where


def test_legacy_special_today():
    where, params = parse_filter("^today")
    assert "due BETWEEN ? AND ?" in where


def test_status_filter_wait():
    where, params = parse_filter("§wait")
    assert where == "status='wait'"
    assert params == []


def test_status_filter_started():
    where, params = parse_filter("§started")
    assert where == "status='started'"
    assert params == []


def test_status_filter_closed():
    where, params = parse_filter("§closed")
    assert where == "status='closed'"
    assert params == []


def test_status_filter_open():
    where, params = parse_filter("§open")
    assert where == "status='open'"
    assert params == []


def test_status_filter_wait_with_tag():
    where, params = parse_filter("§wait #next")
    assert "status='wait'" in where
    assert TAG_SUBQUERY in where
    assert params == ["next"]


def test_status_filter_in_dsl_prefix():
    """§status before a DSL expression sets the scope."""
    where, params = parse_filter("§wait (&(#next)(@home))")
    assert "status='wait'" in where
    assert TAG_SUBQUERY in where
    assert "location=?" in where


def test_dsl_not_status_atom():
    """§wait used as a DSL atom inside NOT should negate wait status, not set scope."""
    where, params = parse_filter("(&(#-next)(!(§wait)))")
    # Default scope (not overridden — §wait is inside the DSL, not a scope prefix)
    assert "status!='closed'" in where
    # Tag -next must match
    assert TAG_SUBQUERY in where
    assert "-next" in params
    # The NOT(§wait) must exclude wait tasks
    assert "NOT" in where.upper()
    assert "status='wait'" in where
