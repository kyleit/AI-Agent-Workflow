---
name: readiness-and-approval-gates
command: evaluate-gate
aliases:
  - readiness-gate
  - approval-gate
  - gate-governance
category: quality
tags:
  - readiness
  - approval
  - gates
  - governance
version: 1.0.0
license: MIT
created_at: 2026-07-29
updated_at: 2026-07-29
role: readiness_and_approval_governance
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
canonical_entrypoint_authority: false
direct_source_write: false
direct_test_execution: false
direct_git_write: false
direct_release: false
approval_authority: none
waiver_authority: none
default_readiness_threshold: 95
hash_algorithm: SHA-256
description: Evaluates readiness scores (95/100 threshold), enforces strict blocking rules, validates explicit SHA-256 approval records, detects gate bypasses, and logs audit events.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
code_block_gate_required: true
min_readiness_score: 95
fail_closed: true
---

# Skill: readiness-and-approval-gates (AIWF Readiness and Approval Gates)

## 1. Overview & CODE_BLOCK_GATE Rule
Skill `readiness-and-approval-gates` chịu trách nhiệm thẩm định mức độ sẵn sàng (Readiness Assessment) và quản lý các cổng phê duyệt chính thức.

> [!CRITICAL]
> **CODE_BLOCK_GATE & Source-Write Authorization Rules (The 5 Golden Pillars)**:
> 1. **`CODE_BLOCK_GATE`** chỉ được cấp `PASS` bởi `skills/strict-code-block-gate/SKILL.md` khi:
>    - `readiness_score >= 95/100` đánh giá qua 4 chiều trọng số (25đ/chiều):
>      - **Chiều 1 (25đ)**: Kiến trúc DDD 4 Lớp & Phân lập Domain độc lập (SOLID, zero external framework import in domain).
>      - **Chiều 2 (25đ)**: Hợp đồng Giao diện & Typed DTO Schemas chi tiết từng trường.
>      - **Chiều 3 (25đ)**: An ninh NIST/OWASP, Băm Mật khẩu & Token Protection (PBKDF2/JWT).
>      - **Chiều 4 (25đ)**: Ma trận Kiểm thử Tự động (Unit + E2E Acceptance Mapping).
>    - Không có blocker mức Critical hoặc High.
>    - Tuân thủ **Policy 11 (Absolute Path Prohibition)**: 100% đường dẫn là Strict Relative Paths (`docs/features/...`), zero `file:///` machine links.
>    - Có Bảng File-by-File Change Matrix chi tiết với chữ ký hàm, imports/exports và line budget < 500 dòng.
>    - Độc lập thẩm định (`reviewed_by = "Independent Auditor"`).
>    - `code-block-gate.json` có `decision: PASS`, `blueprint_full_sha256` khớp Blueprint hiện tại, không có `FAIL`/`BLOCKED` per-block, và mọi implementation-ready block đều có strict language profile.
> 2. Phân định rõ ràng: `BLUEPRINT_APPROVAL` không tự động là `IMPLEMENTATION_APPROVAL`.
> 3. CẤM cấp `source_write_allowed: true` khi thiếu `code-block-gate.json` hoặc `implementation-entry-receipt.json`.
> 4. **STRICT ENGINEERING & PHYSICAL WRITE POLICY INVARIANT**: Gate evaluation MUST verify compliance with Core Engineering Policy (`.agents/policies/strict-engineering.md`), Physical Repository Write Policy (`.agents/policies/physical-repository-write.md`), active Language Profiles (`.agents/profiles/*.yaml`), and Project Architecture Contract (`.agents/contracts/engineering-quality-gates.yaml`). Any file size >500 lines, unverified physical write, or validator bypass invalidates gate approval.

## 0. Contract & Governance Boundaries

- **Role**: `readiness_and_approval_governance`
- **Activation Mode**: `delegated` (Evaluated by `workflow-coordinator` or phase skills)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Default Readiness Threshold**: `95/100`
- **Hash Algorithm**: `SHA-256`
- **Direct Source Write**: `false` (STRICTLY FORBIDDEN)
- **Direct Test Execution**: `false` (STRICTLY FORBIDDEN)
- **Direct Git Write**: `false` (STRICTLY FORBIDDEN)
- **Direct Release**: `false` (STRICTLY FORBIDDEN)
- **Approval Authority**: `none` (Evaluates gates; cannot issue self-approvals)
- **Waiver Authority**: `none` (Evaluates waivers against policy; cannot grant waivers)

---

## 1. Purpose & Core Principles

The `readiness-and-approval-gates` skill enforces deterministic, multi-dimensional quality gates and explicit approval governance across all SDLC phases.

### Core Principles
1. **Default Threshold (95/100)**: Scored gates require an overall score of at least 95/100 to pass.
2. **Strict Blocking Rule**: A weighted score of 95/100 or 100/100 **MUST NOT** override an unfulfilled blocking condition. If any blocking condition exists, the gate decision MUST be `FAIL`, `BLOCKED`, `AWAITING_APPROVAL`, or `INVALIDATED`.
3. **Artifact Readiness ≠ Approval**: Artifact readiness score assesses quality; transition authorization requires explicit approval from authorized roles.
4. **Approval Separation**: Each approval type is strictly independent. Blueprint Approval DOES NOT grant Implementation Approval; Git Commit DOES NOT grant Release Approval.
5. **No Self-Approval**: Gate evaluators, orchestrators, and artifact authors MUST NOT approve their own work when independent review/approval is required.

---

## 2. 25+ Blocking Conditions Taxonomy Supported

1. `MISSING_REQUIRED_ARTIFACT`
2. `MISSING_REQUIRED_SECTION`
3. `BLOCKING_OPEN_QUESTION`
4. `UNRESOLVED_CONFLICT`
5. `UNVERIFIABLE_ACCEPTANCE_CRITERIA`
6. `UNAPPROVED_ASSUMPTION`
7. `SECURITY_AMBIGUITY`
8. `PRIVACY_AMBIGUITY`
9. `DESTRUCTIVE_ACTION_UNCONFIRMED`
10. `BREAKING_CHANGE_UNCONFIRMED`
11. `APPROVAL_MISSING`
12. `APPROVAL_INVALID`
13. `HASH_DRIFT`
14. `VERSION_DRIFT`
15. `BASELINE_DRIFT`
16. `STATE_TRANSITION_INVALID`
17. `OWNER_UNCLEAR`
18. `TEST_PERMISSION_MISSING`
19. `GIT_PERMISSION_MISSING`
20. `RELEASE_PERMISSION_MISSING`
21. `SCOPE_UNCLEAR`
22. `TRACEABILITY_BROKEN`
23. `DEPENDENCY_UNKNOWN`
24. `ROLLBACK_MISSING`
25. `MIGRATION_UNSAFE`

---

## 3. 8 Independent Approval Types Supported

1. `REQUIREMENT_APPROVAL` (Owner approval of requirement spec before Brainstorming)
2. `FEASIBILITY_APPROVAL` (Architect approval of feasibility review)
3. `PLAN_APPROVAL` (Planner/Architect approval of execution plan)
4. `BLUEPRINT_APPROVAL` (Owner approval of zero-placeholder frozen blueprint)
5. `IMPLEMENTATION_APPROVAL` (Owner authorization before code modification)
6. `TEST_EXECUTION_APPROVAL` (Explicit authorization to run test suite; exclusive owner = `TESTER`)
7. `GIT_APPROVAL` (Explicit authorization for git actions: stage/commit/push/PR/merge/tag)
8. `RELEASE_APPROVAL` (Explicit authorization for package publish/release)

---

## 4. Full SHA-256 Approval Identity Binding

All approval records MUST be bound to:
- Specific Artifact Path & Artifact ID
- Version String
- **Full SHA-256 Hash** (`full_artifact_hash`)
- Authorized Approver & Authority Role
- Timestamp & Baseline Commit

Short hashes or conversational phrases (`"OK"`, `"Tiếp tục"`, `"Looks good"`) ARE INVALID and MUST NOT unlock gates.

---

## 5. Test Execution Gate Rules

- **Exclusive Owner**: `TESTER` Agent is the sole role authorized to execute tests.
- **Explicit Authorization Required**: Tests execute ONLY when `TEST_EXECUTION_APPROVAL` exists specifying scope, command, and `TESTER` owner.
- **Default State**: In the absence of approval, test execution status is strictly **`NOT_RUN`**.
- `NOT_RUN` MUST NOT be treated as PASS or FAIL.

---

## 6. Git & Release Permission Separation

Git permissions are granularly separated: `READ` ≠ `STAGE` ≠ `COMMIT` ≠ `PUSH` ≠ `CREATE_PR` ≠ `MERGE` ≠ `TAG`.
- `COMMIT` permission DOES NOT grant `PUSH` or `RELEASE`.
- Release Approval requires separate explicit authorization with full artifact identity, build verification, and rollback readiness.

---

## 7. Approval Invalidation, Revocation & Expiry

An existing approval record becomes **`INVALIDATED`** when:
- Artifact content or full SHA-256 hash changes.
- Version or scope changes.
- A new blocking finding or Requirement Change Request (RCR) is approved.
- Approval reaches its expiration timestamp (`EXPIRED`) or is revoked (`REVOKED`).

Old approvals MUST NOT be silently reused after invalidation.

---

## 8. Gate Bypass Detection & Audit Logging

The engine detects bypass attempts such as:
- State transitions without approval records.
- Approval hash mismatches.
- Unauthorized approvers.
- Direct edits to runtime mirrors (`.agents/skills/`).

Critical bypass attempts generate an append-only audit event (`audit-event.schema.json`) and transition the workflow state to **`BLOCKED`**.

---

## 9. Gate State Machine Lifecycle

```text
NOT_EVALUATED → EVALUATING → READY_FOR_REVIEW → AWAITING_APPROVAL → APPROVED → PASS
                                                                    ↓
                                                        FAIL / BLOCKED / INVALIDATED
```
