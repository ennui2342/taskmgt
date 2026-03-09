Feature: Left nav navigation
  As a user I want to navigate between task views
  so I can see the right subset of tasks.

  Scenario: All Tasks shows open tasks
    Given the task store has an open task "Write unit tests #dev"
    When I visit the All Tasks view
    Then I see "Write unit tests" in the task list
    And the "All Tasks" nav item is active

  Scenario: Inbox shows only untagged tasks
    Given the task store has an open task "Tagged task #dev"
    And the task store has an open task "Untagged task"
    When I visit the Inbox view
    Then I see "Untagged task" in the task list
    But I do not see "Tagged task" in the task list

  Scenario: Overdue shows tasks with past due dates
    Given the task store has an open task "Old task ^2020-01-01"
    And the task store has an open task "Future task ^2099-01-01"
    When I visit the Overdue view
    Then I see "Old task" in the task list
    But I do not see "Future task" in the task list

  Scenario: Tag nav links filter to that tag
    Given the task store has an open task "Research something #research"
    When I visit the All Tasks view
    And I click the "#research" tag in the nav
    Then I see "Research something" in the task list
