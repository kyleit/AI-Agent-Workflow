# FEAT-998: Single Phase Legacy Blueprint

> **Note**: This is a single-phase legacy-format blueprint (no multi-phase structure).
> Used to test backward compatibility of the ledger module's auto-detect logic.

## Overview

- **Feature ID**: FEAT-998
- **Feature Name**: Single Phase Legacy Implementation  
- **Format**: Legacy (no `phases` array — all tasks in flat `implementation_packages`)

## Implementation Packages

### Task 1: Setup Environment

```json
{
  "task_id": "Task 1",
  "module": "Phase 1",
  "write_set": ["scripts/setup.py"],
  "dependencies": [],
  "implementation_notes": "Setup the environment"
}
```

### Task 2: Implement Core Module

```json
{
  "task_id": "Task 2",
  "module": "Phase 1",
  "write_set": ["src/core.py"],
  "dependencies": ["Task 1"],
  "implementation_notes": "Implement core module"
}
```

### Task 3: Write Tests

```json
{
  "task_id": "Task 3",
  "module": "Phase 1",
  "write_set": ["tests/test_core.py"],
  "dependencies": ["Task 2"],
  "implementation_notes": "Write unit tests"
}
```

## Verification

```bash
python -m pytest tests/test_core.py -v
```

## Expected Outputs

- `scripts/setup.py`
- `src/core.py`
- `tests/test_core.py`
