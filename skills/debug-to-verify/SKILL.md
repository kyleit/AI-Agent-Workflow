---
name: debug-to-verify
command: verify
aliases:
  - check
  - audit
  - governance-verify
category: workflow
tags:
  - verification
  - evidence
  - static-checks
  - governance
version: 3.3.0
license: MIT
created_at: 2026-07-04
updated_at: 2026-07-29
role: verification_governance_orchestrator
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
input_contract: debug_remediated_handoff
output_contract: verification_handoff_and_architecture_conformance
allowed_input_debug_statuses:
  - READY_FOR_VERIFICATION
test_execution_authorized: false
test_execution_owner: TESTER
test_status: NOT_RUN
git_write_authorized: false
release_authorized: false
default_next_route: architecture-review
description: Governs the evidence consolidation, static verification, acceptance criteria mapping, independent verification review, and final architecture conformance handoff. Enforces Test Authorization guards (tests default to NOT_RUN) and honest limitations reporting.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

> [!CRITICAL]
> ## ⛔ MANDATORY ENFORCEMENT GUARDS — READ BEFORE ANY ACTION
>
> **YOU MUST COMPLY WITH ALL 5 GUARDS BELOW. VIOLATION = IMMEDIATE STOP.**
>
> 1. **BOOTSTRAP FIRST**: You MUST have executed `initialize-workflow` skill and possess a valid Bootstrap Receipt (SHA-256) BEFORE executing this skill. If you have NOT loaded AI_RULES.md, AGENTS.md, and memory context — STOP NOW and run `initialize-workflow` first.
>
> 2. **COORDINATOR ROUTING**: This skill MUST be invoked via `workflow-coordinator` delegation chain (`aiwf → initialize-workflow → workflow-coordinator → this skill`). Direct invocation from raw user prompt is FORBIDDEN.
>
> 3. **NO BLUEPRINT = NO CODE**: Source code MUST NOT be created, modified, or deleted until a Technical Design Blueprint exists under `docs/features/` AND is explicitly approved by the user. Spec and Blueprint documents MUST be created FIRST.
>
> 4. **PHYSICAL WRITES ONLY**: All file changes MUST be physical writes to the project filesystem using file creation/edit tools. The following are NOT valid implementation and are STRICTLY FORBIDDEN:
>    - IDE "proposed changes" or "Apply" button
>    - Code blocks in chat/conversation response presented as implementation
>    - IDE virtual patches or preview mode
>    - Any change that exists only in AI response but not on disk
>    - Ref: Physical Repository Write Policy (AI_RULES.md Section 33)
>
> 5. **DOCUMENTATION FIRST**: Required workflow documents (Spec, Blueprint, Report) MUST be created BEFORE or IN THE SAME TRANSACTION as source code changes. No source change is complete without its corresponding document update.

# Skill: debug-to-verify (Verification Governance Engine)

## 0. Contract & Governance Boundaries

- **Role**: `verification_governance_orchestrator`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Debug Ready for Verification)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Debug Remediation Handoff` (`schemas/debug-session.schema.json` v1.0.0, status `READY_FOR_VERIFICATION`)
- **Output Contracts**:
  - `Verification Session Artifact` (`schemas/verification.schema.json` v1.0.0)
  - `Acceptance Evidence Mapping` (`schemas/acceptance-evidence.schema.json` v1.0.0)
  - `Verification Handoff Artifact` (`schemas/verification-handoff.schema.json` v1.0.0)
- **Allowed Input Debug Statuses**: `READY_FOR_VERIFICATION`
- **Test Execution Authorized**: `false` (Tests default to `NOT_RUN`; `TESTER` Agent is exclusive owner when approved)
- **Test Execution Owner**: `TESTER` Agent
- **Test Status**: `NOT_RUN` (In Phase 11, Test Execution Approval IS NOT PROVIDED)
- **Git Write Authorized**: `false` (STRICTLY FORBIDDEN)
- **Release Authorized**: `false` (STRICTLY FORBIDDEN)
- **Default Next Route**: `test-execution-governance` (Delegates Final Verification Decision & Test Governance)

> [!CRITICAL]
> **Cross-Skill Strict Policy & Physical Write Invariant**:
> **STRICT ENGINEERING POLICY IS AUTHORITATIVE.**
> The skill MUST load the Core Engineering Policy (`.agents/policies/strict-engineering.md`), Physical Repository Write Policy (`.agents/policies/physical-repository-write.md`), all active Language Profiles (`.agents/profiles/*.yaml`), and the Project Architecture Contract (`.agents/contracts/engineering-quality-gates.yaml`) before executing static verification.
> A skill MUST NOT weaken, bypass, suppress, reinterpret, or locally override a blocking gate.
> Verify is the HARD-GATE OWNER for Physical Repository Mutation Integrity (`disk = truth`, working tree inspection) and Language Profile Static Validators (Pyright STRICT, golangci-lint, tsc strict, ESLint, Import Linter, depguard, file-size <= 500 lines). Verify MUST independently confirm physical file writes on disk. ALL active language profiles MUST PASS (no cross-language compensation). Unit/integration tests remain `NOT_RUN` unless explicitly authorized.
> If compliance requires an architecture change outside the skill's current approved authority, the skill MUST raise architecture/blueprint drift and route through AIWF change control.

---

## 1. Purpose & Core Principles

The `debug-to-verify` skill manages evidence consolidation, static verification, acceptance criteria mapping, independent verification review, and final architecture conformance integration.

### Core Principles
1. **Verification ≠ Test Execution**: Verification encompasses static checks, schema validation, contract references, build checks, and acceptance evidence mapping. It DOES NOT equate to running test suites.
2. **Honest Acceptance Mapping**: Acceptance criteria requiring test suite execution that have not been run MUST BE MARKED **`NOT_VERIFIED`**. Claiming `SATISFIED` for unrun tests IS STRICTLY PROHIBITED.
3. **Test Authorization Guard**: Running unit/integration/E2E test suites requires explicit `TEST_EXECUTION_APPROVAL` and MUST be executed by `TESTER` Agent. In Phase 11, tests remain **`NOT_RUN`**.
4. **Final Architecture Conformance**: Submits evidence to `architecture-review` with `review_type: FINAL_CONFORMANCE` for architectural compliance audit.

---

## 2. Input Contract & Prerequisites Validation

Validates the debug handoff containing:
- `debug_session_id`, `execution_id`, `completion_record_id`, `blueprint_identity`, `requirement_identity`
- Debug status: `READY_FOR_VERIFICATION`
- `files_changed`, `change_records`, `static_verification`, `test_status: NOT_RUN`, `full SHA-256`

Missing any item or hash drift triggers `VERIFICATION_ENTRY_BLOCKED`.

---

## 3. Verification Lifecycle State Machine

```text
NOT_STARTED → ENTRY_VALIDATING → EVIDENCE_COLLECTING → STATIC_VERIFYING → BUILD_VERIFYING → TEST_AUTHORIZATION_CHECKING → TESTS_NOT_AUTHORIZED → EVIDENCE_CONSOLIDATING → INDEPENDENT_REVIEW → READY_FOR_ARCHITECTURE_CONFORMANCE
```
*Secondary Outcomes*: `VERIFIED_WITHOUT_TESTS`, `VERIFIED_WITH_FINDINGS`, `VERIFICATION_INCOMPLETE`, `BLOCKED`, `FAILED`, `CANCELLED`, `INVALIDATED`, `SUPERSEDED`.

In Phase 11, `TESTS_NOT_AUTHORIZED` IS THE MANDATORY DEFAULT STATE.

---

## 4. Verification Activity Taxonomy

- **Static Activities** (Allowed): `STATIC_CHECK`, `SCHEMA_VALIDATION`, `REFERENCE_VALIDATION`, `ROUTE_VALIDATION`, `HASH_VALIDATION`, `DIFF_SCOPE_VALIDATION`.
- **Build Activities** (Allowed if static): `BUILD_CHECK` (Static compilation/config check without hidden test execution).
- **Test Activities** (Blocked in Phase 11): `UNIT_TEST`, `INTEGRATION_TEST`, `E2E_TEST`, `PERFORMANCE_TEST`, `SECURITY_TEST`. All test activities default to **`NOT_RUN`**.

---

## 5. Acceptance Evidence Mapping

- Maps Requirement -> AC -> Verification Activity -> Evidence -> Status.
- Status values: `SATISFIED`, `PARTIALLY_SATISFIED`, `NOT_SATISFIED`, `NOT_VERIFIED`, `BLOCKED`, `NOT_APPLICABLE`.
- If an AC requires test suite execution that has not been run: Status MUST be **`NOT_VERIFIED`**.

---

## 6. Static Verification Contract

Performs comprehensive static verification:
- Skill frontmatter & Markdown structure parsing.
- Schema reference & contract validation.
- Full SHA-256 hash consistency checks.
- Allowed/protected file scope validation.
- Direct mirror edit checks (`.agents/skills/**` forbidden).

---

## 7. Build Verification Contract

- Performs static build/config inspection ONLY when command is verified not to trigger hidden test execution.
- Build PASS proves compilation scope ONLY; it DOES NOT prove unit/integration test pass.

---

## 8. Test Authorization & TESTER Ownership

- Test execution REQUIRES explicit `TEST_EXECUTION_APPROVAL` issued to `TESTER` Agent.
- In Phase 11, `test_execution_authorized: false`. Test execution status is strictly **`NOT_RUN`**.
- Attempting to execute tests without authorization or under a non-TESTER role triggers `TEST_OWNER_VIOLATION` (Gate: `BLOCKED`).

---

## 9. Independent Verification Review

- Invokes Independent Reviewer Agent (`templates/independent-verification-review.md`).
- Reviewer operates in `READ_ONLY` mode, verifying that static evidence is authentic and test limitations are reported honestly.

---

## 10. Final Architecture Conformance Integration

Submits request (`templates/final-conformance-request.md`) to `skills/architecture-review/SKILL.md` with `review_type: FINAL_CONFORMANCE`. Evaluates architectural alignment of implemented components.

---

## 11. Verification-to-Next-Phase Handoff

Generates `verification-handoff.schema.json` containing:
- Upstream identities, `verification_outcome: VERIFIED_WITHOUT_TESTS`, `test_status: NOT_RUN`
- `unverified_items`, `architecture_conformance_record`
- `git_status: NOT_RUN`, `release_readiness_candidate: false` (NO implied Git or Release approval).

---

## 12. Change Control & Auto-Invalidation

If any upstream artifact (Requirement, Brainstorming, Roadmap, Plan, Blueprint, Execution, or Debug) changes (full SHA-256 hash drift):
- The verification session IS IMMEDIATELY `INVALIDATED`.
- Conformance requests ARE `REVOKED`.
- Re-verification IS REQUIRED.

---

## 13. Forbidden Routing Guards (STRICTLY BLOCKED)

- `VERIFICATION → TEST_SUITE_EXECUTION` (BLOCKED in Phase 11)
- `VERIFICATION → GIT_WRITE / RELEASE_EXECUTION` (BLOCKED)
- `UNRUN_TESTS → CLAIMED_SATISFIED_STATUS` (BLOCKED)
- `BUILD_PASS → CLAIMED_TEST_PASS` (BLOCKED)
