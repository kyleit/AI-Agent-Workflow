# Requirement Specification: {{TITLE}}

- **Requirement Spec ID**: `{{REQ_ID}}`
- **Feature/Fix ID**: `{{WORK_ITEM_ID}}`
- **Intent ID**: `{{INTENT_ID}}`
- **Version**: `{{VERSION}}`
- **Status**: `{{STATUS}}`
- **Owner**: `{{OWNER}}`
- **Full SHA-256**: `{{FULL_SHA256}}`

---

## 1. Problem Statement
- **Statement**: {{PROBLEM_STATEMENT}}
- **Affected Actors**: {{AFFECTED_ACTORS}}
- **Observed Evidence**: {{OBSERVED_EVIDENCE}}
- **Current Impact**: {{CURRENT_IMPACT}}

---

## 2. Goals & Non-Goals
### 2.1 Goals
- `GOAL-01`: {{GOAL_1_DESC}} [Priority: MUST]

### 2.2 Non-Goals
- `NGOAL-01`: {{NON_GOAL_1_DESC}} [Reason: {{REASON}}]

---

## 3. Actors & Use Cases
### 3.1 Actors
- `ACTOR-01`: {{ACTOR_1_NAME}} ({{ACTOR_1_TYPE}})

### 3.2 Use Cases
- `UC-01`: {{UC_1_TITLE}}
  - **Primary Actor**: `ACTOR-01`
  - **Main Flow**: {{MAIN_FLOW}}

---

## 4. Functional Requirements
- `REQ-01`: {{REQ_1_TITLE}}
  - **Statement**: System MUST {{STATEMENT}}.
  - **Priority**: `MUST`
  - **Acceptance Criteria IDs**: `[AC-01]`

---

## 5. Non-Functional Requirements (NFRs)
- `NFR-01` [Performance]: Response time MUST be < 200ms.

---

## 6. Constraints
- `CONST-01`: {{CONSTRAINT_DESC}}

---

## 7. Data, Error & Edge Cases
- **Data Sensitivity**: `CONFIDENTIAL`
- **Error Behavior**: System MUST display user-friendly error on network failure.
- **Edge Case `EDGE-01`**: Network drop during submission -> Retry automatically.

---

## 8. Acceptance Criteria
- `AC-01`:
  - **Requirement ID**: `REQ-01`
  - **Given**: {{PRECONDITION}}
  - **When**: {{ACTION}}
  - **Then**: {{EXPECTED_RESULT}}
  - **Verification Method**: `STATIC_CHECK`

---

## 9. Traceability
`Raw Intent` -> `Normalized Intent` -> `GOAL-01` -> `UC-01` -> `REQ-01` -> `AC-01`

---

## 10. Approval Record Request
- **Approval Status**: `AWAITING_OWNER_APPROVAL`
- **Required**: `True`
