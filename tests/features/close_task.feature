Feature: Close a task
  As a user I want to close a task
  so it is removed from my open task list.

  Scenario: Closing a task removes it from the list
    Given the task store has an open task "Fix the bug"
    When I visit the All Tasks view
    And I click on "Fix the bug" in the task list
    And I click the "Close task" button
    Then I do not see "Fix the bug" in the task list
    And the detail panel shows "Select a task to view details"

  Scenario: Close button only appears when a task is selected
    Given the task store has an open task "Some task"
    When I visit the All Tasks view
    Then the "Close task" button is not visible
    When I click on "Some task" in the task list
    Then the "Close task" button is visible
