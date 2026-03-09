Feature: Task CRUD operations
  As a user I want to create, edit and delete tasks
  so I can manage my task list.

  Scenario: Create a new task via the SmartAdd bar
    Given the task store is empty
    When I visit the All Tasks view
    And I type "Buy oat milk" in the task input
    And I submit the task input
    Then I see "Buy oat milk" in the task list

  Scenario: Create a task with SmartAdd tokens
    Given the task store is empty
    When I visit the All Tasks view
    And I type "Call dentist !1 @phone" in the task input
    And I submit the task input
    Then I see "Call dentist" in the task list

  Scenario: Edit an existing task
    Given the task store has an open task "Old task name"
    When I visit the All Tasks view
    And I click on "Old task name" in the task list
    And I click the Edit button
    And I clear the task text and type "New task name"
    And I click Save
    Then I see "New task name" in the task list
    And I do not see "Old task name" in the task list

  Scenario: Cancel editing a task restores the detail view
    Given the task store has an open task "Task to edit"
    When I visit the All Tasks view
    And I click on "Task to edit" in the task list
    And I click the Edit button
    And I click Cancel
    Then the detail panel shows "Task to edit"

  Scenario: Delete a task
    Given the task store has an open task "Task to delete"
    When I visit the All Tasks view
    And I click on "Task to delete" in the task list
    And I click Delete
    And I confirm the deletion
    Then I do not see "Task to delete" in the task list

  Scenario: Adding a task in a tag view inherits the tag
    Given the task store is empty
    When I visit the tag view for "work"
    And I type "Call the client" in the task input
    And I submit the task input
    Then I see "Call the client" in the task list

  Scenario: Adding a task in a location view inherits the location
    Given the task store is empty
    When I visit the location view for "home"
    And I type "Fix the shelf" in the task input
    And I submit the task input
    Then I see "Fix the shelf" in the task list
