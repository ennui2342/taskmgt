Feature: DSL filter expressions
  As a user I want to filter tasks with compound logic
  so I can find tasks matching OR and NOT conditions.

  # Note: OR/AND scenarios test end-to-end DSL functionality.
  # The base64 encoding correctness is verified at the API unit test level
  # (tests/api/test_search.py) where the server fallback does not apply.

  Scenario: OR filter shows tasks matching either tag
    Given the task store has an open task "Read the paper #read"
    And the task store has an open task "Write the report #write"
    And the task store has an open task "Unrelated task"
    When I visit a favourite filter "(|(#read)(#write))"
    Then I see "Read the paper" in the task list
    And I see "Write the report" in the task list
    And I do not see "Unrelated task" in the task list

  Scenario: AND filter narrows to tasks matching all conditions
    Given the task store has an open task "High read task #read !1"
    And the task store has an open task "Low read task #read !2"
    And the task store has an open task "High write task #write !1"
    When I visit a favourite filter "(&(#read)(!1))"
    Then I see "High read task" in the task list
    And I do not see "Low read task" in the task list
    And I do not see "High write task" in the task list

  Scenario: NOT filter excludes tasks with a specific tag
    Given the task store has an open task "Read task #read"
    And the task store has an open task "Write task #write"
    And the task store has an open task "Plain task"
    When I visit a favourite filter "(!(#read))"
    Then I see "Write task" in the task list
    And I see "Plain task" in the task list
    And I do not see "Read task" in the task list

  Scenario: SmartAdd in a DSL favourite correctly seeds tokens
    Given the task store is empty
    When I visit a favourite filter "(&(#next)(@home))"
    And I create a task "Seed test" via SmartAdd
    Then I see "Seed test" in the task list
