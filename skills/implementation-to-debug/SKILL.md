---
name: implementation-to-debug
command: debug
aliases:
  - compile
  - lint
  - analyze
category: workflow
tags:
  - debug
  - hypothesis
  - root-cause
  - governance
version: 3.3.0
license: MIT
created_at: 2026-07-04
updated_at: 2026-07-29
role: debug_lifecycle_orchestrator
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
input_contract: valid_debug_handoff
output_contract: debug_report_and_remediation_handoff
allowed_input_completion_statuses:
  - COMPLETED
  - COMPLETED_WITH_FINDINGS
  - BLOCKED_WITH_DEBUGGABLE_FAILURE
test_execution_authorized: false
debug_source_write_authorized: false
default_next_route: debug-to-verify
description: Governs the reproduction, hypothesis tracking, root-cause analysis, and remediation design lifecycle for implementation failures. Enforces patch authorization boundaries (Debug CANNOT edit source directly) and handoff to verification.
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

# Skill: implementation-to-debug (Debug Lifecycle Engine)

## 0. Contract & Governance Boundaries

- **Role**: `debug_lifecycle_orchestrator`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Implementation Completion)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Valid Debug Handoff` (`schemas/debug-handoff.schema.json` v1.0.0, `test_status: NOT_RUN`)
- **Output Contracts**:
  - `Debug Session Artifact` (`schemas/debug-session.schema.json` v1.0.0)
  - `Root Cause Record` (`schemas/root-cause.schema.json` v1.0.0)
  - `Debug Patch Authorization` (`schemas/debug-patch-authorization.schema.json` v1.0.0)
- **Allowed Input Completion Statuses**: `COMPLETED`, `COMPLETED_WITH_FINDINGS`, `BLOCKED_WITH_DEBUGGABLE_FAILURE`
- **Debug Source Write Authorized**: `false` (Debug Agent CANNOT write source code directly! Edits require formal Patch Authorization and `Main Writer` assignment)
- **Test Execution Authorized**: `false` (Tests default to `NOT_RUN`; test execution for reproduction IS PROHIBITED in Phase 11)
- **Git Write Authorized**: `false` (STRICTLY FORBIDDEN)
- **Release Authorized**: `false` (STRICTLY FORBIDDEN)
- **Default Next Route**: `debug-to-verify` (ONLY AFTER Root-Cause Identification and Static Re-verification)

> [!CRITICAL]
> **Cross-Skill Strict Policy & Physical Write Invariant**:
> **STRICT ENGINEERING POLICY IS AUTHORITATIVE.**
> The skill MUST load the Core Engineering Policy (`.agents/policies/strict-engineering.md`), Physical Repository Write Policy (`.agents/policies/physical-repository-write.md`), all active Language Profiles (`.agents/profiles/*.yaml`), and the Project Architecture Contract (`.agents/contracts/engineering-quality-gates.yaml`) before diagnosing or patching code.
> A skill MUST NOT weaken, bypass, suppress, reinterpret, or locally override a blocking gate.
> Debug principle is ROOT CAUSE > WORKAROUND. Diagnostic suppression (`# type: ignore`, `@ts-ignore`, `_ = err`, typed dummy fallbacks) IS STRICTLY FORBIDDEN. Debug patches MUST physically write to canonical project files on disk and execute read-back verification. If a fix requires an architectural change outside the approved Blueprint, Debug MUST raise Blueprint Drift and route through AIWF change control.

---

## 1. Purpose & Core Principles

The `implementation-to-debug` skill orchestrates the systematic reproduction, hypothesis generation, root-cause analysis, and remediation design for implementation defects.

### Core Principles
1. **Requires Valid Debug Handoff Input**: Accepts ONLY completed or debuggable implementation handoffs with verified SHA-256 hashes and `test_status: NOT_RUN`.
2. **Debug Agent ≠ Writer**: The Debug Agent analyzes failures, formulates hypotheses, and identifies root causes. It MUST NOT write source code patches directly.
3. **Evidence-Based Reproduction**: Reproduction analysis uses existing logs, static inspection, build reports, and dry-run outputs. Executing test suites for reproduction IS PROHIBITED in Phase 11.
4. **Formal Patch Authorization**: Source code patches require formal Debug Patch Authorization (`schemas/debug-patch-authorization.schema.json`) and MUST be executed by the assigned `Main Writer`.

---

## 2. Input Contract & Prerequisites Validation

Validates the debug handoff containing:
- `debug_handoff_id`, `execution_id`, `completion_record_id`
- `blueprint_identity`, `files_changed`, `change_records`, `static_verification`, `test_status: NOT_RUN`
- `known_failures`, `open_findings`, `expected_behavior`, `acceptance_criteria`, `verification_matrix`, `full SHA-256`

Missing any mandatory item or hash mismatch triggers `DEBUG_ENTRY_BLOCKED`.

---

## 3. Debug Lifecycle State Machine

```text
NOT_STARTED → ENTRY_VALIDATING → INTAKE_READY → REPRODUCTION_ANALYZING → HYPOTHESES_GENERATING → HYPOTHESES_EVALUATING → ROOT_CAUSE_IDENTIFIED → REMEDIATION_DESIGNING → PATCH_AUTHORIZATION_REQUIRED → PATCH_AUTHORIZED → STATIC_REVERIFYING → READY_FOR_VERIFICATION
```
*Secondary States*: `PATCH_NOT_AUTHORIZED`, `BLOCKED`, `NEEDS_MORE_INFORMATION`, `RECOVERY_REQUIRED`, `CANCELLED`, `INVALIDATED`, `SUPERSEDED`.

Forbidden Transitions: `NOT_STARTED → PATCH_AUTHORIZED`, `ROOT_CAUSE_IDENTIFIED → DIRECT_SOURCE_WRITE`, `READY_FOR_VERIFICATION → RELEASE`.

---

## 4. Reproduction Analysis & Evidence

- Distinguishes observed failure, expected behavior, reproduction evidence, environment, and preconditions.
- Uses existing logs, static code inspection, and user-provided evidence. Test execution for reproduction IS PROHIBITED in Phase 11.

---

## 5. Debug Hypothesis Model

- Formulates structured hypotheses (`schemas/debug-hypothesis.schema.json`) specifying `statement`, `supporting_evidence`, `contradicting_evidence`, `affected_components`, and `confidence`.
- Evaluates hypotheses systematically; rejected hypotheses ARE RETAINED in audit trail.

---

## 6. Root-Cause Analysis Contract

- Generates root-cause records (`schemas/root-cause.schema.json`) with `causal_chain`, `evidence`, and status (`CONFIRMED`, `PROBABLE`).
- Remediation recommendations ARE PERMITTED ONLY for `CONFIRMED` or `PROBABLE` root causes.

---

## 7. Remediation Design & Patch Authorization Boundary

- Debug Agent designs minimal remediation options (`summary`, `approach`, `affected_files`, `risk`, `rollback`).
- Source edits CANNOT be executed directly. Submits `debug-patch-authorization-request.md`. Upon approval (`PATCH_AUTHORIZED`), patch execution is assigned to `Main Writer`.

---

## 8. Blueprint Deviation & Requirement Change Guards

- If remediation conflicts with Frozen Blueprint: Submits `Blueprint Deviation Request`.
- If remediation modifies user acceptance criteria: Submits `Requirement Change Request`.
- Direct modification of Blueprint or Requirement files IS STRICTLY FORBIDDEN.

---

## 9. Quick Flow Debug & Patch Contracts

- **Quick Feature Debug**: Uses lightweight intake and static re-verification.
- **Quick Fix Debug**: Uses patch contract handoff, root-cause evidence, and regression boundary definition.

---

## 10. Change Control & Auto-Invalidation

If upstream Blueprint, Freeze, or Execution Completion hashes drift:
- The debug session IS IMMEDIATELY `INVALIDATED`.
- Active patch authorizations ARE `REVOKED`.
- Re-evaluation IS REQUIRED.

---

## 11. Forbidden Routing Guards (STRICTLY BLOCKED)

- `DEBUG → DIRECT_SOURCE_WRITE_BY_DEBUG_AGENT` (BLOCKED)
- `DEBUG → TEST_SUITE_EXECUTION` (BLOCKED)
- `DEBUG → GIT_WRITE / RELEASE_EXECUTION` (BLOCKED)
- `UNAUTHORIZED_PATCH → SOURCE_MODIFICATION` (BLOCKED)
