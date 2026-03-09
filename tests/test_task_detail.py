"""Step definitions for task_detail.feature"""
from pytest_bdd import when, then, scenarios, parsers
from .steps import *  # shared steps

scenarios("features/task_detail.feature")


@when('I visit the All Tasks view')
def visit_all(page, server_url):
    page.goto(f"{server_url}/view/all")
    page.wait_for_selector(".task-list")


@then(parsers.parse('the detail panel shows priority "{priority}"'))
def detail_shows_priority(page, priority):
    assert priority in page.locator(".detail-panel").inner_text()


@then(parsers.parse('the detail panel shows location "{location}"'))
def detail_shows_location(page, location):
    assert location in page.locator(".detail-panel").inner_text()


@then(parsers.parse('the detail panel shows tag "{tag}"'))
def detail_shows_tag(page, tag):
    assert tag in page.locator(".detail-panel").inner_text()


@then(parsers.parse('the detail panel shows full text "{text}"'))
def detail_shows_full_text(page, text):
    assert text in page.locator(".detail-full-text code").inner_text()
