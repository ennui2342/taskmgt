# Prompt: Remember The Milk → aswarm taskstore import script

## Task

Write a Python script `import_rtm.py` that reads a Remember The Milk JSON export
file and imports tasks into the aswarm SQLite taskstore. The script should be
idempotent (safe to run multiple times), print a clear summary of what it did,
and explain any decisions or skipped records.

---

## Source format — RTM JSON export

Top-level structure:
```json
{
  "tasks":     [...],   // 1029 records in the sample
  "lists":     [...],   // named lists (e.g. "personal", "Inbox", "career")
  "locations": [...],   // named locations with id
  "notes":     [...],   // free-text notes linked to tasks via series_id
  ...
}
```

### Task record fields

| Field               | Type            | Notes |
|---------------------|-----------------|-------|
| `id`                | string          | RTM numeric ID as string, e.g. `"912161786"` |
| `series_id`         | string          | Groups repeat instances; notes link via this field |
| `list_id`           | string          | Foreign key into `lists[].id` |
| `location_id`       | string or null  | Foreign key into `locations[].id`; absent on some records |
| `name`              | string          | Plain task title, no tokens |
| `priority`          | string          | `"P1"`, `"P2"`, `"P3"`, or `"PN"` (none) |
| `date_created`      | integer or null | Unix milliseconds |
| `date_added`        | integer or null | Unix milliseconds (use as fallback for created_at) |
| `date_completed`    | integer or null | Unix milliseconds; non-null means completed |
| `date_trashed`      | integer or null | Unix milliseconds; non-null means deleted — **skip these** |
| `date_due`          | integer or null | Unix milliseconds; null means no due date |
| `date_due_has_time` | boolean         | If false, due is date-only (no time component in RTM) |
| `repeat_every`      | boolean         | True if task is from a recurring series |
| `tags`              | list of strings | Tag names; used verbatim as IDs in RTM |
| `source`            | string          | e.g. `"js"` — internal RTM provenance, not useful |

### Location record
```json
{
  "id": "814623",
  "name": "@desk",        // always prefixed with @
  "address": "...",
  "latitude": 52.21,
  "longitude": 0.13
}
```

### List record
```json
{
  "id": "18663695",
  "name": "career"
}
```

### Note record
```json
{
  "id":          "102698199",
  "series_id":   "526817219",   // matches task.series_id (NOT task.id)
  "title":       "",
  "content":     "Some free text...",
  "date_created": 1704213883585
}
```

---

## Target schema — aswarm taskstore SQLite

```sql
CREATE TABLE tasks (
    id              TEXT PRIMARY KEY,       -- UUID
    text            TEXT NOT NULL,          -- full SmartAdd string (tokens included)
    status          TEXT NOT NULL DEFAULT 'open',  -- 'open' | 'closed'
    due             TEXT,                   -- ISO 8601 datetime string or NULL
    priority        INTEGER,               -- 1/2/3 (1=highest) or NULL
    duration        TEXT,                  -- e.g. "30m" — NULL for all RTM tasks
    tags            TEXT NOT NULL DEFAULT '[]',  -- JSON array of strings
    location        TEXT,                  -- plain name without @ prefix, or NULL
    assignee_agent  TEXT,                  -- NULL for all RTM tasks
    assignee_human  TEXT,                  -- NULL for all RTM tasks
    source_pipeline TEXT,                  -- "rtm" for all imported tasks
    source_agent    TEXT,                  -- "import" for all imported tasks
    created_at      TEXT NOT NULL,         -- ISO 8601
    completed_at    TEXT                   -- ISO 8601 or NULL
);
```

---

## Field mapping — detailed

### `id`
Generate a new UUID v5 from the namespace `uuid.NAMESPACE_URL` and the RTM task
`id` string. This gives a stable, reproducible UUID that won't clash with native
aswarm UUIDs and allows the script to be re-run idempotently.

### `text` (SmartAdd format)
The design doc is explicit: *"The `text` column is the source of truth. All other
columns are parsed from it at write time."* and *"The `<pipeline.agent` source token
is appended to the task text on ingestion."* The full reconstructed text must
therefore contain all metadata tokens including the source provenance token.

Reconstruct from parsed fields in this order:
```
{name} [!{priority}] [#.{list_name}] [#{tag} ...] [@{location}] [^{due_date}] <rtm.import
```
- Start with the plain `name`
- Append `!1`, `!2`, or `!3` if priority is P1/P2/P3 (omit for PN)
- Append `#.{list_name}` for the RTM list (e.g. `#.personal`, `#.career`) —
  using the `#.` project tag convention from the design doc
- Append `#tag` for each task tag (space-separated)
- Append `@{location}` (without the `@` prefix from RTM, add it back)
- Append `^{YYYY-MM-DD}` if due date present (date only — `date_due_has_time`
  is always false in this export; if it were true, use full ISO datetime)
- Always append `<rtm.import` — the source provenance token required by the design

Example: `"Research prep for meeting !1 #.career #research #-next @desk ^2022-11-04 <rtm.import"`

### `status`
- `date_trashed` is non-null → **skip this record entirely**
- `date_completed` is non-null → `'closed'`
- Otherwise → `'open'`

### `due`
- `date_due` is null → `NULL`
- `date_due_has_time` is false → convert ms to `YYYY-MM-DDT00:00:00+00:00`
- `date_due_has_time` is true → convert ms to full ISO 8601 with UTC offset

### `priority`
| RTM | aswarm |
|-----|--------|
| `P1` | `1` |
| `P2` | `2` |
| `P3` | `3` |
| `PN` | `NULL` |

### `tags`
Combine the RTM task tags with the list name as a project tag:
```python
tags = [f".{list_name}"] + task["tags"]   # e.g. [".career", "research", "-next"]
json.dumps(tags)
```
The `#.` project convention is stored in the tags array without the `#` (just `.career`),
consistent with how the design doc describes all tag conventions: *"Project (`#.`),
customer (`#..`), and action (`#-`) are not stored in separate columns — they are
tag conventions and live entirely in the `tags` JSON array."*

RTM tag names already use the same prefix conventions (`.project` → matches `#.`,
`-next` → matches `#-`), so they map cleanly with no transformation.

### `location`
- `location_id` absent or null → `NULL`
- Otherwise look up `locations` by id, take `name`, **strip the leading `@`**
  (RTM stores `"@desk"`, aswarm stores `"desk"`)

### `source_pipeline` and `source_agent`
These columns record the aswarm agent that wrote the task — not an RTM concept.
Set both to identify the import provenance:
- `source_pipeline = "rtm"`
- `source_agent = "import"`

The RTM list (provenance within RTM) is captured via the `#.{list_name}` project
tag in `text` and `tags`, not via `source_pipeline`.

### `created_at`
Use `date_created` if non-null, else `date_added`. Convert ms to ISO 8601.

### `completed_at`
`date_completed` converted to ISO 8601, or `NULL`.

### `duration`, `assignee_agent`, `assignee_human`
All `NULL` — RTM has no equivalent.

---

## Notes handling

41 notes exist, each linked to a task via `series_id`. The aswarm schema has no
notes column; notes are stored as annotation lines in the `text` field using the
Taskwarrior-style `* ` prefix convention documented in `taskstore-design.md`.

Rules:
- Each annotation is a single line starting with `* `
- Literal newlines within a note's `content` are escaped as the two-character
  sequence `\n` (backslash + n)
- If a note has a non-empty `title`, prefix the content with `{title}: `
- Multiple notes produce multiple `* ` lines, one per note, ordered by `date_created`
- Annotation lines follow immediately after the SmartAdd line — no blank line separator
- The SmartAdd parser only processes line 1, so annotation content is never
  misread as tokens

Example (single note, no title):
```
Apply for carbon13 !1 #.career #-next #-write @peripatetic ^2023-01-02 <rtm.import
* https://carbonthirteen.com/carbon13-venture-builder-application-form/
```

Example (note with title and internal newlines):
```
Fix fence !2 #.personal @home <rtm.import
* Surveyor notes: Check the east boundary first\nMay need planning permission for height > 2m
```

---

## Repeat tasks

`repeat_every: true` appears on 693 tasks. The aswarm schema has no recurrence
field. Import these tasks as normal one-off tasks (the recurrence spec is not
preserved in this export format anyway — the field is only a boolean flag).
Log a count of how many recurring tasks were imported so the user is aware.

---

## Idempotency

Use `INSERT OR IGNORE` (SQLite) keyed on the stable UUID v5 `id`. Running the
script twice will not create duplicates.

---

## CLI interface

```
python import_rtm.py <export.json> <tasks.db> [--dry-run] [--open-only]
```

| Flag | Behaviour |
|------|-----------|
| `--dry-run` | Print what would be imported without writing to the DB |
| `--open-only` | Import only open tasks (skip completed ones) |

---

## Output / summary

Print a clear import report:

```
RTM Import Summary
==================
Source file : rememberthemilk_export_2026-03-08T12_58_34.788Z.json
Target DB   : /path/to/tasks.db

Records in export      : 1029
  Trashed (skipped)    :    9
  Completed            :  904
  Open                 :  116

  Recurring tasks      :  693  (imported as one-off, no recurrence preserved)
  Tasks with notes     :   41  (note text appended to task text field)

Imported this run      :  XXX  (new)
Already present        :  XXX  (skipped — idempotent)

Priority breakdown     : P1=123  P2=57  P3=50  none=799
List tags added        : #.personal(343) #.moratgames(380) #.Inbox(93) #.career(46) ...
Locations mapped       : @desk→desk  @home→home  @peripatetic→peripatetic ...
```

---

## Implementation notes

- The design doc (`taskstore-design.md`) specifies `status` values `'open' | 'done'`
  but the live schema and taskboard code use `'open' | 'closed'`. Use **`'closed'`**
  to match the running implementation.
- Use only stdlib: `json`, `sqlite3`, `uuid`, `datetime`, `argparse`
- Open the database in WAL mode (`PRAGMA journal_mode=WAL`) before writing
- All timestamps in the export are Unix **milliseconds** — divide by 1000 before
  passing to `datetime.fromtimestamp(..., tz=timezone.utc)`
- UUID v5 namespace: `uuid.NAMESPACE_URL`, name: `"rtm:" + task["id"]`
- Wrap all inserts in a single transaction for performance
