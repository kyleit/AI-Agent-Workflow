---
name: git-governance
command: git-govern
aliases:
  - git-plan
  - git-readiness
  - release-prep
category: workflow
tags:
  - git-governance
  - release-preparation
  - secret-inspection
  - pr-governance
version: 1.0.0
license: MIT
created_at: 2026-07-29
updated_at: 2026-07-29
role: git_governance_and_release_preparation_orchestrator
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
input_contract: valid_git_release_readiness_handoff
output_contract: git_readiness_and_release_preparation_package
git_write_authorized: false
release_authorized: false
test_status: NOT_RUN
default_next_route: release-governance
description: Governs repository state snapshotting, change scope reconciliation, secret and sensitive content inspection, Git action planning, Git approval validation, commit packaging, pull request planning, and release preparation packaging. Enforces strict read-only execution boundaries when Git/Release approvals are not provided.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

# Skill: git-governance (Git Governance & Release Preparation Engine)

## 0. Contract & Governance Boundaries

- **Role**: `git_governance_and_release_preparation_orchestrator`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Final Verification)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Git & Release Readiness Handoff` (`schemas/git-release-readiness-handoff.schema.json` v1.0.0, `git_actions_authorized: []`)
- **Output Contracts**:
  - `Git Readiness Decision` (`schemas/git-readiness.schema.json` v1.0.0)
  - `Release Preparation Package` (`schemas/release-preparation.schema.json` v1.0.0)
  - `Release Approval Request Handoff` (`schemas/release-approval-request.schema.json` v1.0.0)
- **Git Write Authorized**: `false` (Git write operations require explicit `GIT_APPROVAL`; in Phase 13 `GIT_APPROVAL` IS NOT PROVIDED)
- **Release Authorized**: `false` (Release execution requires explicit `RELEASE_APPROVAL`; in Phase 13 `RELEASE_APPROVAL` IS NOT PROVIDED)
- **Allowed Git Operations**: Read-only Git metadata inspection ONLY (`git rev-parse`, `git status --short`, `git diff --stat`, `git log`). Execution of write commands (`git add`, `commit`, `push`, `PR`, `merge`, `tag`) IS STRICTLY FORBIDDEN.
- **Test Status**: `NOT_RUN` (Preserved 100%)
- **Default Next Route**: `implementation-to-release` (Handoff candidate ONLY; NO release execution)

---

## 1. Purpose & Core Principles

The `git-governance` skill manages repository state snapshotting, change scope reconciliation, secret inspection, Git action planning, Git approval validation, commit packaging, pull request planning, version governance, changelog drafting, and release preparation packaging.

### Core Principles
1. **Requires Independent Approvals**: `GIT_APPROVAL` and `RELEASE_APPROVAL` are independent gates. `GIT_APPROVAL` DOES NOT grant `RELEASE_APPROVAL`.
2. **No Implicit Command Authorization**: `COMMIT` approval DOES NOT imply `PUSH` approval; `PUSH` approval DOES NOT imply `PR` creation; `PR` approval DOES NOT imply `MERGE`; `MERGE` approval DOES NOT imply `TAG`.
3. **Strict Read-Only Boundary**: In Phase 13, zero Git write commands are executed. All action plans remain `PLANNED` or `NOT_AUTHORIZED`.
4. **Honest Status Representation**: Commit messages, PR descriptions, and release preparation notes MUST report test status as `Tests: NOT RUN`.

---

## 2. Repository State Snapshot Contract

- Captures read-only repository metadata (`schemas/repository-snapshot.schema.json`): `current_branch`, `head_commit`, `staged_changes`, `unstaged_changes`, `untracked_files`.
- Credential tokens in remote URLs ARE REDACTED.

---

## 3. Change Scope Reconciliation & Safety Inspection

- Reconciles Git diff against Implementation allowed files, change ledger, and verification handoffs (`schemas/change-scope-reconciliation.schema.json`).
- Detects unauthorized out-of-scope files, protected file edits, mirror file edits (`.agents/skills/**`), and sensitive content risks. Any finding triggers `BLOCKED` readiness.

---

## 4. Secret, Sensitive & Generated File Inspection

- Scans read-only diffs for API keys, tokens, credentials, and private keys.
- Scans for build outputs, cache files, and large binaries. Sensitive values ARE REDACTED in reports.

---

## 5. Git Action Taxonomy & Safety Policies

- Models 16 Git action types independently (`schemas/git-action-plan.schema.json`).
- Safety defaults: `force_push_forbidden: true`, `rebase_forbidden: true`, `delete_branch_forbidden: true`.

---

## 6. Git Approval Validation

- Validates `GIT_APPROVAL` against `approval-record.schema.json`. Requires exact full SHA-256 match of `repository_snapshot_id` and `head_commit`.
- In Phase 13, `GIT_APPROVAL` is NOT PROVIDED. Status transitions to `GIT_ACTION_NOT_AUTHORIZED`.

---

## 7. Staging Plan & Commit Package Contracts

- **Staging Plan**: Defines explicit path lists (`schemas/staging-plan.schema.json`). `git add .` IS FORBIDDEN.
- **Commit Package**: Formats structured commit messages (`schemas/commit-package.schema.json`) detailing change scope, requirement references, and `Tests: NOT RUN`.

---

## 8. Branch, Push, PR, Merge & Tag Governance

- **PR Plan**: Prepares draft PR specification (`schemas/pull-request-plan.schema.json`).
- **Merge & Tag Governance**: Models merge strategies and release tags independently. Requires explicit individual approvals.

---

## 9. Git Readiness Decision

Generates `schemas/git-readiness.schema.json`:
- Decision: `READY_FOR_GIT_APPROVAL` (Candidate ONLY; `git_actions_authorized: []`).

---

## 10. Release Preparation Package & Version Governance

Generates `schemas/release-preparation.schema.json`:
- Candidate versioning according to SemVer rules.
- Drafts evidence-based changelog without unverified claims.

---

## 11. Release Approval Request Handoff

Generates `schemas/release-approval-request.schema.json`:
- Submits handoff request ONLY (`RELEASE_NOT_AUTHORIZED` in Phase 13).

---

## 12. Invalidation & Recovery Contracts

- If HEAD commit, branch, or working tree state drifts: All active Git action plans and Release preparation packages ARE IMMEDIATELY `INVALIDATED`.

---

## 13. Forbidden Routing Guards (STRICTLY BLOCKED)

- `UNAUTHORIZED → GIT_WRITE_COMMAND_EXECUTION` (BLOCKED)
- `GIT_APPROVAL → IMPLIED_RELEASE_APPROVAL` (BLOCKED)
- `UNAUTHORIZED → RELEASE_OR_DEPLOY_EXECUTION` (BLOCKED)
