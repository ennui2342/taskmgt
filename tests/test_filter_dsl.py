"""Step definitions for filter_dsl.feature.

Phase 4 DSL filter scenarios test end-to-end DSL functionality via the UI.
Phase 5 SmartAdd seed scenario is genuinely red until MainPanel.jsx is fixed.
"""
import httpx
from pytest_bdd import when, scenarios, parsers
from .steps import *  # shared steps

scenarios("features/filter_dsl.feature")


@when(parsers.parse('I visit a favourite filter "{filter_str}"'))
def visit_favourite_filter(page, server_url, _servers, filter_str):
    _, api_url = _servers
    with httpx.Client(base_url=api_url) as c:
        c.post("/filters", json={"name": "test", "filter": filter_str})
    page.goto(f"{server_url}/favourite/0")
    page.wait_for_selector(".task-list")


@when(parsers.parse('I create a task "{name}" via SmartAdd'))
def create_task_via_smartadd(page, name):
    page.locator(".smartadd-input").fill(name)
    page.locator(".smartadd-input").press("Enter")
