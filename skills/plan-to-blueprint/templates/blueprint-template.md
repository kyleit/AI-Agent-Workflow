# Technical Blueprint: {{TITLE}}

- **Blueprint ID**: `{{BLUEPRINT_ID}}`
- **Requirement Spec ID**: `{{REQ_SPEC_ID}}`
- **Requirement Full Hash**: `{{REQ_FULL_HASH}}`
- **Brainstorming ID**: `{{BRAINSTORMING_ID}}`
- **Brainstorming Full Hash**: `{{BRAINSTORMING_FULL_HASH}}`
- **Roadmap ID**: `{{ROADMAP_ID}}`
- **Roadmap Full Hash**: `{{ROADMAP_FULL_HASH}}`
- **Plan ID**: `{{PLAN_ID}}`
- **Plan Full Hash**: `{{PLAN_FULL_HASH}}`
- **Plan Architecture Review ID**: `{{PLAN_ARCH_REVIEW_ID}}`
- **Version**: `{{VERSION}}`
- **Status**: `{{STATUS}}`
- **Full SHA-256**: `{{FULL_SHA256}}`

---

## 1. Current-State vs Target-State Architecture
- **Current State**: {{CURRENT_STATE_SUMMARY}}
- **Target State**: {{TARGET_STATE_SUMMARY}}

---

## 2. Component Boundaries & Interfaces
### 2.1 Components
- `COMP-01` [Type: {{COMP_1_TYPE}}]: {{COMP_1_RESPONSIBILITY}}

### 2.2 Interface Contracts
- `INT-01`: {{INTERFACE_NAME}} (Provider: `COMP-01`, Consumers: `[COMP-02]`)

---

## 3. Data Models & Data Flow
- `MODEL-01` [Type: DOMAIN_ENTITY]: {{MODEL_1_NAME}}
- **Data Flow**: {{DATA_FLOW_DESCRIPTION}}

---

## 4. Concurrency, Safe-Write & Error Handling
- **Concurrency Model**: `ASYNC_SERIAL`
- **Safe-Write Strategy**: `single_writer: true` (`Main Writer`)
- **Error Handling**: Standard error taxonomy mapping.

---

## 5. File Impact Map & Implementation Sequence
### 5.1 File Impact Map
| Path | Category | Write Allowed | Reason |
|---|---|---|---|
| `skills/example.md` | Authoritative Skill | Yes | Implementation target |

### 5.2 Implementation Sequence
1. `STEP-01`: {{STEP_1_OBJECTIVE}} (Files: `[skills/example.md]`)

---

## 6. Verification Matrix & Rollback Design
- **Verification Matrix**: {{VERIFICATION_MATRIX}}
- **Rollback Design**: {{ROLLBACK_DESIGN}}

---

## 7. Blueprint Readiness & Architecture Approval
- **Blueprint Readiness Gate**: `PASS` (Score >= 95/100)
- **Blueprint Architecture Approval**: `AWAITING_ARCHITECTURE_APPROVAL` (`review_type: BLUEPRINT_APPROVAL`)
- **Freeze Status**: `UNFROZEN`
