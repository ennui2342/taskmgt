---
name: tm
description: >
  Manage tasks in the aswarm taskstore via the `tm` CLI.
  Use when an agent needs to create, list, update, close, or query tasks —
  for productivity workflows (email triage, reminders), project coordination
  (subtask delegation, status tracking), or passing work items between agents.
allowed-tools: Bash(tm:*)
---

# Task Management with `tm`

## Installation

From the taskmgt project root:

```bash
make install-cli
```

Or manually:

```bash
pip install -e ".[cli]"
ln -sf "$(python3 -c 'import sysconfig; print(sysconfig.get_path("scripts"))')/tm" /usr/local/bin/tm
```

## Configuration

```bash
# Explicit API target (preferred in agent invocations)
tm --api http://tasks.k8s.ecafe.org list

# Env var fallback (default: http://localhost:8081)
export TASK_API_URL=http://tasks.k8s.ecafe.org
tm list
```

All commands accept `--api URL` as the first argument.

---

## SmartAdd Token Reference

Tokens are embedded in task text (first line only). Order doesn't matter.

| Token | Example | Meaning |
|-------|---------|---------|
| `!1` `!2` `!3` | `!1` | Priority (1=high, 2=medium, 3=low) |
| `#tag` | `#research` `#.project-x` | Tag (use `#.name` for project tags) |
| `@location` | `@desk` `@office` | Location context |
| `^date` | `^friday` `^2026-04-15` `^tomorrow` | Due date (natural language ok) |
| `=duration` | `=30m` `=2h` | Estimated duration |
| `+agent` | `+analyst.analyse` | Assign to an agent |
| `++human` | `++alice` | Assign to a human |
| `§status` | `§wait` | Status override (open/wait/started/closed) |
| `<source` | `<cli.ennui2342` | Provenance (injected automatically — see below) |

Subsequent lines starting with `* ` are preserved as annotations.

---

## Provenance Convention

Every task records who or what created it via the `<source:timestamp` token embedded in the task text. The API stamps the timestamp; clients embed the `<source` part.

The `tm` CLI injects provenance automatically. Use `--provenance` to override.

| Source | Creation token | Completion token |
|--------|---------------|-----------------|
| Direct CLI use (default) | `<cli.<username>` | `>cli.<username>` |
| Claude Code agent | `<cli.claude-code.<username>` | `>cli.claude-code.<username>` |
| aswarm pipeline | `<aswarm.<pipeline>.<agent>` | `>aswarm.<pipeline>.<agent>` |

**Claude Code agents should always pass `--provenance cli.claude-code.<username>`** so tasks are attributed correctly on both creation and close.

Format: `type.tool.user` — three dot-separated segments. The `--provenance` flag applies to both `tm add` (creation) and `tm update --close` (completion).

The API stamps `:timestamp` onto the provenance token; clients are responsible for embedding the actor part.

---

## Filter DSL

Filters select tasks by token values. The `--filter` flag accepts raw DSL expressions.

### Simple (AND-joined, space-separated)
```
#tag              tasks with tag
@location         tasks at location
!1                priority 1
+agent            assigned to agent
++human           assigned to human
^inbox            no tags (inbox view)
^today            due today
^overdue          past due date
§wait             status=wait (overrides --status)
```

### Boolean DSL (prefix notation)
```
(&(#tag1)(#tag2))         AND: has both tags
(|(#tag1)(#tag2))         OR: has either tag
(!(#tag))                 NOT: doesn't have tag
(&(!1)(|(#read)(#write))) nested: priority 1 AND (read OR write)
```

---

## Commands

### `tm list` — List tasks

```bash
tm list                                    # open tasks (default)
tm list --status all                       # all statuses
tm list --status closed                    # closed tasks
tm list --tag research                     # filter by tag
tm list --location office                  # filter by location
tm list --priority 1                       # high priority only
tm list --inbox                            # untagged tasks
tm list --filter "#research !1"            # DSL filter
tm list --filter "(|(#read)(#write))"      # OR filter
tm list --format table                     # human-readable table
```

Output (JSON, default):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "Read paper !1 #research ^friday <cli.ennui2342:2026-03-31T10:00:00Z",
    "name": "Read paper",
    "status": "open",
    "priority": 1,
    "due": "2026-04-04T00:00:00+00:00",
    "tags": ["research"],
    "location": null,
    "assignee_agent": null,
    "assignee_human": null,
    "created_at": "2026-03-31T10:00:00+00:00",
    "completed_at": null
  }
]
```

### `tm get <id>` — Get a single task

```bash
tm get 550e8400-e29b-41d4-a716-446655440000   # full UUID
tm get 550e8400                                # short prefix (unambiguous)
```

Returns the full task object (same shape as list items).

### `tm add <text>` — Create a task

```bash
tm add "Buy milk #shopping @store !2"
tm add "Analyse dataset +analyst.analyse #.project-x" --provenance aswarm.orchestrator.planner
tm add "Call Alice ^tomorrow =30m ++alice"

# Claude Code agent — always specify provenance
tm add "Review PR #dev !1" --provenance cli.claude-code.ennui2342
```

If no `<source` token is present in the text, `tm` automatically injects `<cli.<USER>` (where `USER` is the current OS user). Use `--provenance` to override this.

Returns the created task object (HTTP 201).

### `tm update <id>` — Update a task

```bash
tm update <id> --close                         # close a task
tm update <id> --status wait                   # set to waiting
tm update <id> --status started                # mark in progress
tm update <id> --text "Revised text !1 #ops"  # rewrite with new SmartAdd text
tm update <id> --text "New name" --close       # text + status together
```

Returns the updated task object.

### `tm delete <id>` — Delete a task

```bash
tm delete <id> --force    # agents MUST use --force (no stdin prompt)
```

Returns `{"deleted": true, "id": "<uuid>"}`.

### `tm counts` — Summary counts

```bash
tm counts                  # table (default)
tm counts --format json    # JSON
```

Output (JSON):
```json
{"all": 42, "inbox": 5, "today": 3, "overdue": 1, "closed": 100, "wait": 7, "started": 2}
```

### `tm tags` / `tm locations` — Taxonomy

```bash
tm tags                    # all tags with counts
tm locations               # all locations with counts
```

Output (JSON):
```json
[{"tag": "research", "count": 12}, {"tag": "shopping", "count": 3}]
```

### `tm filter` — Saved filters

```bash
tm filter list                              # list all saved filters (with index)
tm filter add "high priority" "!1"          # add a filter
tm filter add "project x" "(&(#.project-x)(§open))"
tm filter update 0 --name "urgent"          # rename by index
tm filter update 0 --filter "!1 !2"        # update expression by index
tm filter delete 0 --force                  # delete by index (agents use --force)
```

Filters store raw DSL expressions (not base64). Indices are 0-based from `filter list`.

---

## Common Agent Workflows

### Email triage → tasks

```bash
# Create tasks from emails (Claude Code agent pattern)
tm --api http://tasks.k8s.ecafe.org add "Reply to John re: proposal !2 #email ++john ^friday" \
  --provenance cli.claude-code.ennui2342
tm --api http://tasks.k8s.ecafe.org add "Review invoice from Acme #email #finance !1" \
  --provenance cli.claude-code.ennui2342

# Review email tasks
tm --api http://tasks.k8s.ecafe.org list --tag email

# Close when handled
tm --api http://tasks.k8s.ecafe.org update <id> --close
```

### Project task delegation (agent → agent)

```bash
# Orchestrator creates subtask for analyst agent
tm --api http://tasks.k8s.ecafe.org add "Analyse section 3 of dataset #.project-x +analyst.analyse" \
  --provenance aswarm.orchestrator.planner

# Analyst queries its queue
tm --api http://tasks.k8s.ecafe.org list --filter "+analyst.analyse"

# Analyst marks started, then done
tm --api http://tasks.k8s.ecafe.org update <id> --status started
tm --api http://tasks.k8s.ecafe.org update <id> --close
```

### Triage and prioritise

```bash
# Get counts to understand workload
tm --api http://tasks.k8s.ecafe.org counts --format json

# List overdue items
tm --api http://tasks.k8s.ecafe.org list --filter "^overdue"

# List inbox (untagged — needs filing)
tm --api http://tasks.k8s.ecafe.org list --inbox

# Bump priority on urgent item
tm --api http://tasks.k8s.ecafe.org update <id> --text "$(tm get <id> | jq -r .text) !1"
```

### Working with short IDs

The `tm get` / `update` / `delete` commands accept ID prefixes. Use the first 8
characters from `tm list` output to reference tasks without the full UUID:

```bash
tasks=$(tm --api http://tasks.k8s.ecafe.org list --tag research)
first_id=$(echo "$tasks" | jq -r '.[0].id')
tm --api http://tasks.k8s.ecafe.org update "$first_id" --close
```

---

## Output conventions

- **stdout**: JSON (or rich table with `--format table`)
- **stderr**: error messages only
- **exit 0**: success
- **exit 1**: any error (connection failure, 404, validation error)

Agents should parse stdout as JSON. Stderr is for human-readable diagnostics.
