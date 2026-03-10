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
_TOKEN_RE = re.compile(r"\s*([!#@^=][^\s]+|\+\+?[^\s]+|<[^\s]+)")


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

    source_pipeline = None
    source_agent = None
    if src_m:
        parts = src_m.group(1).split(".", 1)
        source_pipeline = parts[0]
        source_agent = parts[1] if len(parts) > 1 else None

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
        "has_source_token": src_m is not None,
    }
