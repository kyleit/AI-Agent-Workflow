<!-- File path: docs/designs/FIX-025_runtime_test_classification_and_impact_execution_blueprint.md -->
---
artifact_type: blueprint
issue_id: FIX-025
workflow: quick-fix
status: draft
---
# Technical Design Blueprint – Refactor Runtime Test Strategy with Test Classification and Impact-Based Execution

## 1. Proposed Code Changes

### [pytest.ini](file:///E:/AgentsProject/pytest.ini)
- **Operation**: NEW
- **Responsibility**: Register pytest custom markers to enable classification of test suites.
- **Changes**: Add markers for `unit`, `integration`, `concurrency`, `e2e`, `smoke`, `stateful`, and `slow`.

### [skills/workflow-runtime/scripts/tia_engine.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/tia_engine.py)
- **Operation**: NEW
- **Responsibility**: Implement the dependency mapping resolver for Test Impact Analysis (TIA).
- **Changes**:
  - Class `TestImpactResolver` mapping changed source files to test files.
  - Method `resolve_affected_tests(changed_files: list[str]) -> list[str]` detecting affected tests.
  - Method `get_git_changed_files() -> list[str]` querying uncommitted and dirty workspace files using Git commands.

### [skills/workflow-runtime/tests/test_smoke.py](file:///E:/AgentsProject/skills/workflow-runtime/tests/test_smoke.py)
- **Operation**: NEW
- **Responsibility**: Implement a quick smoke test verifying system CLI startup and import health.
- **Changes**: Test CLI imports, initialization status checks, and exit codes.

### [skills/workflow-runtime/scripts/workflow_runtime.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
- **Operation**: MODIFY
- **Responsibility**: Register and handle the `aiwf test` subcommand.
- **Changes**:
  - Add CLI subcommands `affected`, `unit`, `integration`, `concurrency`, `smoke`, `full`.
  - Delegate execution calls to `pytest` targeting selected tests, with logging of run metrics and estimated saved time.

## 2. Target Folder Structure
```text
.
├── pytest.ini
└── skills/
    └── workflow-runtime/
        ├── scripts/
        │   ├── tia_engine.py
        │   └── workflow_runtime.py
        └── tests/
            └── test_smoke.py
```

## 3. Interface & Data Contracts
- **CLI Subcommand Structure**: `python workflow_runtime.py test <mode>`
  - Mode values: `affected | unit | integration | concurrency | smoke | full`.
- **Saved Time Estimations**: Flat rate of 1.5 seconds per skipped test file.

## 4. Algorithms & Key Logic

```python
# Pseudo-code for TIA resolver mapping
def resolve_affected_tests(changed_files):
    affected = {"skills/workflow-runtime/tests/test_smoke.py"}
    
    # Check if only doc files are changed
    if all(f.endswith((".md", ".json", ".txt")) for f in changed_files):
        return list(affected) # Skip python tests, run only smoke
        
    for f in changed_files:
        name = os.path.basename(f)
        if name.startswith("test_") and name.endswith(".py"):
            affected.add(f)
        elif name in SOURCE_TO_TEST_MAP:
            for t in SOURCE_TO_TEST_MAP[name]:
                affected.add(f"skills/workflow-runtime/tests/{t}")
                
    return list(affected)
```

## 5. Validation Rules
- Mode must be one of the registered choices.
- Git commands must fail gracefully (falling back to running smoke suite if no repository changes exist).

## 6. Implementation Checklist
- [ ] Create `pytest.ini` with custom markers.
- [ ] Create `skills/workflow-runtime/scripts/tia_engine.py`.
- [ ] Create `skills/workflow-runtime/tests/test_smoke.py`.
- [ ] Modify `skills/workflow-runtime/scripts/workflow_runtime.py` to register and run the `test` command.
- [ ] Mark existing tests in `skills/workflow-runtime/tests/` with the appropriate custom pytest decorators.

## 7. Verification & Test Plan
- Run the smoke suite directly:
  `python skills/workflow-runtime/scripts/workflow_runtime.py test smoke`
- Verify TIA affected test routing on modified source files.
