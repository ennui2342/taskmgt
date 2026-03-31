"""
RTM → aswarm taskstore importer.

Usage:
    python import_rtm.py <export.json> <tasks.db> [--dry-run] [--open-only]
"""
import argparse
import collections
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


# ── helpers ───────────────────────────────────────────────────────────────────

def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def ms_to_date(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def make_uuid(rtm_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "rtm:" + rtm_id))


PRIO_MAP = {"P1": 1, "P2": 2, "P3": 3, "PN": None}
PRIO_TOKEN = {1: "!1", 2: "!2", 3: "!3"}


# ── core conversion ───────────────────────────────────────────────────────────

def convert(task: dict, loc_map: dict, list_map: dict, notes_map: dict) -> dict:
    # status / filtering
    if task.get("date_trashed"):
        return None  # caller skips

    completed_ms = task.get("date_completed")
    status = "closed" if completed_ms else "open"
    completed_at = ms_to_iso(completed_ms) if completed_ms else None

    # priority
    priority = PRIO_MAP.get(task.get("priority", "PN"))

    # due
    due_ms = task.get("date_due")
    if due_ms:
        if task.get("date_due_has_time"):
            due = ms_to_iso(due_ms)
        else:
            due = ms_to_date(due_ms) + "T00:00:00+00:00"
    else:
        due = None

    # location
    loc_id = task.get("location_id")
    location = loc_map[loc_id].lstrip("@") if loc_id and loc_id in loc_map else None

    # list name
    list_name = list_map.get(task.get("list_id", ""), "")

    # tags: project tag from list + task tags
    tags = ([f".{list_name}"] if list_name else []) + list(task.get("tags", []))

    # created_at
    created_ms = task.get("date_created") or task.get("date_added")
    created_at = ms_to_iso(created_ms) if created_ms else ms_to_iso(0)

    # SmartAdd text — tokens on line 1
    parts = [task["name"]]
    if priority:
        parts.append(PRIO_TOKEN[priority])
    if list_name:
        parts.append(f"#.{list_name}")
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")
    if location:
        parts.append(f"@{location}")
    if due:
        parts.append(f"^{due[:10]}")  # date portion only in the token
    parts.append("<rtm.import")
    smartadd_line = " ".join(parts)

    # annotation lines for notes
    annotation_lines = []
    for note in notes_map.get(task.get("series_id", ""), []):
        content = note.get("content", "").replace("\n", "\\n").replace("\r", "")
        title = note.get("title", "").strip()
        body = f"{title}: {content}" if title else content
        if body.strip():
            annotation_lines.append(f"* {body}")

    text = smartadd_line
    if annotation_lines:
        text = smartadd_line + "\n" + "\n".join(annotation_lines)

    return {
        "id": make_uuid(task["id"]),
        "text": text,
        "status": status,
        "due": due,
        "priority": priority,
        "duration": None,
        "tags": json.dumps(tags),
        "location": location,
        "assignee_agent": None,
        "assignee_human": None,
        "created_at": created_at,
        "completed_at": completed_at,
    }


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Import RTM JSON export into aswarm taskstore")
    parser.add_argument("export_json", help="Path to RTM JSON export file")
    parser.add_argument("tasks_db", help="Path to aswarm tasks.db")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be imported without writing")
    parser.add_argument("--open-only", action="store_true", help="Import only open (incomplete) tasks")
    args = parser.parse_args()

    # ── load export ──
    with open(args.export_json) as f:
        data = json.load(f)

    tasks = data["tasks"]
    loc_map = {loc["id"]: loc["name"] for loc in data.get("locations", [])}
    list_map = {lst["id"]: lst["name"] for lst in data.get("lists", [])}

    # notes keyed by series_id, sorted by date_created
    notes_map: dict[str, list] = collections.defaultdict(list)
    for note in data.get("notes", []):
        notes_map[note["series_id"]].append(note)
    for lst in notes_map.values():
        lst.sort(key=lambda n: n.get("date_created", 0))

    # ── convert ──
    total = len(tasks)
    trashed = 0
    completed_count = 0
    open_count = 0
    recurring_count = 0
    annotated_count = 0
    skipped_open_only = 0

    rows: list[dict] = []
    list_tally: collections.Counter = collections.Counter()
    loc_seen: dict[str, str] = {}

    for task in tasks:
        if task.get("date_trashed"):
            trashed += 1
            continue

        row = convert(task, loc_map, list_map, notes_map)

        if row["status"] == "closed":
            completed_count += 1
        else:
            open_count += 1

        if task.get("repeat_every"):
            recurring_count += 1

        series_id = task.get("series_id", "")
        if series_id in notes_map:
            annotated_count += 1

        if args.open_only and row["status"] == "closed":
            skipped_open_only += 1
            continue

        list_name = list_map.get(task.get("list_id", ""), "")
        if list_name:
            list_tally[list_name] += 1

        loc_id = task.get("location_id")
        if loc_id and loc_id in loc_map:
            raw = loc_map[loc_id]
            loc_seen[raw] = raw.lstrip("@")

        rows.append(row)

    # ── report header ──
    print("RTM Import Summary")
    print("==================")
    print(f"Source file : {Path(args.export_json).name}")
    print(f"Target DB   : {args.tasks_db}")
    print()
    print(f"Records in export      : {total:>5}")
    print(f"  Trashed (skipped)    : {trashed:>5}")
    print(f"  Completed            : {completed_count:>5}")
    print(f"  Open                 : {open_count:>5}")
    print()
    print(f"  Recurring tasks      : {recurring_count:>5}  (imported as one-off, no recurrence preserved)")
    print(f"  Tasks with notes     : {annotated_count:>5}  (note text appended as * annotations)")
    if args.open_only:
        print(f"  Skipped (--open-only): {skipped_open_only:>5}")
    print()

    prio_tally = collections.Counter(
        t.get("priority", "PN") for t in tasks if not t.get("date_trashed")
    )
    print(f"Priority breakdown     : " + "  ".join(
        f"{k}={prio_tally[k]}" for k in ("P1", "P2", "P3", "PN")
    ))

    list_parts = "  ".join(f"#.{name}({n})" for name, n in list_tally.most_common())
    print(f"List tags added        : {list_parts}")

    if loc_seen:
        loc_parts = "  ".join(f"@{raw.lstrip('@')}→{clean}" for raw, clean in sorted(loc_seen.items()))
        print(f"Locations mapped       : {loc_parts}")

    print()

    if args.dry_run:
        print(f"DRY RUN — {len(rows)} rows would be imported. No changes made.")
        print()
        print("Sample (first 3 rows):")
        for row in rows[:3]:
            print(f"  [{row['status']:6}] {row['text'][:100]}")
        return

    # ── write ──
    db = sqlite3.connect(args.tasks_db)
    db.execute("PRAGMA journal_mode=WAL")

    with db:
        inserted = 0
        skipped = 0
        for row in rows:
            cur = db.execute(
                """INSERT OR IGNORE INTO tasks
                   (id, text, status, due, priority, duration, tags, location,
                    assignee_agent, assignee_human, created_at, completed_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    row["id"], row["text"], row["status"], row["due"],
                    row["priority"], row["duration"], row["tags"], row["location"],
                    row["assignee_agent"], row["assignee_human"],
                    row["created_at"], row["completed_at"],
                ),
            )
            if cur.rowcount:
                inserted += 1
            else:
                skipped += 1

    db.close()

    print(f"Imported this run      : {inserted:>5}  (new)")
    print(f"Already present        : {skipped:>5}  (skipped — idempotent)")


if __name__ == "__main__":
    main()
