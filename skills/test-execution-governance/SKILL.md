---
name: test-execution-governance
command: test-govern
aliases:
  - test-plan
  - test-matrix
  - test-approval
category: workflow
tags:
  - test-governance
  - test-matrix
  - tester-ownership
  - final-verification
version: 1.0.0
license: MIT
created_at: 2026-07-29
updated_at: 2026-07-29
role: test_execution_governance_orchestrator
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
input_contract: valid_verification_handoff
output_contract: final_verification_decision_and_git_release_readiness_handoff
test_execution_authorized: policy
test_execution_owner: TESTER_OR_WORKFLOW_SUPERVISOR
tester_source_write_access: false
test_status: NOT_RUN
required_unrun_test_behavior: NOT_VERIFIED
git_write_authorized: false
release_authorized: false
default_next_route: implementation-to-release
description: Governs test requirement analysis, test matrix construction, test execution approval validation, TESTER agent task ownership, test session controls, retry/flaky governance, acceptance evidence reconciliation, final verification decision, and handoff to Git/Release governance.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

# Skill: test-execution-governance (Test Execution Governance Engine)

## Frontend Browser Matrix

When project discovery identifies a frontend, the test matrix MUST include a
real browser journey in this order: Mobile 375/390, Desktop 1440/1920, Tablet
768/820. The journey must capture screenshot SHA-256 evidence after automation,
validate DOM/layout/touch targets and runtime errors, and rerun after every fix.
Mock, fake, stub, static-only, or screenshot-only evidence cannot satisfy this
matrix or authorize verification.

## 0. Contract & Governance Boundaries

- **Role**: `test_execution_governance_orchestrator`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Verification Handoff)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Verification Handoff` (`schemas/verification-handoff.schema.json` v1.0.0, `test_status: NOT_RUN`)
- **Output Contracts**:
  - `Final Verification Decision` (`schemas/final-verification.schema.json` v1.0.0)
  - `Git & Release Readiness Handoff` (`schemas/git-release-readiness-handoff.schema.json` v1.0.0)
- **Test Execution Authorized**: resolved by the shared capability policy. Autonomous local validation proceeds without an additional manual command.
- **Test Execution Owner**: `TESTER` Agent for delegated test work, or `Workflow Supervisor` for autonomous local validation.
- **TESTER Source Write Access**: `false` (TESTER Agent CANNOT edit source code or test files directly)
- **Test Status**: `NOT_RUN` (Mandatory default in Phase 12)
- **Required Unrun Test Behavior**: `NOT_VERIFIED` (Unrun test criteria MUST be marked `NOT_VERIFIED`)
- **Git Write Authorized**: `false` (STRICTLY FORBIDDEN)
- **Release Authorized**: `false` (STRICTLY FORBIDDEN)
- **Default Next Route**: `git-governance` (Delegates Git Governance & Release Preparation)

---

## 1. Purpose & Core Principles

The `test-execution-governance` skill manages test requirement analysis, test matrix construction, approval validation, TESTER agent task ownership, test execution safety, flaky/retry policies, acceptance reconciliation, final verification decision, and Git/Release readiness handoff.

### Core Principles
1. **Capability-Driven Execution**: The runtime consults the shared capability policy. Autonomous local validation proceeds without an additional manual command; delegated, network, destructive, and production test work still requires the appropriate approval and ownership evidence.
2. **TESTER Agent ≠ Code Writer**: The `TESTER` Agent is the exclusive owner of test execution tasks. It MUST NOT write or modify source code or test files.
3. **Honest Acceptance Reconciliation**: Acceptance criteria requiring test suite execution that have not been run MUST BE MARKED **`NOT_VERIFIED`**.
4. **No Gate Override by Scores**: Weighted readiness or test scores MUST NOT override unfulfilled blocking conditions or unrun required tests.

---

## 2. Test Requirement Analysis & Test Matrix Model

- Analyzes test requirements from Requirements ACs, Blueprint Verification Matrix, Implementation Completion, and Verification Coverage Gaps.
- Constructs structured Test Matrix (`schemas/test-matrix.schema.json`) detailing test entries, commands, working directories, environments, timeouts, and resource limits.

---

## 3. Test Execution Approval Validation

- Validates `TEST_EXECUTION_APPROVAL` against `approval-record.schema.json`.
- Requires exact full SHA-256 match of `test_matrix_id` and `test_matrix_version`.
- When autonomous local validation is unavailable, the result must explicitly record `TEST_EXECUTION_UNAVAILABLE` and retain the reason; the Agent must not silently convert a missing manual command into `NOT_RUN`.

---

## 4. TESTER Agent Ownership & Safety Policies

- **Exclusive Ownership**: Only `TESTER` Agent can execute test commands when authorized.
- **Safety Defaults**: `network_allowed: false`, `destructive_allowed: false`, `production_allowed: false`, `max_parallelism: 1`, `timeout_seconds: 300`.
- Violating ownership or safety defaults triggers `TEST_OWNER_VIOLATION` (Gate: `BLOCKED`).

---

## 5. Controlled Test Session & Evidence Contract

- Defines test session lifecycle (`schemas/test-session.schema.json`) and test run evidence recording (`schemas/test-run-evidence.schema.json`).
- Tracks stdout/stderr references, exit codes, durations, and hashes. Evidence missing exit codes or environment binding is `INVALIDATED`.

---

## 6. Failure Classification & Flaky / Retry Governance

- Classifies failures into 14 categories (`schemas/test-failure.schema.json`).
- Retry policy requires explicit approval permission. Rerunning tests until PASS without retaining failure evidence IS STRICTLY PROHIBITED.
- Flaky tests MUST retain ALL execution attempts in evidence.

---

## 7. Acceptance Evidence Reconciliation

Reconciles final Acceptance Criteria status:
- `SATISFIED`: Passed required static, build, and approved test evidence.
- `NOT_VERIFIED`: Required test suite has not been run (`test_status: NOT_RUN`).
- `BLOCKED` / `NOT_SATISFIED`: Failed static, build, or test checks.

---

## 8. Final Verification Decision

Generates `schemas/final-verification.schema.json`:
- Supported decisions: `VERIFIED`, `VERIFIED_WITH_CONDITIONS`, `VERIFIED_WITHOUT_TESTS`, `VERIFICATION_INCOMPLETE`, `FAILED`, `BLOCKED`, `INVALIDATED`.
- In Phase 12, the mandatory decision is **`VERIFIED_WITHOUT_TESTS`** or **`VERIFICATION_INCOMPLETE`**.

---

## 9. Final Architecture Conformance Reconciliation

Reconciles architectural conformance records from `architecture-review` (`review_type: FINAL_CONFORMANCE`). Non-conformance blocks final verification.

---

## 10. Git & Release Readiness Handoff

Generates `schemas/git-release-readiness-handoff.schema.json`:
- Candidate status: `READY_FOR_GIT_REVIEW` (Candidate ONLY; `git_actions_authorized: []`, `release_authorized: false`).
- Does NOT grant Git commit/push approval or Release authorization.

---

## 11. Change Control & Auto-Invalidation

If any upstream artifact (Requirement, Blueprint, Execution, Debug, Verification, or Test Matrix) changes:
- Active test sessions ARE IMMEDIATELY `INVALIDATED`.
- Test approvals ARE `REVOKED`.
- Re-evaluation IS REQUIRED.

---

## 12. Forbidden Routing Guards (STRICTLY BLOCKED)

- `UNAUTHORIZED → TEST_SUITE_EXECUTION` (BLOCKED)
- `TESTER → SOURCE_OR_TEST_CODE_WRITE` (BLOCKED)
- `UNRUN_TESTS → CLAIMED_VERIFIED_STATUS` (BLOCKED)
- `TEST_GOVERNANCE → GIT_WRITE / RELEASE_EXECUTION` (BLOCKED)
