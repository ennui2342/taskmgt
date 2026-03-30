import json
import re
from datetime import timezone

import dateparser

_TAG_RE = re.compile(r"(?<![<+])#(\S+)")
_PRIO_RE = re.compile(r"!([123])\b")
_DUE_RE = re.compile(r"\^(\S+)")
_LOC_RE = re.compile(r"@(\S+)")
_HUMAN_RE = re.compile(r"\+\+(\S+)")
_AGENT_RE = re.compile(r"(?<!\+)\+(?!\+)(\S+)")
_DUR_RE = re.compile(r"=(\S+)")
_SRC_RE = re.compile(r"<(\S+)")
_STATUS_RE = re.compile(r"§(\S+)")
_COMPLETE_RE = re.compile(r">(\S+)")
_TOKEN_RE = re.compile(r"\s*([!#@^=§>][^\s]+|\+\+?[^\s]+|<[^\s]+)")


_STATUS_SUB_RE = re.compile(r"\s*§\S+")
_COMPLETE_SUB_RE = re.compile(r"\s*>\S+")


def _token_ts(now: str) -> str:
    """Format a timestamp for embedding in a text token (uses Z to avoid + in +00:00)."""
    return now.replace("+00:00", "Z")


def inject_source_timestamp(text: str, now: str) -> str:
    """Ensure the first line has a <actor:timestamp token.

    - If <actor:timestamp already present: leave as-is.
    - If <actor (no timestamp): append :timestamp after actor.
    - If no < token: append <:timestamp.
    """
    ts = _token_ts(now)
    lines = text.split("\n", 1)
    first = lines[0]
    m = _SRC_RE.search(first)
    if m:
        if ":" in m.group(1):
            return text  # already timestamped
        first = first[: m.end()] + ":" + ts + first[m.end() :]
    else:
        first = first + " <:" + ts
    return "\n".join([first] + ([lines[1]] if len(lines) > 1 else []))


def apply_status_to_text(text: str, status: str, now: str) -> str:
    """Rewrite status/completion tokens in the first line to reflect a status change."""
    ts = _token_ts(now)
    lines = text.split("\n", 1)
    first = lines[0]
    tail = ("\n" + lines[1]) if len(lines) > 1 else ""

    if status == "closed":
        if _STATUS_RE.search(first):
            first = _STATUS_RE.sub("§closed", first)
        else:
            first = first + " §closed"
        if _COMPLETE_RE.search(first):
            first = _COMPLETE_RE.sub(f">:{ts}", first)
        else:
            first = first + f" >:{ts}"
    elif status == "open":
        first = _STATUS_SUB_RE.sub("", first).strip()
        first = _COMPLETE_SUB_RE.sub("", first).strip()
    elif status in ("wait", "started"):
        if _STATUS_RE.search(first):
            first = _STATUS_RE.sub(f"§{status}", first)
        else:
            first = first + f" §{status}"
        first = _COMPLETE_SUB_RE.sub("", first).strip()

    return first + tail


def strip_tokens(text: str) -> str:
    first_line = text.split("\n", 1)[0]
    return _TOKEN_RE.sub("", first_line).strip()


def parse_due(raw: str) -> str | None:
    if re.match(r"\d{4}-\d{2}-\d{2}$", raw):
        return raw + "T00:00:00+00:00"
    if "T" in raw and ("+" in raw or "Z" in raw):
        return raw
    parsed = dateparser.parse(raw, settings={"RETURN_AS_TIMEZONE_AWARE": True, "PREFER_DATES_FROM": "future"})
    if parsed:
        return parsed.astimezone(timezone.utc).isoformat()
    return raw + "T00:00:00+00:00"


def parse_text(text: str) -> dict:
    first_line = text.split("\n", 1)[0]
    tags = _TAG_RE.findall(first_line)
    prio_m = _PRIO_RE.search(first_line)
    due_m = _DUE_RE.search(first_line)
    loc_m = _LOC_RE.search(first_line)
    human_m = _HUMAN_RE.search(first_line)
    agent_m = _AGENT_RE.search(first_line)
    dur_m = _DUR_RE.search(first_line)
    src_m = _SRC_RE.search(first_line)
    status_m = _STATUS_RE.search(first_line)
    complete_m = _COMPLETE_RE.search(first_line)

    # Source: <pipeline.agent:timestamp or <pipeline.agent (legacy, no timestamp)
    source_pipeline = None
    source_agent = None
    has_source_token = src_m is not None
    if src_m:
        # Strip optional :timestamp suffix before splitting on .
        actor = src_m.group(1).split(":", 1)[0]
        parts = actor.split(".", 1)
        source_pipeline = parts[0] or None
        source_agent = parts[1] if len(parts) > 1 else None

    # Completion: >actor:timestamp or >:timestamp
    completed_at = None
    if complete_m:
        # Everything after the first : is the timestamp
        raw = complete_m.group(1)
        colon_idx = raw.find(":")
        if colon_idx != -1:
            completed_at = raw[colon_idx + 1:]

    return {
        "tags": json.dumps(tags),
        "priority": int(prio_m.group(1)) if prio_m else None,
        "due": parse_due(due_m.group(1)) if due_m else None,
        "location": loc_m.group(1) if loc_m else None,
        "assignee_human": human_m.group(1) if human_m else None,
        "assignee_agent": agent_m.group(1) if agent_m else None,
        "duration": dur_m.group(1) if dur_m else None,
        "source_pipeline": source_pipeline,
        "source_agent": source_agent,
        "has_source_token": has_source_token,
        "status": status_m.group(1) if status_m else "open",
        "completed_at": completed_at,
    }
