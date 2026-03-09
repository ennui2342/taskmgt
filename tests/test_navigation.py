"""Step definitions for navigation.feature"""
from pytest_bdd import when, then, scenarios, parsers
from .steps import *  # shared steps

scenarios("features/navigation.feature")


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


@when(parsers.parse('I click the "{tag}" tag in the nav'))
def click_tag_nav(page, tag):
    page.locator(".nav-section a", has_text=tag).first.click()
    page.wait_for_selector(".task-list")
