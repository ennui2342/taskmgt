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
