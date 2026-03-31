# aswarm Task API

A RESTful HTTP API for managing tasks in the aswarm taskstore. Runs on port **8081** by default.

Base URL: `http://localhost:8081`

Interactive docs (Swagger UI): `http://localhost:8081/docs`

---

## Data Model

### Task

| Field | Type | Description |
|---|---|---|
| `id` | string (UUID) | Unique task identifier |
| `text` | string | Raw task text including SmartAdd tokens and annotation lines |
| `name` | string | Display name — first line of `text` with all tokens stripped |
| `status` | string | `"open"`, `"wait"`, `"started"`, or `"closed"` |
| `due` | string \| null | ISO 8601 datetime (UTC) |
| `priority` | int \| null | `1` = High, `2` = Medium, `3` = Low, `null` = none |
| `duration` | string \| null | Duration string e.g. `"30m"`, `"2h"` |
| `tags` | string[] | List of tag strings (without `#`) |
| `location` | string \| null | Location name (without `@`) |
| `assignee_agent` | string \| null | Agent name (without `+`) |
| `assignee_human` | string \| null | Human assignee (without `++`) |
| `created_at` | string | ISO 8601 datetime (UTC) |
| `completed_at` | string \| null | ISO 8601 datetime (UTC), set when closed |

Provenance (who/what created the task) is stored in the `text` field via the `<source:timestamp` token — see [Provenance Tokens](#provenance-tokens).

---

## SmartAdd Format

Tasks are created and updated using **SmartAdd text** — a natural-language string with embedded tokens. All tokens apply only to the first line of the text; subsequent lines are annotation lines (see below).

The task text is the **source of truth**: all indexed DB fields are derived from tokens in the text. The API also injects provenance tokens into the text automatically (see [Provenance Tokens](#provenance-tokens)).

### Tokens

| Token | Field | Example |
|---|---|---|
| `!1`, `!2`, `!3` | priority (1=High, 2=Med, 3=Low) | `Buy milk !2` |
| `#tag` | adds a tag | `Deploy release #ops #infra` |
| `@location` | location | `Call dentist @phone` |
| `^due` | due date | `File taxes ^2026-04-15` or `^tomorrow` |
| `=duration` | duration | `Write report =2h` |
| `+agent` | assignee_agent | `Review PR +carbon13` |
| `++human` | assignee_human | `Review PR ++alice` |
| `§status` | task status | `Blocked §wait` |
| `<source:timestamp` | creation provenance | `Task <cli.claude-code.ennui2342:2026-03-30T14:00:00Z` |
| `>actor:timestamp` | completion provenance | `Done >cli.ennui2342:2026-03-30T15:00:00Z` |

**Due date** accepts ISO dates (`2026-04-15`), ISO datetimes, or natural language understood by [dateparser](https://dateparser.readthedocs.io/) (`tomorrow`, `next friday`, `in 3 days`).

**Status values**: `open` (default), `wait` (blocked/waiting), `started` (in progress), `closed`.

### Provenance Tokens

Provenance is embedded directly in the task text by the client using the `<source` token. The API stamps the server-side timestamp on creation.

**Convention** — three-layer dot-separated namespace (`type.tool.user`):

| Source | Creation token | Completion token |
|---|---|---|
| CLI (direct human use) | `<cli.ennui2342` | `>cli.ennui2342` |
| CLI (via Claude Code agent) | `<cli.claude-code.ennui2342` | `>cli.claude-code.ennui2342` |
| Web frontend | `<web.taskmgt` | `>web.taskmgt` |
| aswarm pipeline | `<aswarm.researcher.analyse` | `>aswarm.researcher.analyse` |

**Client responsibility**: embed the provenance token in the task text before sending. The API stamps `:timestamp` onto it.

- **On create**: embed `<source` in the text. The API stamps `:timestamp` → `<source:2026-03-30T14:00:00Z`. If absent, injects `<:timestamp`.
- **On close**: embed `>actor` in the text alongside `status: "closed"`. The API stamps `:timestamp` → `>actor:2026-03-30T15:00:00Z`. If absent, injects `>:timestamp` as fallback.

**API behaviour**:
- **On create**: if `<source` is present without timestamp, stamps it. If no `<` token, injects `<:timestamp` (no source attribution).
- **On close** (`PATCH status=closed`): `§closed` replaces any existing `§status` token. If `>actor` is present (no timestamp), stamps it. If `>actor:oldts` exists, preserves actor and updates timestamp. If no `>` token, injects `>:timestamp` as fallback.
- **On status change** (to `open`, `wait`, or `started`): the `§status` token is replaced. The `>` completion token is removed when reopening.

This means the text is always a self-contained record of the task's lifecycle.

### Annotations

Lines after the first line that begin with `* ` are annotation lines — notes attached to the task. Newlines within a note are escaped as `\n`.

```
Buy milk !2 @supermarket
* Check expiry dates
* Get the 2L bottle\nOr 1L if unavailable
```

The `name` field in API responses strips all tokens from the first line only. Annotation lines are preserved in `text` but not reflected in `name`.

---

## Endpoints

### POST /tasks

Create a new task.

**Request body**

```json
{
  "text": "Deploy release !1 #ops ^tomorrow <cli.claude-code.ennui2342"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | yes | SmartAdd task text. Include a `<source` token for provenance attribution. |

The API stamps `:timestamp` onto any `<source` token (or injects `<:timestamp` if none present). The initial status is derived from any `§status` token, defaulting to `"open"`.

**Response** `201 Created`

```json
{
  "id": "a1b2c3d4-...",
  "text": "Deploy release !1 #ops ^tomorrow <cli.claude-code.ennui2342:2026-03-30T14:00:00Z",
  "name": "Deploy release",
  "status": "open",
  "due": "2026-03-09T00:00:00+00:00",
  "priority": 1,
  "duration": null,
  "tags": ["ops"],
  "location": null,
  "assignee_agent": null,
  "assignee_human": null,
  "created_at": "2026-03-30T14:00:00+00:00",
  "completed_at": null
}
```

---

### GET /tasks

List tasks, with optional filtering.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `status` | string | `"open"` | Low-level status scope override: `"open"` (non-closed), `"closed"`, or `"all"`. Prefer `§status` in the filter instead. |
| `filter` | string | `""` | **Base64-encoded** filter expression (see [Filter Syntax](#filter-syntax)) |
| `inbox` | bool | `false` | Direct inbox query — returns non-closed tasks with no tags. Bypasses filter parsing. |

By default (no parameters), returns all tasks where `status != 'closed'` — i.e. `open`, `wait`, and `started` tasks. Use a `§status` filter token to scope by status (e.g. `?filter=<b64('§closed')>` for closed tasks). Use `?inbox=1` for the inbox view.

Tasks are returned ordered by: `priority ASC NULLS LAST`, then `created_at ASC`.

**Example**

```bash
# High-priority ops tasks (base64 of "!1 #ops")
GET /tasks?filter=$(echo -n '!1 #ops' | base64)

# OR filter: read or write tasks (base64 of "(|(#read)(#write))")
GET /tasks?filter=$(echo -n '(|(#read)(#write))' | base64)

# Closed tasks only
GET /tasks?status=closed
```

**Response** `200 OK` — array of [Task](#task) objects.

---

### GET /tasks/{id}

Get a single task by ID.

**Response** `200 OK` — [Task](#task) object.

**Errors**

| Code | Reason |
|---|---|
| `404` | Task not found |

---

### PATCH /tasks/{id}

Update a task. Only provided fields are changed. Omitted fields are left unchanged.

**Request body**

```json
{
  "text": "Deploy release !2 #ops #infra",
  "status": "closed"
}
```

| Field | Type | Description |
|---|---|---|
| `text` | string \| null | New SmartAdd text. All derived fields (`priority`, `tags`, `due`, etc.) are re-parsed from the new text. |
| `status` | string \| null | `"open"`, `"wait"`, `"started"`, or `"closed"`. The API updates `§status` and `>:timestamp` tokens in the stored text accordingly. Setting to `"closed"` sets `completed_at` to now; `"open"` clears it. |

**Response** `200 OK` — updated [Task](#task) object.

**Errors**

| Code | Reason |
|---|---|
| `404` | Task not found |

---

### DELETE /tasks/{id}

Permanently delete a task.

**Response** `204 No Content`

**Errors**

| Code | Reason |
|---|---|
| `404` | Task not found |

---

### GET /tags

List all tags across non-closed tasks, with counts.

**Response** `200 OK`

```json
[
  {"tag": "infra", "count": 14},
  {"tag": "ops", "count": 8}
]
```

Ordered alphabetically by tag name.

---

### GET /locations

List all locations across non-closed tasks, with counts.

**Response** `200 OK`

```json
[
  {"location": "office", "count": 5},
  {"location": "phone", "count": 3}
]
```

Ordered alphabetically by location name.

---

### GET /counts

Summary counts for the standard views.

**Response** `200 OK`

```json
{
  "all": 153,
  "inbox": 12,
  "today": 4,
  "overdue": 2,
  "wait": 7,
  "started": 3,
  "closed": 47
}
```

| Field | Description |
|---|---|
| `all` | All non-closed tasks (`status != 'closed'`) |
| `inbox` | Non-closed tasks with no tags (`tags = []`) |
| `today` | Non-closed tasks with `due` falling today (UTC) |
| `overdue` | Non-closed tasks with `due` in the past |
| `wait` | Tasks with `status = 'wait'` |
| `started` | Tasks with `status = 'started'` |
| `closed` | All closed tasks |

---

## Filter Syntax

The `filter` parameter on `GET /tasks` must be **base64-encoded**. Two filter formats are supported.

### Transport encoding

Always encode the filter string before sending:

```bash
# curl
curl "http://localhost:8081/tasks?filter=$(echo -n '#ops !1' | base64)"

# Python
import base64, httpx
httpx.get("/tasks", params={"filter": base64.b64encode(b"#ops !1").decode()})

# JavaScript (browser / Node)
fetch(`/tasks?filter=${btoa('#ops !1')}`)
```

The server falls back to treating the value as a raw (unencoded) string if base64 decoding fails, which allows direct API exploration in browser devtools.

---

### Legacy format (flat AND)

A space-separated list of tokens, all implicitly ANDed. Returns non-closed tasks by default.

| Token | Matches |
|---|---|
| `#tag` | Tasks with the given tag |
| `@location` | Tasks at the given location |
| `!1` / `!2` / `!3` | Tasks with priority 1, 2, or 3 |
| `+agent` | Tasks assigned to the given agent |
| `++human` | Tasks assigned to the given human |
| `^inbox` | Tasks with no tags |
| `^today` | Tasks due today |
| `^overdue` | Tasks with a past due date |
| `§wait` | Tasks with `status = 'wait'` |
| `§started` | Tasks with `status = 'started'` |
| `§closed` | Tasks with `status = 'closed'` |
| `§open` | Tasks with `status = 'open'` |

Unknown tokens are silently ignored.

**Examples**

```bash
# High-priority ops tasks
curl "http://localhost:8081/tasks?filter=$(echo -n '!1 #ops' | base64)"

# Alice's tasks due today
curl "http://localhost:8081/tasks?filter=$(echo -n '++alice ^today' | base64)"

# Waiting tasks (§ is UTF-8 two-byte sequence 0xC2 0xA7)
curl "http://localhost:8081/tasks?filter=$(printf '§wait' | base64)"

# Inbox (non-closed tasks with no tags — direct query, no filter needed)
curl "http://localhost:8081/tasks?inbox=1"
```

---

### DSL format (Polish notation)

For compound logic, use parenthesised prefix expressions. The filter is detected as DSL when the decoded string starts with `(`.

**Operators**

| Operator | Arity | Description |
|---|---|---|
| `&` | variadic | AND — all children must match |
| `\|` | variadic | OR — at least one child must match |
| `!` followed by `(` | 1 | NOT — child must not match |

**Atoms** inside the DSL use the same token syntax as the legacy format: `(#tag)`, `(@location)`, `(!1)`, `(^today)`, `(^wait)`, `(^started)`, etc. `(!1)` is a priority atom (digit follows `!`), not a NOT operator.

**Examples**

```bash
# Tasks tagged "read" OR "write"
curl "http://localhost:8081/tasks?filter=$(echo -n '(|(#read)(#write))' | base64)"

# Tasks tagged "next" AND at location "home"
curl "http://localhost:8081/tasks?filter=$(echo -n '(&(#next)(@home))' | base64)"

# High-priority tasks tagged "next" AND (read OR write)
curl "http://localhost:8081/tasks?filter=$(echo -n '(&(!1)(#next)(|(#read)(#write)))' | base64)"

# Non-closed tasks NOT tagged "waiting"
curl "http://localhost:8081/tasks?filter=$(echo -n '(!(#waiting))' | base64)"

# Due today OR overdue
curl "http://localhost:8081/tasks?filter=$(echo -n '(|(^today)(^overdue))' | base64)"
```

---

## Error Responses

All errors return JSON with a `detail` field:

```json
{"detail": "Not Found"}
```

| Code | Meaning |
|---|---|
| `404` | Resource not found |
| `422` | Validation error (malformed request body) |

---

## Running the API

**Docker Compose**

```bash
docker compose up api
```

The `api` service mounts the aswarm memory volume (read-write) and exposes port 8081.

**Directly**

```bash
DATABASE_PATH=/path/to/tasks.db python -m taskapi
```

**Development** (with source hot-reload)

```bash
DATABASE_PATH=/path/to/tasks.db uvicorn taskapi.main:app --reload --port 8081
```
