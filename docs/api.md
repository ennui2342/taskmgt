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
| `status` | string | `"open"` or `"closed"` |
| `due` | string \| null | ISO 8601 datetime (UTC) |
| `priority` | int \| null | `1` = High, `2` = Medium, `3` = Low, `null` = none |
| `duration` | string \| null | Duration string e.g. `"30m"`, `"2h"` |
| `tags` | string[] | List of tag strings (without `#`) |
| `location` | string \| null | Location name (without `@`) |
| `assignee_agent` | string \| null | Agent name (without `+`) |
| `assignee_human` | string \| null | Human assignee (without `++`) |
| `source_pipeline` | string \| null | Pipeline that created this task |
| `source_agent` | string \| null | Agent within pipeline that created this task |
| `created_at` | string | ISO 8601 datetime (UTC) |
| `completed_at` | string \| null | ISO 8601 datetime (UTC), set when closed |

---

## SmartAdd Format

Tasks are created and updated using **SmartAdd text** — a natural-language string with embedded tokens. All tokens apply only to the first line of the text; subsequent lines are annotation lines (see below).

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
| `<pipeline.agent` | source provenance | `Task from CI <ci.builder` |

**Due date** accepts ISO dates (`2026-04-15`), ISO datetimes, or natural language understood by [dateparser](https://dateparser.readthedocs.io/) (`tomorrow`, `next friday`, `in 3 days`).

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
  "text": "Deploy release !1 #ops ^tomorrow",
  "source_pipeline": "ci",
  "source_agent": "builder"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | yes | SmartAdd task text |
| `source_pipeline` | string \| null | no | Override source_pipeline (also parseable from `<pipeline.agent` token in text) |
| `source_agent` | string \| null | no | Override source_agent |

**Response** `201 Created`

```json
{
  "id": "a1b2c3d4-...",
  "text": "Deploy release !1 #ops ^tomorrow",
  "name": "Deploy release",
  "status": "open",
  "due": "2026-03-09T00:00:00+00:00",
  "priority": 1,
  "duration": null,
  "tags": ["ops"],
  "location": null,
  "assignee_agent": null,
  "assignee_human": null,
  "source_pipeline": "ci",
  "source_agent": "builder",
  "created_at": "2026-03-08T14:00:00+00:00",
  "completed_at": null
}
```

---

### GET /tasks

List tasks, with optional filtering.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `status` | string | `"open"` | Filter by status (`"open"` or `"closed"`) |
| `filter` | string | `""` | SmartAdd filter expression (see [Filter Syntax](#filter-syntax)) |

Tasks are returned ordered by: `priority ASC NULLS LAST`, then `created_at ASC`.

**Example**

```
GET /tasks?filter=%23ops+%211
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
| `text` | string \| null | New SmartAdd text. All derived fields (`priority`, `tags`, `due`, etc.) are re-parsed from the new text. If no `<` token is present, `source_pipeline` and `source_agent` are preserved from the existing task. |
| `status` | string \| null | `"open"` or `"closed"`. Setting to `"closed"` sets `completed_at` to now; setting to `"open"` clears it. |

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

List all tags across all tasks, with open-task counts. Tags that only appear on closed tasks are included with a count of `0`.

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

List all locations across all tasks, with open-task counts. Locations that only appear on closed tasks are included with a count of `0`.

**Response** `200 OK`

```json
[
  {"location": "office", "count": 5},
  {"location": "phone", "count": 3}
]
```

Ordered alphabetically by location name.

---

### GET /pipelines

List all source pipelines represented in open tasks, with task counts.

**Response** `200 OK`

```json
[
  {"pipeline": "ci", "count": 42},
  {"pipeline": "rtm", "count": 1020}
]
```

Ordered alphabetically by pipeline name.

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
  "closed": 47
}
```

| Field | Description |
|---|---|
| `all` | All open tasks |
| `inbox` | Open tasks with no tags (`tags = []`) |
| `today` | Open tasks with `due` falling today (UTC) |
| `overdue` | Open tasks with `due` in the past |
| `closed` | All closed tasks |

---

## Filter Syntax

The `filter` query parameter on `GET /tasks` accepts a space-separated list of SmartAdd tokens. All clauses are ANDed. By default only open tasks are returned; combine with `status=closed` to filter closed tasks.

| Token | Matches |
|---|---|
| `#tag` | Tasks with the given tag |
| `@location` | Tasks at the given location |
| `!1` / `!2` / `!3` | Tasks with priority 1, 2, or 3 |
| `+agent` | Tasks assigned to the given agent |
| `++human` | Tasks assigned to the given human |
| `^today` | Tasks due today |
| `^overdue` | Tasks with a past due date |

Unknown tokens are silently ignored.

**Examples**

```
# High-priority ops tasks
GET /tasks?filter=!1 #ops

# Alice's tasks due today
GET /tasks?filter=++alice ^today

# Tasks at the office assigned to the planner agent
GET /tasks?filter=@office +planner
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
