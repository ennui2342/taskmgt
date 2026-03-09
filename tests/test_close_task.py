"""Step definitions for close_task.feature"""
from pytest_bdd import when, then, scenarios
from .steps import *  # shared steps

scenarios("features/close_task.feature")


@when('I visit the All Tasks view')
def visit_all(page, server_url):
    page.goto(f"{server_url}/view/all")
    page.wait_for_selector(".task-list")


@when('I click the "Close task" button')
def click_close(page):
    page.locator(".btn-close").click()
    # Wait for the action bar to revert to the empty state, confirming the htmx swap completed
    page.wait_for_selector(".action-bar-empty")


@then('the "Close task" button is not visible')
def close_not_visible(page):
    assert page.locator(".btn-close").count() == 0


@then('the "Close task" button is visible')
def close_visible(page):
    page.locator(".btn-close").wait_for(state="visible")
