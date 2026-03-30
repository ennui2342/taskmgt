"""Shared fixtures for BDD tests."""
import importlib
import os
import socket
import sqlite3
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import httpx
import pytest
import uvicorn

REACT_SRC = Path(__file__).parent.parent / "react-src"

_CREATE_SQL = """
    CREATE TABLE tasks (
        id TEXT PRIMARY KEY, text TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open',
        due TEXT, priority INTEGER, duration TEXT, tags TEXT NOT NULL DEFAULT '[]',
        location TEXT, assignee_agent TEXT, assignee_human TEXT,
        source_pipeline TEXT, source_agent TEXT,
        created_at TEXT NOT NULL, completed_at TEXT
    )
"""


# ── Server helpers ────────────────────────────────────────────────────────────

class _ApiServer(threading.Thread):
    def __init__(self, app, port: int):
        super().__init__(daemon=True)
        self._server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
        )

    def run(self):
        self._server.run()

    def stop(self):
        self._server.should_exit = True


class _ViteProcess:
    def __init__(self, port: int, api_url: str):
        self.port = port
        self._api_url = api_url
        self._proc = None

    def start(self):
        env = {**os.environ, "VITE_API_TARGET": self._api_url}
        self._proc = subprocess.Popen(
            ["npm", "run", "dev", "--", "--port", str(self.port), "--strictPort"],
            cwd=str(REACT_SRC),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self):
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for(url: str, timeout: float = 30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url)
            return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"Server at {url} did not start within {timeout}s")


# ── Core fixture ──────────────────────────────────────────────────────────────

@pytest.fixture
def _servers(tmp_path, monkeypatch):
    # Create isolated database
    db_path = tmp_path / "tasks.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(_CREATE_SQL)
    conn.commit()
    conn.close()

    # Start taskapi on a free port
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    filters_src = Path(__file__).parent / "fixtures" / "filters.json"
    filters_copy = tmp_path / "filters.json"
    filters_copy.write_text(filters_src.read_text())
    monkeypatch.setenv("FILTERS_PATH", str(filters_copy))
    import taskapi.main as api_mod
    importlib.reload(api_mod)
    api_port = _free_port()
    api_server = _ApiServer(api_mod.app, api_port)
    api_server.start()
    api_url = f"http://127.0.0.1:{api_port}"
    _wait_for(api_url + "/counts")

    # Start Vite dev server proxying to this taskapi instance
    frontend_port = _free_port()
    vite = _ViteProcess(frontend_port, api_url)
    vite.start()
    frontend_url = f"http://127.0.0.1:{frontend_port}"
    _wait_for(frontend_url + "/", timeout=30.0)

    yield frontend_url, api_url

    vite.stop()
    api_server.stop()


@pytest.fixture
def server_url(_servers):
    frontend_url, _ = _servers
    return frontend_url


@pytest.fixture
def insert_task(_servers):
    _, api_url = _servers

    def _insert(text: str, status: str | None = None):
        if status and status != "open":
            text = f"{text} §{status}"
        with httpx.Client(base_url=api_url) as c:
            resp = c.post("/tasks", json={"text": text})
            resp.raise_for_status()

    return _insert
