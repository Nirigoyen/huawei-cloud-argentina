# Task Template

Copy this directory to create a new task. Replace `_template` with your task name.

## Structure

```
task_name/
  task.yaml      # metadata: id, vertical, difficulty, language, prompt, timeout_seconds, points
  setup/         # files placed in working dir before harness runs
  tests/         # test files (pytest, jest, go test, etc.)
  eval.py        # evaluation script -> JSON {passed, metrics, details}
  solution/      # reference solution
```

## task.yaml fields

| field | description |
|-------|-------------|
| id | unique task identifier (matches directory name) |
| vertical | one of: code_generation, software_design, devops, iac, security, documentation, debugging, refactoring, data_engineering, testing |
| difficulty | easy, medium, or hard |
| language | python, javascript, rust, go, java, etc. |
| prompt | the task prompt given to the agent |
| timeout_seconds | max time for the agent to complete |
| points | scoring weight |

## eval.py contract

eval.py must:
1. Run the test suite (pytest, jest, etc.)
2. Print a JSON object to stdout: `{"passed": bool, "metrics": dict, "details": list}`
3. Exit 0 if passed, 1 if failed
