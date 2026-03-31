"""Database schema migrations using PRAGMA user_version.

Migrations run synchronously at startup before the async DB connection is
initialised. Each migration is a plain sqlite3 operation so it can run
before aiosqlite is involved.

To add a migration: append a (version, description, callable) tuple to
MIGRATIONS. The callable receives a sqlite3.Connection.
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


def _migration_1(con: sqlite3.Connection) -> None:
    """Remove source_pipeline and source_agent columns.

    Provenance is stored exclusively in the task text via the <source:timestamp
    token. The separate columns are redundant.
    Uses table recreation for compatibility with all SQLite versions.
    """
    has_table = con.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='tasks'"
    ).fetchone()[0]
    if not has_table:
        return

    con.executescript("""
        CREATE TABLE tasks_new (
            id              TEXT PRIMARY KEY,
            text            TEXT,
            status          TEXT,
            due             TEXT,
            priority        INTEGER,
            duration        TEXT,
            tags            TEXT,
            location        TEXT,
            assignee_agent  TEXT,
            assignee_human  TEXT,
            created_at      TEXT,
            completed_at    TEXT
        );
        INSERT INTO tasks_new
            SELECT id, text, status, due, priority, duration, tags,
                   location, assignee_agent, assignee_human,
                   created_at, completed_at
            FROM tasks;
        DROP TABLE tasks;
        ALTER TABLE tasks_new RENAME TO tasks;
    """)


MIGRATIONS: list[tuple[int, str, object]] = [
    (1, "Remove source_pipeline and source_agent columns", _migration_1),
]


def run_migrations(db_path: str) -> None:
    """Apply any pending migrations to the database at db_path."""
    con = sqlite3.connect(db_path)
    try:
        current = con.execute("PRAGMA user_version").fetchone()[0]
        pending = [(v, desc, fn) for v, desc, fn in MIGRATIONS if v > current]
        if not pending:
            return
        for version, desc, fn in pending:
            logger.info("Running migration %d: %s", version, desc)
            fn(con)
            con.execute(f"PRAGMA user_version = {version}")
            con.commit()
            logger.info("Migration %d complete", version)
    finally:
        con.close()
