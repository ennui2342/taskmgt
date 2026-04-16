import re
from datetime import datetime, timezone

_STATUS_FILTER_RE = re.compile(r"\s*§(open|wait|started|closed)")


def parse_filter(s: str) -> tuple[str, list]:
    # §status token overrides the default status scope only when it appears
    # *before* any DSL expression — inside a DSL tree it is treated as an atom.
    pre_dsl, _, _ = s.partition("(")
    sm = _STATUS_FILTER_RE.search(pre_dsl)
    if sm:
        status_prefix = f"status='{sm.group(1)}'"
        s = (s[: sm.start()] + s[sm.end() :]).strip()
    else:
        status_prefix = "status!='closed'"

    if not s:
        return status_prefix, []

    if s.startswith("("):
        where, params = _parse_dsl(s)
        return f"{status_prefix} AND ({where})", params
    return _parse_legacy(s, status_prefix)


# ── Legacy (flat AND) parser ──────────────────────────────────────────────────

def _parse_legacy(s: str, status_prefix: str = "status!='closed'") -> tuple[str, list]:
    clauses = [status_prefix]
    params: list = []
    for token in s.split():
        clause, token_params = _compile_atom(token)
        if clause:
            clauses.append(clause)
            params.extend(token_params)
    return " AND ".join(clauses), params


# ── DSL (Polish notation) parser ──────────────────────────────────────────────

def _parse_dsl(s: str) -> tuple[str, list]:
    """Recursively compile a parenthesised DSL expression to (where, params)."""
    # Strip outer parens
    inner = s[1:-1]

    if not inner:
        return "1=1", []

    # Determine operator vs atom
    if inner[0] == "&":
        children = _split_children(inner[1:])
        parts = [_parse_dsl(c) for c in children]
        where = " AND ".join(p[0] for p in parts)
        params = [v for p in parts for v in p[1]]
        return where, params

    if inner[0] == "|":
        children = _split_children(inner[1:])
        parts = [_parse_dsl(c) for c in children]
        where = "(" + " OR ".join(p[0] for p in parts) + ")"
        params = [v for p in parts for v in p[1]]
        return where, params

    # NOT: ! followed by ( means NOT operator; !digit means priority atom
    if inner[0] == "!" and len(inner) > 1 and inner[1] == "(":
        children = _split_children(inner[1:])
        child_where, child_params = _parse_dsl(children[0])
        return f"NOT ({child_where})", child_params

    # Atom: the whole inner string is a single token
    clause, params = _compile_atom(inner)
    return clause or "1=1", params


def _split_children(s: str) -> list[str]:
    """Split a string of adjacent parenthesised expressions into a list."""
    children = []
    depth = 0
    start = 0
    for i, ch in enumerate(s):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                children.append(s[start:i + 1])
    return children


# ── Atom compiler (shared by legacy loop and DSL leaf nodes) ─────────────────

def _compile_atom(token: str) -> tuple[str, list]:
    """Compile a single filter token to (sql_clause, params).
    Returns ("", []) for unrecognised tokens.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

    if token.startswith("++"):
        return "assignee_human=?", [token[2:]]
    if token.startswith("+"):
        return "assignee_agent=?", [token[1:]]
    if token.startswith("!") and token[1:].isdigit():
        return "priority=?", [int(token[1:])]
    if token.startswith("#"):
        return (
            "id IN (SELECT t.id FROM tasks t, json_each(t.tags) WHERE json_each.value=?)",
            [token[1:]],
        )
    if token.startswith("@"):
        return "location=?", [token[1:]]
    if token == "^inbox":
        return "tags='[]'", []
    if token == "^today":
        return "due BETWEEN ? AND ?", [today_start, today_end]
    if token == "^overdue":
        return "due IS NOT NULL AND due < ?", [today_start]
    if token.startswith("§") and token[1:] in ("open", "wait", "started", "closed"):
        return f"status='{token[1:]}'", []
    return "", []
