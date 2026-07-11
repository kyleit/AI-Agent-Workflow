# Skill Specification — frontend-design

---

## 1. Traceability & Owners
- **Purpose**: Declarative design tokens validation and UI compliance.
- **Owner**: Design Authority Team
- **Related FEAT**: `FEAT-065`
- **Related Blueprint**: `bp_vir_design_authority`

---

## 2. Core Specification
- **Name**: `frontend-design`
- **Description**: Style audit agent guidelines mapping and style violations flagging.
- **Required Inputs**: `allowed_tokens`, `computed_styles`.
- **Produced Outputs**: `violation_details`.

---

## 3. Invocation Workflows
- **Workflows**: Run layout audit -> Compare color tokens and margins -> Dispatch ADVISORY/VETO events.
- TODO: Add support for custom layout grid tokens matching `bp_vir_design_authority` (FEAT-065).
