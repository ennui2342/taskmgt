"""Shared step definitions — imported by all test modules.

Fixtures used: `insert_task`, `server_url`, `page` (from pytest-playwright).
"""
import re as _re
import pytest
from pytest_bdd import given, then, when, parsers


# ── Given steps ──────────────────────────────────────────────────────────────

@given(parsers.parse('the task store has an open task "{text}"'))
def add_task(insert_task, text):
    insert_task(text)


@given('the task store is empty')
def empty_store():
    pass  # task_db fixture always starts empty


# ── When steps ───────────────────────────────────────────────────────────────

@when(parsers.parse('I click on "{task_name}" in the task list'))
def click_task(page, task_name):
    page.locator(".task-row", has_text=task_name).first.click()
    page.wait_for_selector(".detail-header")


# ── Then steps ───────────────────────────────────────────────────────────────

@then(parsers.parse('I see "{text}" in the task list'))
def see_in_list(page, text):
    page.locator(".task-list", has_text=text).wait_for(state="visible")


@then(parsers.parse('I do not see "{text}" in the task list'))
def not_see_in_list(page, text):
    from playwright.sync_api import expect
    # Use retrying assertion so React's async state updates are handled correctly
    expect(
        page.locator(".task-text", has_text=_re.compile(rf"^{_re.escape(text)}$"))
    ).to_have_count(0)


@then(parsers.parse('the detail panel shows "{text}"'))
def detail_shows(page, text):
    panel = page.locator(".detail-panel")
    assert text in panel.inner_text()
