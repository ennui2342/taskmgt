"""Step definitions for crud.feature"""
from pytest_bdd import when, then, scenarios, parsers
from .steps import *  # shared steps

scenarios("features/crud.feature")


@when('I visit the All Tasks view')
def visit_all(page, server_url):
    page.goto(f"{server_url}/view/all")
    page.wait_for_selector(".task-list")


@when(parsers.parse('I visit the tag view for "{tag}"'))
def visit_tag(page, server_url, tag):
    page.goto(f"{server_url}/view/tag?tag={tag}")
    page.wait_for_selector(".task-list")


@when(parsers.parse('I visit the location view for "{location}"'))
def visit_location(page, server_url, location):
    page.goto(f"{server_url}/view/location?location={location}")
    page.wait_for_selector(".task-list")


@when(parsers.parse('I type "{text}" in the task input'))
def type_in_input(page, text):
    page.locator(".smartadd-input").fill(text)


@when('I submit the task input')
def submit_input(page):
    page.locator(".smartadd-input").press("Enter")
    page.wait_for_selector(".task-list")


@when('I click the Edit button')
def click_edit(page):
    page.locator(".btn-edit").click()
    page.wait_for_selector(".detail-edit-form")


@when(parsers.parse('I clear the task text and type "{text}"'))
def clear_and_type(page, text):
    page.locator(".detail-edit-input").fill(text)


@when('I click Save')
def click_save(page):
    page.locator(".btn-save").click()
    page.wait_for_selector(".detail-header")


@when('I click Cancel')
def click_cancel(page):
    page.locator(".btn-cancel").click()
    page.wait_for_selector(".detail-header")


@when('I click Delete')
def click_delete(page):
    page.locator(".btn-delete").click()
    page.wait_for_selector(".btn-delete-confirm")


@when('I confirm the deletion')
def confirm_delete(page):
    page.locator(".btn-delete-confirm").click()
    page.wait_for_selector(".action-bar-empty")
