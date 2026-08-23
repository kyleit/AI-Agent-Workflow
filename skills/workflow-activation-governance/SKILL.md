---
name: workflow-activation-governance
command: activation-govern
aliases:
  - activation-readiness
  - e2e-audit
  - activation-approval
category: workflow
tags:
  - activation-governance
  - e2e-audit
  - readiness-assessment
  - activation-plan
version: 1.0.0
license: MIT
created_at: 2026-07-29
updated_at: 2026-07-29
role: end_to_end_audit_and_activation_governance_orchestrator
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
input_contract: valid_final_workflow_handoff
output_contract: activation_readiness_and_approval_package
activation_authorized: false
workflow_activation_performed: false
runtime_activation_performed: false
mirror_force_sync_performed: false
test_status: NOT_RUN
git_write_authorized: false
release_authorized: false
default_next_route: controlled-activation
description: Governs end-to-end audit verification across all 14 redesign phases, activation readiness scoring, activation plan drafting, activation rollback design, and activation approval request handoffs. Enforces strict read-only execution boundaries when Activation Approval is not provided.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

# Skill: workflow-activation-governance (End-to-End Audit & Activation Governance Engine)

## 0. Contract & Governance Boundaries

- **Role**: `end_to_end_audit_and_activation_governance_orchestrator`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Final Workflow Handoff)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Final Workflow Handoff` (`schemas/final-workflow-handoff.schema.json` v1.0.0)
- **Output Contracts**:
  - `End-to-End Audit Report` (`schemas/end-to-end-audit.schema.json` v1.0.0)
  - `Activation Readiness Assessment` (`schemas/activation-readiness.schema.json` v1.0.0)
  - `Activation Approval Request` (`schemas/activation-approval-request.schema.json` v1.0.0)
- **Activation Authorized**: `false` (Workflow activation requires explicit `ACTIVATION_APPROVAL`; in Phase 15 `ACTIVATION_APPROVAL` IS NOT PROVIDED)
- **Workflow Activation Performed**: `false` (STRICTLY FORBIDDEN)
- **Runtime Activation Performed**: `false` (STRICTLY FORBIDDEN)
- **Mirror Force Sync Performed**: `false` (STRICTLY FORBIDDEN)
- **Test Status**: `NOT_RUN` (Preserved 100%)
- **Git Write Authorized**: `false` (STRICTLY FORBIDDEN)
- **Release Authorized**: `false` (STRICTLY FORBIDDEN)
- **Default Next Route**: `controlled-activation` (Handoff candidate ONLY; NO workflow activation execution)

---

## 1. Purpose & Core Principles

The `workflow-activation-governance` skill manages end-to-end audit verification across all 14 redesign phases, authoritative source and manifest registry validation, authority matrix and approval separation auditing, readiness scoring, activation plan drafting, activation rollback design, and activation approval request handoffs.

### Core Principles
1. **Explicit Activation Approval Required**: Redesigned workflow activation CANNOT take place without explicit `ACTIVATION_APPROVAL`. In Phase 15, `ACTIVATION_APPROVAL` is NOT PROVIDED and activation status remains `NOT_RUN`.
2. **Comprehensive 14-Phase Audit**: All 14 prerequisite phase handoffs MUST be verified (`status: REVIEWED`, `gate: PASS`, `blocking_findings: []`).
3. **Single Canonical Entrypoint**: `workflow-coordinator` MUST be validated as the sole canonical entrypoint (`canonical_entrypoint_count: 1`).
4. **Strict Execution Boundaries**: Zero workflow activation, zero test suite execution, zero Git write, and zero release commands are performed in Phase 15.

---

## 2. End-to-End Phase Handoff Chain Audit

- Audits all 14 phase handoff files (`docs/aiwf-redesign/implementation-phase-01` through `phase-14`).
- Verifies 100% pass status (`schemas/end-to-end-audit.schema.json`).

---

## 3. Authoritative Source & Manifest Registry Audit

- Validates `MANIFEST.json` and authoritative Skills inventory under `skills/`.
- Verifies `workflow-coordinator` as the single canonical entrypoint.

---

## 4. Authority Matrix & Approval Separation Audit

- Verifies independent approval gates: `REQUIREMENT_APPROVAL`, `FEASIBILITY_APPROVAL`, `PLAN_APPROVAL`, `BLUEPRINT_APPROVAL`, `IMPLEMENTATION_ENTRY`, `TEST_EXECUTION_APPROVAL`, `GIT_APPROVAL`, `RELEASE_APPROVAL`, `ACTIVATION_APPROVAL`.
- Prohibits implicit approval inference across gates.

---

## 5. Gate Readiness, State Machine & Workflow Variant Audit

- Validates 9 workflow variants (STANDARD_FEATURE, QUICK_FEATURE, QUICK_FIX, etc.) and state transitions.
- Enforces 95/100 readiness threshold with Strict Blocking Rules.

---

## 6. End-to-End Traceability & Artifact Index Audit

- Consolidates complete 14-phase traceability chain from Raw Intent to Final Workflow Handoff (`schemas/final-artifact-index.schema.json`).

---

## 7. Non-Executing & Negative-Path Simulations

- Conducts 9 non-executing workflow simulations and 16 negative-path simulations without side effects.

---

## 8. Activation Readiness Assessment Model

Generates `schemas/activation-readiness.schema.json`:
- Candidate decision: `READY_FOR_ACTIVATION_APPROVAL` (Candidate ONLY; `activation_authorized: false`).

---

## 9. Activation Plan & Rollback Contracts

- **Activation Plan**: Formats structured plan (`schemas/activation-plan.schema.json`). Status: `READY_FOR_REVIEW` / `NOT_AUTHORIZED`.
- **Activation Rollback**: Formats rollback plan (`schemas/activation-rollback.schema.json`). Status: `READY`.

---

## 10. Activation Approval Request Handoff

Generates `schemas/activation-approval-request.schema.json`:
- Submits handoff request ONLY (`ACTIVATION_NOT_AUTHORIZED` in Phase 15).

---

## 11. Forbidden Routing Guards (STRICTLY BLOCKED)

- `UNAUTHORIZED → WORKFLOW_ACTIVATION_EXECUTION` (BLOCKED)
- `UNAUTHORIZED → RUNTIME_ACTIVATION_EXECUTION` (BLOCKED)
- `UNAUTHORIZED → FORCE_MIRROR_SYNC_EXECUTION` (BLOCKED)
