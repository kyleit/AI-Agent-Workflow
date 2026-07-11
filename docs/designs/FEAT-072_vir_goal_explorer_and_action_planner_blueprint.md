<!-- File path: docs/designs/FEAT-072_vir_goal_explorer_and_action_planner_blueprint.md -->

---
feature_id: FEAT-072
feature_name: Visual Intelligence Runtime — Goal Explorer & Action Planner
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-072_vir_goal_explorer_and_action_planner_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Goal Explorer & Action Planner

## 0. Baseline Context & References
- **Memory Baseline**: Memory of graph traversal logic and A* search heuristics models.
- **RAG Query Summaries**: Explorer uses `TouchEngine` and `DigitalTwin` APIs from Phase 2 and 3 to execute clicks and read updated state hashes.
- **Inspected Source Files**:
  - [FEAT-072 Plan](file:///e:/AgentsProject/docs/plans/FEAT-072_vir_goal_explorer_and_action_planner_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/planner/spec_parser.py` | Create | Parse target state parameters and preconditions from test specs | None | Medium. Reads user goal specifications. |
| `vir_runtime/planner/graph.py` | Create | Maintain State Transition Graph (STG) and backtrack paths | None | High. Model layout transitions. |
| `vir_runtime/planner/pathfinder.py` | Create | Compute shortest action sequence to target states (A* search) | `graph.py` | High. Action router processor. |
| `vir_runtime/planner/security.py` | Create | Classify actions and block destructive changes unless authorized | None | High. Safety coordinator gate. |
| `vir_runtime/planner/loop.py` | Create | Monitor and flag repeated cyclic navigation patterns | `graph.py` | Low. Detects tab click loops. |
| `vir_runtime/planner/bridge.py` | Create | Translate plan paths to Touch Engine interaction arrays | None | Medium. Interfaces path sequences to touch execution. |
| `vir_runtime/planner/forms.py` | Create | Populate input forms dynamically with pre-generated seed values | None | Low. Form auto-fill manager. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── planner/
    ├── bridge.py
    ├── forms.py
    ├── graph.py
    ├── loop.py
    ├── pathfinder.py
    ├── security.py
    └── spec_parser.py
```

---

## 3. Complete Class & Module Design

### 3.1 StateTransitionGraph
- **Class / Module Name**: `vir_runtime.planner.graph.StateTransitionGraph`
  - **Responsibilities**: Model layout transitions, map DOM hashes to nodes, catalog action edges, and handle backtrack state recoveries.
  - **Constructor Parameters**: None.
  - **Public Methods**:
    - `def add_node(state_hash: str) -> None`
    - `def add_edge(from_hash: str, to_hash: str, action: Dict[str, Any]) -> None`
    - `def get_backtrack_route(from_hash: str) -> List[Dict[str, Any]]`

### 3.2 Pathfinder
- **Class / Module Name**: `vir_runtime.planner.pathfinder.Pathfinder`
  - **Responsibilities**: Run A* search on STG nodes to find shortest path to goal state hashes, calculating path costs.
  - **Constructor Parameters**:
    - `graph: StateTransitionGraph`
  - **Public Methods**:
    - `def find_shortest_path(start_hash: str, target_hash: str) -> List[Dict[str, Any]]`
  - **Dependencies**: `vir_runtime.planner.graph`

---

## 4. Detailed Interface Contracts

- **API Signature**: `def find_shortest_path(start_hash: str, target_hash: str) -> List[Dict[str, Any]]`
  - **Parameters**:
    - `start_hash` (string representing current DOM state hash)
    - `target_hash` (string representing goal state hash matching preconditions)
  - **Return Types**: Returns a list of action dictionaries to execute sequentially.
  - **Exceptions**:
    - `GoalUnreachableError` - If no valid path connects start to target.

---

## 5. Configuration Schema

- **Target Schema (`safety.yaml`)**:
```yaml
safety:
  exploration_limits:
    max_steps: 100
    max_duration_seconds: 300
  destructive_actions:
    block_patterns: ["*delete*", "*remove*", "*clear*"]
    override_allowed: false
```

---

## 6. Database & Storage Design
- Visual baseline hashes and explored routes layouts are saved to SQLite `vir_digital_twin` tables.

---

## 7. Cache Architecture
- **Pathfinder Route Cache**:
  - Memory dictionary storing computed shortest paths to speed up duplicate goal queries.

---

## 8. Error Model

- **Exception Class**: `GoalUnreachableError`
  - **Trigger Condition**: Pathfinder search tree finishes traversing nodes without matching the target state.
  - **Recovery Strategy**: Publish `goal.unreachable` alert event, rollback state to home node, halt exploration.
  - **Logging Requirements**: WARNING log referencing the target state parameters.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Path Exploration & Backtrack Flow**:
  1. `Pathfinder` computes shortest path steps array.
  2. `ActionSafetyChecker` validates actions against patterns.
  3. Action executed via `TouchEngine`.
  4. Node transition fails (unexpected layout shifts occur).
  5. Pathfinder retrieves `get_backtrack_route()` to last healthy node.
  6. Return path executed; exploration recalibrated.

---

## 12. Security & Safety
- **Workspace Boundary Safety**: Dynamic form fillers block typing system paths or executing terminal strings, protecting against injection attacks inside inputs.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-04` | Unit Test | `tests/unit/test_pathfinder.py` | `pathfinder.py` | `self.assertEqual(len(path), 3)` |
| `FR-07` | Unit Test | `tests/unit/test_action_safety.py` | `security.py` | `self.assertTrue(is_blocked)` |

---

## 14. Requirement Traceability Matrix
- `FR-04` -> Task 1.3 -> Class `Pathfinder` -> `pathfinder.py` -> `test_pathfinder.py` -> Verified.
- `FR-07` -> Task 1.5 -> Class `ActionSafetyChecker` -> `security.py` -> `test_action_safety.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/planner/security.py`
  - **Purpose**: Action safety checker filter.
  - **Owner**: Verifier
  - **Inputs / Outputs / Dependencies**: Depends on rules loaded from `safety.yaml`.
