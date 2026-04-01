# taskmgt

A task management web app built on the [aswarm](https://github.com/ennui2342/aswarm) task store.

## Stack

- **Frontend** — React + Vite + TanStack Query + Tailwind CSS
- **Backend** — FastAPI REST API (`taskapi`) over SQLite via aiosqlite

## Development

```bash
make react-dev   # Vite dev server at http://localhost:5173 (hot reload + API proxy)
make react-up    # Production build served via nginx at http://localhost:3000
make test        # Full BDD + API test suite (Playwright)
make test-api    # API unit tests only
```

Requires `DATABASE_PATH` env var pointing to a `tasks.db` SQLite file.

## Docker

```bash
docker compose up api react-app
```

See `compose.yaml` for full service definitions.

## Filter syntax

Tasks can be filtered using a compact token syntax or a Polish-notation DSL for compound logic (AND/OR/NOT). The `filter` query parameter must be base64-encoded.

```bash
# Legacy: space-separated tokens (implicit AND)
curl "http://localhost:8081/tasks?filter=$(echo -n '#ops !1' | base64)"

# DSL: OR across tags
curl "http://localhost:8081/tasks?filter=$(echo -n '(|(#read)(#write))' | base64)"

# DSL: compound — next AND (read OR write)
curl "http://localhost:8081/tasks?filter=$(echo -n '(&(#next)(|(#read)(#write)))' | base64)"
```

See [`docs/api.md`](docs/api.md#filter-syntax) for the full filter reference.

## Web interface

| URL | Description |
|---|---|
| `/view/all` | All open tasks |
| `/view/inbox` | Tasks with no tags |
| `/view/today` | Tasks due today |
| `/view/overdue` | Overdue tasks |
| `/view/wait` | Waiting tasks |
| `/view/started` | In-progress tasks |
| `/view/closed` | Closed tasks |
| `/view/tag?tag=<name>` | Tasks with a specific tag |
| `/view/location?location=<name>` | Tasks at a specific location |
| `/favourite/<idx>` | Saved filter by index |

Append `?task=<id>` to any view URL to open a specific task directly, e.g. `/view/all?task=42`.

Task notes (lines 2+ of the task text) are rendered as markdown. `[label](url)` links open in a new tab.

## Design philosophy

The backend is a **timestamped text store with a query layer** — analogous to a filesystem. It records when things happened, indexes content for search, but does not prescribe how tasks are managed.

**Text is the source of truth.** Every task is a SmartAdd string. All structured fields (`priority`, `tags`, `due`, `status`, `location`, etc.) are derived by parsing tokens from that string. The text is always a complete, self-contained record of the task's lifecycle.

**The server enforces exactly two things**, both timestamps:
- **Creation** — stamps `<source:timestamp` on `POST /tasks` (client supplies `<source`, server supplies the time)
- **Completion** — stamps `>actor:timestamp` when `§closed` appears in a `PATCH` (client supplies `>actor`, server supplies the time)

Timestamps must be server-authoritative to be trustworthy. Everything else is convention.

**Clients own the lifecycle.** Status transitions, priority changes, tag management — all are expressed by the client sending updated text with the appropriate tokens. The server re-indexes the derived fields but does not validate token semantics or enforce state machine rules. This keeps the backend flexible: new clients can invent new token conventions without any server changes.

**Conventions, not workflow.** What `§wait` means, how `+agent` is used for delegation, whether `#.project` implies a project scope — these are client-level agreements, not server constraints. The API surface is stable; the conventions can evolve.
