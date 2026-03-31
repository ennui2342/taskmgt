"""tm — CLI for the taskmgt REST API.

Designed for use by AI agents. Defaults to JSON output on stdout.
Errors go to stderr with exit code 1.

Configuration:
  --api URL        API base URL (overrides TASK_API_URL env var)
  TASK_API_URL     API base URL env var (default: http://localhost:8081)

Examples:
  tm add "Buy milk !1 #shopping @store"
  tm list --status open --tag shopping
  tm get abc123
  tm update abc123 --close
  tm delete abc123 --force
  tm filter list
"""

# ── Imports ────────────────────────────────────────────────────────────────────
import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone

import httpx
from rich.console import Console
from rich.table import Table

# ── Config / client ────────────────────────────────────────────────────────────
API_URL_DEFAULT = "http://localhost:8081"
console = Console()
err_console = Console(stderr=True)


def get_api_url(args) -> str:
    return getattr(args, "api", None) or os.environ.get("TASK_API_URL", API_URL_DEFAULT)


def make_client(args) -> httpx.Client:
    return httpx.Client(base_url=get_api_url(args), timeout=10.0)


# ── Output helpers ─────────────────────────────────────────────────────────────
def out_json(data) -> None:
    print(json.dumps(data, indent=2))


def err(msg: str) -> None:
    err_console.print(f"[red]Error:[/red] {msg}")
    sys.exit(1)


def handle_response(r: httpx.Response, expected: int = 200):
    if r.status_code != expected:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        err(f"HTTP {r.status_code}: {detail}")
    if expected == 204:
        return {}
    return r.json()


def api_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except httpx.ConnectError as e:
        err(f"Cannot connect to API: {e}")
    except httpx.TimeoutException:
        err("Request timed out after 10s")


# ── Filter helpers ─────────────────────────────────────────────────────────────
def encode_filter(expr: str) -> str:
    return base64.b64encode(expr.encode()).decode()


def build_filter_expr(filter_expr, tag, location, priority) -> str | None:
    if filter_expr:
        return filter_expr
    tokens = []
    if tag:
        tokens.append(f"#{tag}")
    if location:
        tokens.append(f"@{location}")
    if priority:
        tokens.append(f"!{priority}")
    return " ".join(tokens) if tokens else None


# ── ID resolution ──────────────────────────────────────────────────────────────
def resolve_id(client: httpx.Client, id_or_prefix: str) -> str:
    if len(id_or_prefix) == 36 and id_or_prefix.count("-") == 4:
        return id_or_prefix
    r = api_call(client.get, "/tasks", params={"status": "all"})
    tasks = handle_response(r)
    matches = [t for t in tasks if t["id"].startswith(id_or_prefix)]
    if len(matches) == 0:
        err(f"No task found with ID prefix: {id_or_prefix!r}")
    if len(matches) > 1:
        ids = ", ".join(t["id"][:12] for t in matches)
        err(f"Ambiguous prefix {id_or_prefix!r} matches: {ids}")
    return matches[0]["id"]


# ── Table renderers ────────────────────────────────────────────────────────────
def _priority_str(p) -> str:
    if p == 1:
        return "[red]1[/red]"
    if p == 2:
        return "[yellow]2[/yellow]"
    if p == 3:
        return "[blue]3[/blue]"
    return ""


def _status_initial(s: str) -> str:
    return {"open": "O", "wait": "W", "started": "S", "closed": "C"}.get(s, s[0].upper())


def _due_str(due: str | None) -> str:
    if not due:
        return ""
    try:
        dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")
        if dt < now:
            return f"[red]{date_str}[/red]"
        return date_str
    except Exception:
        return due


def render_tasks_table(tasks: list) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("P", width=1)
    table.add_column("S", width=1)
    table.add_column("Name")
    table.add_column("Tags")
    table.add_column("Due")

    for t in tasks:
        name = t.get("name") or t.get("text", "")
        if len(name) > 60:
            name = name[:57] + "..."
        tags = ", ".join(f"#{tag}" for tag in (t.get("tags") or []))
        table.add_row(
            t["id"][:8],
            _priority_str(t.get("priority")),
            _status_initial(t.get("status", "open")),
            name,
            tags,
            _due_str(t.get("due")),
        )
    console.print(table)


def render_counts_table(counts: dict) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("View")
    table.add_column("Count", justify="right")
    for key, val in counts.items():
        table.add_row(key, str(val))
    console.print(table)


def render_taxonomy_table(items: list, key: str) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column(key.capitalize())
    table.add_column("Count", justify="right")
    for item in items:
        table.add_row(item[key], str(item["count"]))
    console.print(table)


def render_filters_table(filters: list) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Idx", justify="right", style="dim")
    table.add_column("Name")
    table.add_column("Filter")
    for i, f in enumerate(filters):
        table.add_row(str(i), f["name"], f["filter"])
    console.print(table)


# ── Command: list ──────────────────────────────────────────────────────────────
def cmd_list(args) -> None:
    params = {"status": args.status}
    expr = build_filter_expr(args.filter, args.tag, args.location, args.priority)
    if expr:
        params["filter"] = encode_filter(expr)
    if args.inbox:
        params["inbox"] = "true"

    with make_client(args) as client:
        r = api_call(client.get, "/tasks", params=params)
    tasks = handle_response(r)

    if args.format == "table":
        render_tasks_table(tasks)
    else:
        out_json(tasks)


# ── Command: get ───────────────────────────────────────────────────────────────
def cmd_get(args) -> None:
    with make_client(args) as client:
        task_id = resolve_id(client, args.id)
        r = api_call(client.get, f"/tasks/{task_id}")
    task = handle_response(r)

    if args.format == "table":
        render_tasks_table([task])
    else:
        out_json(task)


# ── Command: add ───────────────────────────────────────────────────────────────
def cmd_add(args) -> None:
    text = args.text
    # Inject provenance token if not already in text
    if "<" not in text.split("\n")[0]:
        provenance = args.provenance or f"cli.{os.environ.get('USER', 'unknown')}"
        text = f"{text} <{provenance}"

    with make_client(args) as client:
        r = api_call(client.post, "/tasks", json={"text": text})
    task = handle_response(r, expected=201)

    if args.format == "table":
        render_tasks_table([task])
    else:
        out_json(task)


# ── Command: update ────────────────────────────────────────────────────────────
def cmd_update(args) -> None:
    if not args.text and not args.status and not args.close:
        err("Provide at least one of --text, --status, or --close")

    body = {}
    if args.text:
        body["text"] = args.text
    if args.close:
        body["status"] = "closed"
    elif args.status:
        body["status"] = args.status

    with make_client(args) as client:
        task_id = resolve_id(client, args.id)
        # Inject completion provenance when closing
        if body.get("status") == "closed":
            r_get = api_call(client.get, f"/tasks/{task_id}")
            existing = handle_response(r_get)
            text = body.get("text") or existing["text"]
            first_line = text.split("\n")[0]
            if ">" not in first_line:
                provenance = args.provenance or f"cli.{os.environ.get('USER', 'unknown')}"
                rest = text[len(first_line):]
                text = first_line + f" >{provenance}" + rest
            body["text"] = text
        r = api_call(client.patch, f"/tasks/{task_id}", json=body)
    task = handle_response(r)

    if args.format == "table":
        render_tasks_table([task])
    else:
        out_json(task)


# ── Command: delete ────────────────────────────────────────────────────────────
def cmd_delete(args) -> None:
    with make_client(args) as client:
        task_id = resolve_id(client, args.id)

        if not args.force:
            r = api_call(client.get, f"/tasks/{task_id}")
            task = handle_response(r)
            name = task.get("name") or task.get("text", task_id)
            try:
                answer = input(f"Delete task '{name}'? [y/N] ")
            except EOFError:
                err("Non-interactive mode requires --force")
            if answer.lower() not in ("y", "yes"):
                print("Aborted.")
                sys.exit(0)

        r = api_call(client.delete, f"/tasks/{task_id}")
    handle_response(r, expected=204)
    out_json({"deleted": True, "id": task_id})


# ── Command: counts ────────────────────────────────────────────────────────────
def cmd_counts(args) -> None:
    with make_client(args) as client:
        r = api_call(client.get, "/counts")
    counts = handle_response(r)

    if args.format == "json":
        out_json(counts)
    else:
        render_counts_table(counts)


# ── Command: tags / locations ──────────────────────────────────────────────────
def cmd_tags(args) -> None:
    with make_client(args) as client:
        r = api_call(client.get, "/tags")
    items = handle_response(r)
    if args.format == "table":
        render_taxonomy_table(items, "tag")
    else:
        out_json(items)


def cmd_locations(args) -> None:
    with make_client(args) as client:
        r = api_call(client.get, "/locations")
    items = handle_response(r)
    if args.format == "table":
        render_taxonomy_table(items, "location")
    else:
        out_json(items)


# ── Command: filter ────────────────────────────────────────────────────────────
def cmd_filter_list(args) -> None:
    with make_client(args) as client:
        r = api_call(client.get, "/filters")
    filters = handle_response(r)
    if args.format == "table":
        render_filters_table(filters)
    else:
        out_json(filters)


def cmd_filter_add(args) -> None:
    body = {"name": args.name, "filter": args.expr}
    with make_client(args) as client:
        r = api_call(client.post, "/filters", json=body)
    item = handle_response(r, expected=201)
    out_json(item)


def cmd_filter_update(args) -> None:
    if not args.name and not args.filter:
        err("Provide at least one of --name or --filter")
    body = {}
    if args.name:
        body["name"] = args.name
    if args.filter:
        body["filter"] = args.filter
    with make_client(args) as client:
        r = api_call(client.patch, f"/filters/{args.idx}", json=body)
    item = handle_response(r)
    out_json(item)


def cmd_filter_delete(args) -> None:
    if not args.force:
        try:
            answer = input(f"Delete filter at index {args.idx}? [y/N] ")
        except EOFError:
            err("Non-interactive mode requires --force")
        if answer.lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)
    with make_client(args) as client:
        r = api_call(client.delete, f"/filters/{args.idx}")
    handle_response(r, expected=204)
    out_json({"deleted": True, "idx": args.idx})


# ── main() + argparse setup ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="tm",
        description="Task management CLI for the taskmgt API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Configuration:\n"
            "  --api URL      API base URL (overrides TASK_API_URL env var)\n"
            "  TASK_API_URL   Env var fallback (default: http://localhost:8081)\n"
        ),
    )
    parser.add_argument(
        "--api",
        metavar="URL",
        help="API base URL (overrides TASK_API_URL env var)",
    )

    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    # ── list ──
    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument(
        "--status", "-s",
        default="open",
        choices=["open", "wait", "started", "closed", "all"],
        help="Task status filter (default: open)",
    )
    p_list.add_argument("--filter", "-F", metavar="EXPR", help="Filter expression (raw DSL)")
    p_list.add_argument("--tag", "-t", metavar="TAG", help="Filter by tag (without #)")
    p_list.add_argument("--location", "-l", metavar="LOC", help="Filter by location (without @)")
    p_list.add_argument("--priority", "-p", type=int, choices=[1, 2, 3], help="Filter by priority")
    p_list.add_argument("--inbox", "-i", action="store_true", help="Show inbox (untagged tasks)")
    p_list.add_argument("--format", "-f", default="json", choices=["json", "table"])
    p_list.set_defaults(func=cmd_list)

    # ── get ──
    p_get = sub.add_parser("get", help="Get a single task")
    p_get.add_argument("id", help="Task ID or unique prefix")
    p_get.add_argument("--format", "-f", default="json", choices=["json", "table"])
    p_get.set_defaults(func=cmd_get)

    # ── add ──
    p_add = sub.add_parser("add", help="Create a task (SmartAdd syntax)")
    p_add.add_argument("text", help="Task text with optional SmartAdd tokens")
    p_add.add_argument(
        "--provenance", metavar="SOURCE",
        help="Provenance string embedded as <source token (default: cli.<USER>). "
             "Use e.g. 'cli.claude-code.<username>' when invoking as an agent.",
    )
    p_add.add_argument("--format", "-f", default="json", choices=["json", "table"])
    p_add.set_defaults(func=cmd_add)

    # ── update ──
    p_update = sub.add_parser("update", help="Update a task")
    p_update.add_argument("id", help="Task ID or unique prefix")
    p_update.add_argument("--text", "-t", metavar="TEXT", help="New task text (SmartAdd)")
    p_update.add_argument(
        "--status", "-s",
        choices=["open", "wait", "started", "closed"],
        help="New status",
    )
    p_update.add_argument("--close", "-c", action="store_true", help="Shorthand for --status closed")
    p_update.add_argument("--format", "-f", default="json", choices=["json", "table"])
    p_update.set_defaults(func=cmd_update)

    # ── delete ──
    p_delete = sub.add_parser("delete", help="Delete a task")
    p_delete.add_argument("id", help="Task ID or unique prefix")
    p_delete.add_argument("--force", action="store_true", help="Skip confirmation (required for agents)")
    p_delete.set_defaults(func=cmd_delete)

    # ── counts ──
    p_counts = sub.add_parser("counts", help="Show task count summary")
    p_counts.add_argument("--format", "-f", default="table", choices=["json", "table"])
    p_counts.set_defaults(func=cmd_counts)

    # ── tags / locations / pipelines ──
    p_tags = sub.add_parser("tags", help="List tags with counts")
    p_tags.add_argument("--format", "-f", default="json", choices=["json", "table"])
    p_tags.set_defaults(func=cmd_tags)

    p_locations = sub.add_parser("locations", help="List locations with counts")
    p_locations.add_argument("--format", "-f", default="json", choices=["json", "table"])
    p_locations.set_defaults(func=cmd_locations)

    # ── filter ──
    p_filter = sub.add_parser("filter", help="Manage saved filters")
    filter_sub = p_filter.add_subparsers(dest="filter_command", required=True, metavar="<subcommand>")

    pf_list = filter_sub.add_parser("list", help="List saved filters")
    pf_list.add_argument("--format", "-f", default="json", choices=["json", "table"])
    pf_list.set_defaults(func=cmd_filter_list)

    pf_add = filter_sub.add_parser("add", help="Add a saved filter")
    pf_add.add_argument("name", help="Filter name")
    pf_add.add_argument("expr", help="Filter expression (raw DSL, e.g. '#tag @loc !1')")
    pf_add.set_defaults(func=cmd_filter_add)

    pf_update = filter_sub.add_parser("update", help="Update a saved filter")
    pf_update.add_argument("idx", type=int, help="Filter index (0-based, from 'filter list')")
    pf_update.add_argument("--name", metavar="NAME", help="New name")
    pf_update.add_argument("--filter", "-F", metavar="EXPR", help="New filter expression")
    pf_update.set_defaults(func=cmd_filter_update)

    pf_delete = filter_sub.add_parser("delete", help="Delete a saved filter")
    pf_delete.add_argument("idx", type=int, help="Filter index (0-based)")
    pf_delete.add_argument("--force", action="store_true", help="Skip confirmation")
    pf_delete.set_defaults(func=cmd_filter_delete)

    args = parser.parse_args()

    # Dispatch filter subcommands
    if args.command == "filter":
        if not hasattr(args, "func"):
            p_filter.print_help()
            sys.exit(1)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
