<!-- File path: docs/designs/FEAT-051_harden_implementation_phases_and_release_gate_blueprint.md -->

---
feature_id: FEAT-051
feature_name: Harden AIWF Implementation Flow and Release Gate
status: reviewed
stage: blueprint
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../plans/FEAT-051_harden_implementation_phases_and_release_gate_plan.md
next_artifact: ../../skills/workflow-runtime/scripts/
---

# Technical Design Blueprint & Implementation Contract – Harden AIWF Implementation Flow and Release Gate

## 0. Baseline Context & References

- **Memory Baseline**: High confidence. `workflow_runtime.py` (3223 lines) has existing `release_manager.py` and `approval_gate.py`. `.agents/state/approvals.json` tracks user approvals.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/release_manager.py` — Existing release flow.
  - `skills/workflow-runtime/scripts/approval_gate.py` — Approval gate checks.
  - `.agents/runtime/checkpoints.json` — Checkpoint schema reference.

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/ledger.py` | NEW | Read/write `implementation-ledger.json`; phase lifecycle helpers | `atomic_writer.py` (FEAT-050) | Low – new standalone module |
| `skills/workflow-runtime/scripts/phase_controller.py` | NEW | Check phase boundaries; compute `suggested_next_skill`; update ledger | `ledger.py`, `state_aggregator.py` | Medium – core phase logic |
| `skills/workflow-runtime/scripts/release_gate.py` | NEW | Pre-release validation gate; hard-blocks release if conditions unmet | `ledger.py`, `worker_manager.py` (FEAT-052) | High – gates all releases |
| `.agents/runtime/implementation-ledger.json` | NEW (schema) | Persisted implementation progress | None | Low – new file |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Add `implement resume` and `implement partial-release` sub-commands | `phase_controller.py`, `release_gate.py` | High – CLI entry point |
| `skills/implementation-to-release/SKILL.md` | MODIFY | Mandate `release_gate.validate()` before any release step | None | Low – documentation |
| `skills/software-development-workflow/SKILL.md` | MODIFY | Update phase transition rules: Phase N done → continue Phase N+1 | None | Low – documentation |

---

## 2. Target Folder Structure

```text
skills/workflow-runtime/
├── scripts/
│   ├── ledger.py              [NEW] – Implementation ledger read/write
│   ├── phase_controller.py    [NEW] – Phase boundary & next skill logic
│   ├── release_gate.py        [NEW] – Hard release gate validator
│   └── workflow_runtime.py    [MODIFY] – implement resume/partial-release

.agents/
├── runtime/
│   └── implementation-ledger.json  [NEW SCHEMA]
│       {
│         "feature_id": "FEAT-XXX",
│         "implementation_status": "in_progress|completed",
│         "current_phase": "Phase 1",
│         "phases": [{
│           "id": "Phase 1", "title": "...", "status": "pending|in_progress|completed",
│           "completion_type": "phase_complete|feature_complete",
│           "tasks": ["Task 1.1", "Task 1.2"]
│         }],
│         "release_allowed": false,
│         "verify_allowed": false,
│         "debug_allowed": true,
│         "release_block_reason": "...",
│         "orphan_process_check": "pass|fail"
│       }
```

---

## 3. Complete Class & Module Design

### `ledger.py` — ImplementationLedger

- **Responsibilities**: CRUD operations on `implementation-ledger.json`. Phase lifecycle management. Backward compatibility for single-phase blueprints.
- **Public Methods**:
  - `load() -> dict` — Load ledger from disk; return empty ledger template if file missing.
  - `save(data: dict) -> None` — Write ledger atomically.
  - `init_from_blueprint(blueprint_json: dict) -> dict` — Parse blueprint JSON, create ledger with all phases/tasks set to `pending`.
  - `mark_phase_started(phase_id: str) -> None` — Set phase status to `in_progress`.
  - `mark_phase_completed(phase_id: str) -> None` — Set phase status to `completed`; recompute `implementation_status`.
  - `mark_task_completed(task_id: str) -> None` — Set task status to `completed` inside parent phase.
  - `get_next_incomplete_phase() -> str | None` — Return first phase with status != `completed`, or None if all complete.
  - `is_feature_complete() -> bool` — True if all phases completed.
  - `get_release_gate_status() -> dict` — Return `{release_allowed, debug_allowed, verify_allowed, release_block_reason}`.
- **Backward Compatibility**: If blueprint has no `phases` key, wrap all tasks into a synthetic `Phase 1` with `id = "Phase 1"`.

### `phase_controller.py` — PhaseController

- **Responsibilities**: Evaluate ledger state after each phase completes; update `StateAggregator` target; enforce monotonic phase progression.
- **Public Methods**:
  - `on_phase_completed(phase_id: str) -> dict` — Called after a phase finishes. Returns `{next_action, next_phase_id, message, release_allowed}`.
  - `resume_next_phase() -> str | None` — Find next incomplete phase and return its ID.
  - `get_phase_summary() -> list[dict]` — Return list of phase statuses for display.
- **Decision Logic**:
  ```
  if remaining_phases > 0:
      next_action = "continue_implement"
      message = "Phase X completed. Continue with Phase Y."
  else:
      next_action = "debug"
      message = "All phases complete. Run /debug."
  ```

### `release_gate.py` — ReleaseGate

- **Responsibilities**: Hard pre-release validation. Must pass all conditions before any Release action proceeds.
- **Public Methods**:
  - `validate() -> tuple[bool, str]` — Returns `(allowed: bool, reason: str)`. Checks all conditions in order.
  - `validate_partial(phase_id: str) -> tuple[bool, str]` — Validate partial release for a single phase.
  - `require_explicit_confirmation(text: str) -> bool` — Check that user input exactly matches `"Approve partial release for Phase X"`.
- **Validation Conditions** (ordered, all must pass):
  1. `implementation-ledger.json` exists.
  2. All phases status == `completed`.
  3. All tasks status == `completed`.
  4. `workers.json` has no `running` or `starting` workers.
  5. `file-locks.json` has no `active` locks.
  6. Debug report exists at `docs/debug/FEAT-XXX_debug.md` with status PASS.
  7. Verify report exists at `docs/reviews/FEAT-XXX_verify.md` with status PASS.
  8. User explicitly invoked release (not auto-triggered).

---

## 4. Detailed Interface Contracts

### `init_from_blueprint(blueprint_json: dict) -> dict`
- **Parameters**: `blueprint_json` must have `feature_id`. `phases` array optional (backward compat).
- **Return**: Ledger dict ready to be saved. All phases/tasks initialized to `pending`.
- **Exceptions**: `ValueError` if `feature_id` missing.

### `validate() -> tuple[bool, str]`
- **Return**: `(True, "")` if allowed; `(False, "<reason>")` if blocked.
- **Reason format**: `"Release blocked: FEAT-XXX is only partially implemented. Completed phases: Phase 1. Remaining: Phase 2, Phase 3. Continue with /implement --phase Phase 2"`.
- **Exceptions**: `FileNotFoundError` if ledger missing → auto-blocks release.

### `on_phase_completed(phase_id: str) -> dict`
- **Return**: `{next_action: str, next_phase_id: str | None, message: str, release_allowed: bool}`.
- **Side-effect**: Updates ledger on disk atomically.

---

## 5. Configuration Schema

```json
{
  "release_gate": {
    "require_debug_report": true,
    "require_verify_report": true,
    "require_all_phases_complete": true,
    "allow_partial_release": false
  }
}
```

---

## 6. Database & Storage Design

- **`implementation-ledger.json`** full schema:
  ```json
  {
    "feature_id": "FEAT-XXX",
    "blueprint_path": "docs/designs/FEAT-XXX_..._blueprint.md",
    "implementation_status": "in_progress",
    "current_phase": "Phase 1",
    "phases": [
      {
        "id": "Phase 1",
        "title": "...",
        "status": "completed",
        "completion_type": "phase_complete",
        "tasks": ["Task 1.1", "Task 1.2"]
      }
    ],
    "tasks": {
      "Task 1.1": {"status": "completed", "phase": "Phase 1", "completed_at": "ISO8601"}
    },
    "release_allowed": false,
    "release_block_reason": "Remaining phases: Phase 2.",
    "debug_allowed": false,
    "verify_allowed": false,
    "orphan_process_check": "pass",
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
  }
  ```

---

## 7. Cache Architecture

- No cache. Ledger read directly from disk on every call (file is small, ~2-10KB).

---

## 8. Error Model

| Exception | Trigger | Recovery Strategy | Log Level |
| :--- | :--- | :--- | :--- |
| `LedgerNotFoundError(FileNotFoundError)` | Ledger missing when validate() called | Auto-block release; prompt to run /implement | ERROR |
| `PrematureReleaseError(PermissionError)` | release_gate.validate() returns False | Print block reason; stop release entirely | CRITICAL |
| `InvalidPhaseTransitionError(ValueError)` | Attempting to mark Phase N+2 complete without Phase N+1 | Raise; log attempted transition | ERROR |
| `PartialReleaseConfirmationError(ValueError)` | User text doesn't match required confirmation pattern | Reject; print required confirmation text | WARNING |

---

## 9. Skill Integration Contracts

### `blueprint-to-implementation/SKILL.md`
- **Before Hook**: `ledger.init_from_blueprint(blueprint_json)` called at start.
- **After Each Phase**: `phase_controller.on_phase_completed(phase_id)` called; display menu.

### `implementation-to-release/SKILL.md`
- **Before ANY release step**: `release_gate.validate()` must return `(True, "")`. If False, print block reason and STOP.

---

## 10. CLI & Runtime Contracts

| Command | Parameters | Output | Exit Code |
| :--- | :--- | :--- | :--- |
| `implement resume` | none | JSON `{phase_id, phase_title, tasks_remaining}` | 0 resumed, 1 nothing to resume |
| `implement partial-release` | `--phase "Phase X"` | JSON `{confirmed, release_note_path}` | 0 confirmed, 1 rejected |
| `implement status` | none | JSON `{phases[], current_phase, release_allowed, release_block_reason}` | 0 |

---

## 11. Sequence Flows

### Phase Completion → Next Phase Flow
1. Coder marks Phase 1 done; calls `phase_controller.on_phase_completed("Phase 1")`.
2. PhaseController reads ledger; detects Phase 2 is `pending`.
3. Returns `{next_action: "continue_implement", next_phase_id: "Phase 2", message: "Phase 1 complete. Continue Phase 2.", release_allowed: false}`.
4. StateAggregator updates `suggested_next_skill = "blueprint-to-implementation"`.
5. Dashboard shows: `Next: /implement --phase Phase 2. Release: BLOCKED`.

### Release Attempt → Gate Block Flow
1. User invokes `/release` after Phase 1 only.
2. `release_gate.validate()` checks ledger → Phase 2 still pending.
3. Returns `(False, "Release blocked: Remaining phases: Phase 2, Phase 3.")`.
4. Release aborted. Block reason printed clearly.

### Partial Release Confirmation Flow
1. User requests partial release for Phase 1.
2. System prints: `Type exactly: "Approve partial release for Phase 1"`.
3. User types confirmation text.
4. `require_explicit_confirmation()` validates match.
5. Partial release note created: `docs/releases/FEAT-XXX_Phase_1_partial_release.md`.
6. Feature NOT marked as fully released.

---

## 12. Security & Safety

- **Monotonic Transitions Only**: Phase status can only go `pending → in_progress → completed`. No reversals.
- **Release Hard Gate**: `release_gate.validate()` cannot be bypassed by any CLI argument.
- **Partial Release Labeling**: Partial releases must be labeled with `_partial: true` and `_phases_released: ["Phase 1"]`.

---

## 13. Complete Test Matrix

| Req ID | Test Type | Test File | Component | Assertion |
| :--- | :--- | :--- | :--- | :--- |
| FR-01 | Unit | `test_ledger.py` | `ImplementationLedger` | init_from_blueprint creates correct phase structure |
| FR-02 | Unit | `test_phase_controller.py` | `PhaseController` | Phase 1 done with Phase 2 pending → next_action = continue_implement |
| FR-03 | Integration | `test_phase_controller.py` | `implement resume` | Resume finds Phase 2 and returns correct phase_id |
| FR-04 | Unit | `test_release_gate.py` | `ReleaseGate` | validate() returns False when Phase 2 incomplete |
| FR-05 | Unit | `test_release_gate.py` | `ReleaseGate` | require_explicit_confirmation() True only on exact match |
| TC-01 | Integration | `test_ledger.py` | `ImplementationLedger` | Single-phase blueprint creates 1 synthetic phase |

---

## 14. Requirement Traceability Matrix

- `FR-01` → Task 1.1 → `ImplementationLedger.init_from_blueprint()` → `ledger.py` → `test_ledger.py`
- `FR-02` → Task 1.2 → `PhaseController.on_phase_completed()` → `phase_controller.py` → `test_phase_controller.py`
- `FR-03` → Task 1.3 → `implement resume` CLI → `workflow_runtime.py` → `test_phase_controller.py`
- `FR-04` → Task 2.1 → `ReleaseGate.validate()` → `release_gate.py` → `test_release_gate.py`
- `FR-05` → Task 2.2 → `ReleaseGate.require_explicit_confirmation()` → `release_gate.py` → `test_release_gate.py`

---

## 15. File-Level Implementation Contracts

- **File**: `skills/workflow-runtime/scripts/ledger.py`
  - **Purpose**: Single source of truth for implementation progress.
  - **Owner**: Coder
  - **Notes**: `save()` must use `AtomicWriter`. `load()` returns empty template (not None) if file missing.

- **File**: `skills/workflow-runtime/scripts/phase_controller.py`
  - **Purpose**: Phase boundary logic. Pure computation — no side effects beyond ledger update.
  - **Owner**: Coder
  - **Notes**: Must work without FEAT-052 Worker Manager (optional dependency).

- **File**: `skills/workflow-runtime/scripts/release_gate.py`
  - **Purpose**: Hard validation gate. MUST be called before every release action.
  - **Owner**: Coder
  - **Notes**: Each validation condition checked independently; all must pass. Block reason lists ALL failing conditions.

- **File**: `skills/workflow-runtime/scripts/workflow_runtime.py` (MODIFY)
  - **Purpose**: Add `implement` sub-parser with `resume` and `partial-release` sub-commands.
  - **Owner**: Coder
  - **Notes**: `implement resume` exit 1 with message "No incomplete phases found" if everything complete.
