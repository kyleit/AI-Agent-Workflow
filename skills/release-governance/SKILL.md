---
name: release-governance
command: release-govern
aliases:
  - release-readiness
  - release-approval
  - final-handoff
category: workflow
tags:
  - release-governance
  - final-handoff
  - artifact-integrity
  - post-release-verification
version: 1.0.0
license: MIT
created_at: 2026-07-29
updated_at: 2026-07-29
role: release_governance_and_final_handoff_orchestrator
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
input_contract: valid_release_preparation_package
output_contract: final_workflow_handoff_and_release_readiness
release_authorized: false
deploy_authorized: false
production_migration_authorized: false
test_status: NOT_RUN
git_write_authorized: false
default_next_route: workflow-activation-governance
description: Governs release readiness assessment, artifact inventory integrity validation, version/changelog/migration/rollback reconciliation, environment and channel target validation, release action taxonomy, release execution planning, post-release verification planning, and final end-to-end workflow handoff. Enforces strict read-only execution boundaries when Release Approval is not provided.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

# Skill: release-governance (Release Governance & Final Workflow Handoff Engine)

## 0. Contract & Governance Boundaries

- **Role**: `release_governance_and_final_handoff_orchestrator`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Git Governance)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Release Preparation Package` (`schemas/release-preparation.schema.json` v1.0.0, `release_authorized: false`)
- **Output Contracts**:
  - `Release Readiness Assessment` (`schemas/release-readiness.schema.json` v1.0.0)
  - `Release Approval Request` (`schemas/release-approval-request.schema.json` v1.0.0)
  - `Final Workflow Handoff` (`schemas/final-workflow-handoff.schema.json` v1.0.0)
  - `Final Artifact Index` (`schemas/final-artifact-index.schema.json` v1.0.0)
- **Release Authorized**: `false` (Release execution requires explicit `RELEASE_APPROVAL`; in Phase 14 `RELEASE_APPROVAL` IS NOT PROVIDED)
- **Deploy Authorized**: `false` (STRICTLY FORBIDDEN)
- **Production Migration Authorized**: `false` (STRICTLY FORBIDDEN)
- **Git Write Authorized**: `false` (STRICTLY FORBIDDEN)
- **Test Status**: `NOT_RUN` (Preserved 100%)
- **Default Next Route**: `post-release-lifecycle` (Handoff candidate ONLY; NO release execution)

---

## 1. Purpose & Core Principles

The `release-governance` skill manages release readiness assessment, artifact inventory integrity validation, version/changelog/migration/rollback reconciliation, environment/channel target validation, release action planning, post-release verification planning, and final end-to-end workflow handoff.

### Core Principles
1. **Explicit Release Approval Required**: Release execution CANNOT take place without explicit `RELEASE_APPROVAL`. In Phase 14, `RELEASE_APPROVAL` is NOT PROVIDED and release execution status remains `NOT_RUN`.
2. **Strict Blocking Rules**: Missing approval, invalid artifact hashes, missing rollback plans, or open critical findings MUST trigger `BLOCKED` readiness regardless of numerical scores.
3. **Strict Execution Boundaries**: No publish, image push, deployment, production migration, or Git write commands are executed in Phase 14.
4. **Honest Traceability & Status**: Final Workflow Handoff MUST state `release_approval_status: NOT_PROVIDED`, `release_status: NOT_RUN`, and `test_status: NOT_RUN`.

---

## 2. Release Artifact Inventory & Integrity Validation

- Validates artifact inventory (`schemas/artifact-inventory.schema.json`) including artifact types, full SHA-256 hashes, source commits, and provenance references.
- Unbuilt artifacts ARE REPORTED TRUTHFULLY as `ARTIFACT_NOT_BUILT`. Fake checksums ARE STRICTLY FORBIDDEN.

---

## 3. Release Readiness Assessment Model

Generates `schemas/release-readiness.schema.json`:
- Evaluates 18 readiness dimensions against threshold `95/100`.
- Enforces **Strict Blocking Rules**: Missing approval, invalid hashes, or open critical findings override scores and yield `BLOCKED` status.

---

## 4. Version, Changelog & Migration Reconciliation

- Reconciles candidate versioning across repository, modules, container tags, and docs.
- Reconciles evidence-based changelog drafts. Unverified test claims ARE STRICTLY FORBIDDEN.
- Reconciles database/schema migration plans and rollback procedures.

---

## 5. Environment & Channel Governance

- Models release targets (LOCAL, TEST, STAGING, PRODUCTION) and channels.
- Production environment defaults to `NOT_AUTHORIZED`.

---

## 6. Release Action Taxonomy & Safety Policies

- Models 15 release action types independently (`config/release-actions.yaml`).
- All side-effect actions (BUILD, PUBLISH, PUSH_IMAGE, DEPLOY, APPLY_MIGRATION) ARE BLOCKED in Phase 14.

---

## 7. Release Approval Request & Validation

- Validates `RELEASE_APPROVAL` against `approval-record.schema.json`.
- In Phase 14, `RELEASE_APPROVAL` is NOT PROVIDED. Status transitions to `RELEASE_NOT_AUTHORIZED`.

---

## 8. Release Execution Plan & Ownership Boundaries

- Generates controlled execution plan (`schemas/release-execution-plan.schema.json`).
- Status remains `PLANNED` / `NOT_EXECUTED`.

---

## 9. Pre-Release Checks & Tool Executor Release Boundary

- Pre-release check contract evaluates 16 verification criteria (`config/release-safety-policies.yaml`).
- Tool Executor release boundary blocks all side-effect executions in Phase 14.

---

## 10. Post-Release Verification Plan

- Generates post-release verification plan (`schemas/post-release-verification.schema.json`).
- Post-release test execution REQUIRES independent `TEST_EXECUTION_APPROVAL`.

---

## 11. Release Invalidation, Failure Taxonomy & Recovery

- Supports 17 failure categories (`schemas/release-failure.schema.json`).
- Artifact hash drift or source commit changes IMMEDIATELY INVALIDATE active release plans and readiness packages.

---

## 12. Final Workflow Handoff & End-to-End Traceability

- Generates `schemas/final-workflow-handoff.schema.json` and `schemas/final-artifact-index.schema.json`.
- Consolidates complete 14-phase traceability chain from Raw Intent to Release Governance.
- Reports `release_approval_status: NOT_PROVIDED`, `release_status: NOT_RUN`, `next_allowed_actions: [REQUEST_RELEASE_APPROVAL]`.

---

## 13. Forbidden Routing Guards (STRICTLY BLOCKED)

- `UNAUTHORIZED → RELEASE_OR_DEPLOYMENT_EXECUTION` (BLOCKED)
- `UNAPPROVED_RELEASE → WORKFLOW_COMPLETE` (BLOCKED)
- `UNAUTHORIZED → PRODUCTION_MIGRATION_EXECUTION` (BLOCKED)
