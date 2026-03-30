"""Step definitions for navigation.feature"""
from pytest_bdd import given, when, then, scenarios, parsers
from .steps import *  # shared steps

scenarios("features/navigation.feature")


@given(parsers.parse('the task store has a wait task "{text}"'))
def add_wait_task(insert_task, text):
    insert_task(text, status="wait")


@given(parsers.parse('the task store has a started task "{text}"'))
def add_started_task(insert_task, text):
    insert_task(text, status="started")


@when('I visit the All Tasks view')
def visit_all(page, server_url):
    page.goto(f"{server_url}/view/all")
    page.wait_for_selector(".task-list")


@when('I visit the Inbox view')
def visit_inbox(page, server_url):
    page.goto(f"{server_url}/view/inbox")
    page.wait_for_selector(".task-list")


@when('I visit the Overdue view')
def visit_overdue(page, server_url):
    page.goto(f"{server_url}/view/overdue")
    page.wait_for_selector(".task-list")


@then(parsers.parse('the "{nav}" nav item is active'))
def nav_item_active(page, nav):
    active = page.locator(".nav-item.active a")
    assert nav in active.inner_text()


@when('I visit the Waiting view')
def visit_waiting(page, server_url):
    page.goto(f"{server_url}/view/wait")
    page.wait_for_selector(".task-list")


@when('I visit the Started view')
def visit_started(page, server_url):
    page.goto(f"{server_url}/view/started")
    page.wait_for_selector(".task-list")


@when(parsers.parse('I click the "{tag}" tag in the nav'))
def click_tag_nav(page, tag):
    page.locator(".nav-section a", has_text=tag).first.click()
    page.wait_for_selector(".task-list")
