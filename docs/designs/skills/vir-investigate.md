# Skill Specification — vir-investigate

---

## 1. Traceability & Owners
- **Purpose**: Root cause analysis and contradiction verification.
- **Owner**: Core Reasoning Team
- **Related FEAT**: `FEAT-075`
- **Related Blueprint**: `vir_platform_architecture_blueprint`

---

## 2. Core Specification
- **Name**: `vir-investigate`
- **Description**: Lightweight skill orchestrating RCA pipeline and contradiction resolution workflows.
- **Required Inputs**: `evidence_list`.
- **Produced Outputs**: `root_cause_verdict`.

---

## 3. Invocation Workflows
- **Workflows**: Pipeline receives evidence list -> Runs hypothesis compiler checks -> Asserts contradiction results.
- TODO: Refactor loop boundaries using schema checks matching `vir_platform_architecture_blueprint` (FEAT-074).
