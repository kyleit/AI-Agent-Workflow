# Skill Specification — frontend-visual-debug

---

## 1. Traceability & Owners
- **Purpose**: Declarative visual assertions and elements interaction diagnostics.
- **Owner**: QA Engineering Team
- **Related FEAT**: `FEAT-058`
- **Related Blueprint**: `bp_vir_vision_engine`

---

## 2. Core Specification
- **Name**: `frontend-visual-debug`
- **Description**: Lightweight skill managing visual testing flows, finding selectors, and asserting layout properties.
- **Required Inputs**: `element_selector`, `action_type`.
- **Produced Outputs**: `action_result`.

---

## 3. Invocation Workflows
- **Workflows**: User requests element diagnostics -> Skill compiles action replay -> Dispatches to BrowserAdapter.
- TODO: Implement dynamic click route checks matching `bp_vir_goal_action_planner` (FEAT-072).
