Feature: Task detail panel
  As a user I want to see full task details when I select a task
  so I can understand what needs to be done.

  Scenario: Selecting a task opens the detail panel
    Given the task store has an open task "Deploy to production !1 #ops @desk"
    When I visit the All Tasks view
    And I click on "Deploy to production" in the task list
    Then the detail panel shows "Deploy to production"
    And the detail panel shows priority "High"
    And the detail panel shows location "@desk"
    And the detail panel shows tag "#ops"

  Scenario: Detail panel shows the full original text
    Given the task store has an open task "Some task !2 #work"
    When I visit the All Tasks view
    And I click on "Some task" in the task list
    Then the detail panel shows full text "Some task !2 #work"

  Scenario: No task selected shows placeholder
    Given the task store is empty
    When I visit the All Tasks view
    Then the detail panel shows "Select a task to view details"
