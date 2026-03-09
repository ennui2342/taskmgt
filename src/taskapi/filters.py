from datetime import datetime, timezone


def parse_filter(s: str) -> tuple[str, list]:
    clauses = ["status='open'"]
    params: list = []

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

    for token in s.split():
        if token.startswith("++"):
            clauses.append("assignee_human=?")
            params.append(token[2:])
        elif token.startswith("+"):
            clauses.append("assignee_agent=?")
            params.append(token[1:])
        elif token.startswith("!") and token[1:].isdigit():
            clauses.append("priority=?")
            params.append(int(token[1:]))
        elif token.startswith("#"):
            clauses.append(
                "id IN (SELECT t.id FROM tasks t, json_each(t.tags) WHERE json_each.value=?)"
            )
            params.append(token[1:])
        elif token.startswith("@"):
            clauses.append("location=?")
            params.append(token[1:])
        elif token == "^inbox":
            clauses.append("tags='[]'")
        elif token == "^today":
            clauses.append("due BETWEEN ? AND ?")
            params.extend([today_start, today_end])
        elif token == "^overdue":
            clauses.append("due IS NOT NULL AND due < ?")
            params.append(today_start)

    return " AND ".join(clauses), params
