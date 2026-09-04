---
name: blueprint-to-implementation
command: implement
aliases:
  - code
  - build
  - execution
category: workflow
tags:
  - implementation
  - execution
  - single-writer
  - ledger
  - governance
version: 3.3.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-29
role: implementation_execution_orchestrator
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
input_contract: frozen_blueprint_and_implementation_approval
output_contract: implementation_completion_and_debug_handoff
allowed_input_blueprint_statuses:
  - FROZEN
implementation_approval_required: true
orchestrator_write_access: false
default_collaboration_mode: MODE_B_MULTI_AGENT_SINGLE_WRITER
test_execution_authorized: false
git_write_authorized: false
release_authorized: false
feature_execution_authorized: false
default_next_route: implementation-to-debug
description: Governs the implementation execution lifecycle from a frozen blueprint and valid Implementation Approval. Manages task graph loading, single-writer file governance, pre-write base-hash verification, change ledger recording, static verification, failure/recovery handling, and handoff to debug.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
required_phase_artifacts:
  - implementation-report.md
  - phase-handoff.json
  - changed-files.md
  - change-ledger.json
  - static-validation.md
required_feature_completion_artifacts:
  - feature-implementation-completion.md
  - feature-implementation-completion.json
  - consolidated-change-ledger.json
  - debug-handoff.json
artifact_persistence_gate_required: true
source_write_guard_required: true
no_blueprint_no_code: true
transactional_doc_source_sync_required: true
documentation_sync_gate_required: true
code_block_gate_required: true
implementation_entry_receipt_required: true
---

## Frontend Completion Guard

When `.agents/project-profile.json` reports `visual_debug.e2e_required=true` or
`visual_e2e.required=true`, implementation completion MUST automatically invoke
the structured `visual e2e` runner. The implementation handoff is blocked with
`FRONTEND_E2E_REQUIRED` until the final manifest passes the real-browser
Mobile -> Desktop -> Tablet matrix with zero unresolved findings. A prose claim,
static screenshot, mock adapter, or user-run command is not completion evidence.

> [!CRITICAL]
> **Cross-Skill Strict Policy & Physical Write Invariant**:
> **STRICT ENGINEERING POLICY IS AUTHORITATIVE.**
> The skill MUST load the Core Engineering Policy (`.agents/policies/strict-engineering.md`), Physical Repository Write Policy (`.agents/policies/physical-repository-write.md`), all active Language Profiles (`.agents/profiles/*.yaml`), and the Project Architecture Contract (`.agents/contracts/engineering-quality-gates.yaml`) before mutating source code.
> A skill MUST NOT weaken, bypass, suppress, reinterpret, or locally override a blocking gate.
> Implementation MUST execute physical repository file writes (`disk = truth`), perform mandatory `WRITE -> READ BACK -> COMPARE INTENT -> WORKING TREE VERIFICATION`, enforce pre-write 500-line limit checks plus family-folder split shape, Fail-Fast dependencies, and produce zero validator bypasses (`no any`, `# type: ignore`, `@ts-ignore`, `_ = err`).

## Mandatory Family-Folder Split Shape

When splitting a file to keep each physical file <=500 lines, implementation MUST:
- Create one shared family-name directory for the extracted files under the existing owner boundary.
- Keep one facade/barrel/aggregate entry file as the only external import/use surface for that family.
- Update external imports to the aggregate entry point, not to internal split files.
- Name split files by responsibility, not mechanical sequence labels.
- Treat flat scatter-splitting into the parent folder as a policy violation that must be corrected before verification.
> If compliance requires an architecture change outside the skill's current approved authority, the skill MUST raise architecture/blueprint drift and route through AIWF change control.

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

# Skill: blueprint-to-implementation (Blueprint to Implementation Authority)

## 1. Overview & Source-Write Guard
Skill `blueprint-to-implementation` quản lý việc thực thi mã nguồn từ Technical Design Blueprint được phê duyệt.

> [!CRITICAL]
> **SOURCE_WRITE_GUARD & Transactional Changeset Rules**:
> 1. `NO REQUIRED DOCUMENT = NO CODE` & `NO BLUEPRINT = NO CODE`: Coder & Main Writer BẮT BUỘC phải xác minh `implementation-entry-receipt.json`, canonical `code-block-gate.json` (`decision: PASS`, `authority: strict-code-block-gate`, `blueprint_full_sha256` khớp Blueprint hiện tại, không có per-block `FAIL`/`BLOCKED`), và `documentation-impact-analysis.json` trước khi sửa bất kỳ file mã nguồn kinh doanh nào.
> 2. Mọi thay đổi mã nguồn BẮT BUỘC phải thuộc về một `SOURCE_DOCUMENT_CHANGESET` giao dịch duy nhất, cập nhật đồng thời các tài liệu bị ảnh hưởng.
> 3. Coi là chưa hoàn tất (`SOURCE_COMPLETED_DOCUMENTATION_PENDING`) nếu mã nguồn đã sửa nhưng chưa cập nhật tài liệu và `DOCUMENTATION_SYNC_GATE` chưa đạt `PASS`.

> [!CRITICAL]
> **Mandatory Implementation Artifact Persistence Contract**:
> Sau mỗi phase triển khai mã nguồn, Coder & Main Writer BẮT BUỘC phải tạo và persist đủ 5 tệp chứng minh tại `docs/aiwf-runs/<workflow-id>/implementation/<phase-id>/`:
> 1. `implementation-report.md`
> 2. `phase-handoff.json`
> 3. `changed-files.md`
> 4. `change-ledger.json`
> 5. `static-validation.md`
>
> Và khi kết thúc phase triển khai cuối cùng, BẮT BUỘC phải tạo đủ 4 tệp chứng minh hoàn tất feature tại `docs/aiwf-runs/<workflow-id>/implementation/`:
> 1. `feature-implementation-completion.md`
> 2. `feature-implementation-completion.json`
> 3. `consolidated-change-ledger.json`
> 4. `debug-handoff.json`
>
> CẤM chuyển sang trạng thái `READY_FOR_DEBUG` nếu thiếu bất kỳ tệp tài liệu nào trên.

## 0. Contract & Governance Boundaries

- **Role**: `implementation_execution_orchestrator`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Implementation Entry Gate PASS)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Frozen Blueprint & Valid Implementation Approval` (`schemas/implementation-entry-handoff.schema.json` v1.0.0)
- **Output Contracts**:
  - `Implementation Completion Record` (`schemas/implementation-completion.schema.json` v1.0.0)
  - `Debug Handoff Artifact` (`schemas/debug-handoff.schema.json` v1.0.0)
- **Allowed Input Blueprint Statuses**: `FROZEN`
- **Implementation Approval Required**: `true` (`APPROVED` or `APPROVED_WITH_CONDITIONS`)
- **Main Orchestrator Write Access**: `false` (STRICTLY FORBIDDEN to modify source code directly)
- **Default Collaboration Mode**: `MODE_B_MULTI_AGENT_SINGLE_WRITER` (`Main Writer` is exclusive source writer)
- **Test Execution Authorized**: `false` (Tests default to `NOT_RUN`; `TESTER` Agent is exclusive owner when approved)
- **Git Write Authorized**: `false` (STRICTLY FORBIDDEN)
- **Release Authorized**: `false` (STRICTLY FORBIDDEN)
- **Feature Execution Authorized**: `false` (Phase 10 designs Skill contract ONLY; NO user feature implementation)
- **Default Next Route**: `implementation-to-debug` (ONLY AFTER Independent Implementation Review PASS)

---

## 1. Purpose & Core Principles

The `blueprint-to-implementation` skill manages the controlled execution of tasks defined in a frozen Technical Blueprint.

### Core Principles
1. **Requires Frozen Blueprint & Valid Implementation Approval**: Execution CANNOT commence without a `FROZEN` blueprint and active Implementation Approval record.
2. **Orchestrator ≠ Writer**: The `Main Orchestrator` loads task graphs, monitors state, and enforces gates. It MUST NOT write source code directly.
3. **Single Writer Governance**: Under `MODE_B_MULTI_AGENT_SINGLE_WRITER`, all file edits ARE EXCLUSIVELY EXECUTED by the assigned `Main Writer`. Mode C is blocked (`MODE_C_NOT_ELIGIBLE`) unless explicit OCC runtime prerequisites exist.
4. **Pre-Write Base-Hash Verification**: Every write operation validates that the target file's current SHA-256 matches the authorized base hash. Stale base hashes trigger `STALE_BASE` write blocks.
5. **Append-Only Change Ledger**: All modifications ARE RECORDED in an immutable change ledger (`schemas/change-ledger.schema.json`).

---

## 2. Input Contract & Prerequisites Validation

Validates the implementation entry handoff containing:
- `blueprint_id`, `blueprint_version`, `blueprint_full_hash` (Status: `FROZEN`)
- `implementation_approval_id`, `approval_type: IMPLEMENTATION_APPROVAL`
- Upstream identities (`requirement_spec_id`, `brainstorming_id`, `roadmap_id`, `plan_id` and all full SHA-256 hashes)
- `allowed_files`, `protected_files`, `writer_owner`, `collaboration_mode`, `verification_matrix`, `rollback_design`

Missing any mandatory input triggers `IMPLEMENTATION_ENTRY = BLOCKED`.

---

## 3. Execution Lifecycle & State Machine

```text
NOT_STARTED → ENTRY_VALIDATING → AUTHORIZED → SESSION_INITIALIZING → TASKS_LOADING → READY → EXECUTING → IMPLEMENTATION_REVIEW → COMPLETED
```
*Secondary States*: `PAUSED`, `BLOCKED`, `RECOVERING`, `ROLLING_BACK`, `COMPLETED_WITH_FINDINGS`, `FAILED`, `CANCELLED`, `INVALIDATED`, `SUPERSEDED`.

Forbidden State Transitions: `NOT_STARTED → EXECUTING`, `ENTRY_VALIDATING → EXECUTING`, `EXECUTING → TESTED/COMMITTED/RELEASED`.

---

## 4. Task Graph & Dependency Execution Model

- **Task Properties**: `task_id`, `blueprint_step_id`, `plan_task_id`, `title`, `objective`, `owner_role`, `assigned_agent`, `writer_owner`, `allowed_files`, `protected_files`, `base_hashes`, `status`, `evidence`.
- **Dependency Enforcement**: Tasks transition to `READY` ONLY when all hard dependencies ARE COMPLETED. Unintentional dependency cycles trigger `BLOCKED` status.

---

## 5. Roles & Single Writer Governance

- `Main Orchestrator`: Route, delegate, monitor dependencies, validate gates. Write access: `FORBIDDEN`.
- `Main Writer`: Exclusive writer role for source modifications under Mode B.
- `Specialist Agents`: Read-only analysis and review.
- `TESTER Agent`: Exclusive owner of test execution. In Phase 10, tests remain **`NOT_RUN`**.
- `Tool Executor`: Sole boundary for OS subprocess spawning.

---

## 6. Allowed, Protected & Mirror File Controls

- **Allowed Files**: List of explicitly authorized paths. Edits outside this list trigger `WRITE_BLOCKED`.
- **Protected Files**: High-sensitivity files. Edits trigger `WRITE_FORBIDDEN`.
- **Mirror Files**: `.agents/skills/**`. Direct edits ARE STRICTLY FORBIDDEN (`MIRROR_DIRECT_EDIT_FORBIDDEN`).

---

## 7. Pre-Write Validation & Base-Hash Guard

Before any file write operation:
1. Verifies `path in allowed_files` and `path not in protected_files`.
2. Verifies `writer_agent == assigned_writer_owner`.
3. Computes current full SHA-256 hash of file.
4. Compares current hash with `authorized_base_hash`.
5. If mismatch detected: Issues `STALE_BASE` decision, halts write, records conflict evidence, and routes back to Orchestrator.

---

## 8. Controlled Write & Append-Only Change Ledger

- Every modification generates an append-only change ledger record (`schemas/change-ledger.schema.json`) containing `change_id`, `execution_id`, `task_id`, `writer`, `file`, `change_type`, `original_hash`, `new_hash`, `diff_summary`, and `timestamp`.
- Modification history IS IMMUTABLE; corrections require superseding records.

---

## 9. Controlled Tool Executor Boundary

- OS subprocess creation IS EXCLUSIVELY MANAGED by `Tool Executor`.
- Side-effect classification: `READ_ONLY` (Allowed), `LOCAL_WRITE` (Allowed for allowed files), `BUILD` (Static build check only), `TEST` (Blocked), `GIT_WRITE` (Blocked), `RELEASE` (Blocked).

---

## 10. Task Evidence, Static Verification & Live Checklist Ticking

- **Task Evidence**: Tasks CANNOT be marked `IMPLEMENTED` based solely on agent claims. Requires file diff evidence, new SHA-256 hash, and static verification results.
- **Static Verification**: Validates Markdown/YAML/JSON syntax, schema conformance, and contract references. Does NOT run test suites.
- **Live Checklist Ticking** (applies to both Quick-Feature, Quick-Fix, and any Blueprint containing a `## Implementation Checklist` or `## 6. Implementation Checklist` section):

  > [!IMPORTANT]
  > **Checklist items MUST be ticked one-by-one as each file write completes.**
  > For every task/item in the Blueprint checklist:
  > ```
  > a. Read the checklist item.
  > b. Execute the code write for THAT item only.
  > c. Immediately update the Blueprint file: change `- [ ]` → `- [x]` via multi_replace_file_content.
  > d. Proceed to the next item.
  > ```
  > Batching all writes then ticking all checkboxes at the end is **FORBIDDEN**.
  > The checklist is a live progress tracker and audit trail, not a post-implementation summary.
  > If a write is blocked (file not found, hash mismatch, scope violation), mark it `- [!]` (blocked)
  > with an inline blocker note and continue remaining items. Do NOT skip silently.


---

## 11. Deviations & Scope Change Controls

- **Blueprint Deviation**: Requires formal `deviation-request.md`. Unapproved deviations trigger `BLUEPRINT_DEVIATION` failure.
- **Scope Change Request**: Requires formal `scope-change-request.md`. File additions outside allowed scope trigger `OUT_OF_SCOPE_WRITE_BLOCKED`.

---

## 12. Failure Taxonomy, Recovery & Rollback

- **Failure Categories**: 18 standard failure types (`ENTRY_VALIDATION_FAILURE`, `DEPENDENCY_FAILURE`, `OWNERSHIP_CONFLICT`, `STALE_BASE`, `OUT_OF_SCOPE_WRITE`, `PROTECTED_FILE_WRITE`, `MIRROR_DIRECT_EDIT`, `TOOL_EXECUTION_FAILURE`, etc.).
- **Recovery Contract**: Preserves evidence, cleans up partial outputs, and resumes from valid checkpoints idempotently.
- **Rollback Contract**: Restores original SHA-256 base hashes if task fails during high-risk edits.

---

## 13. Independent Implementation Review & Completion Record

- After all tasks complete, invokes Independent Reviewer Agent (`templates/implementation-review.md`).
- Generates `implementation-completion.schema.json` recording total/completed tasks, files changed, change ledger hash, and `test_status: NOT_RUN`.

---

## 14. Handoff Contract to Debug

Creates `debug-handoff.schema.json` containing `execution_id`, `completion_record_id`, `blueprint_identity`, `files_changed`, `change_records`, `static_verification`, `test_status: NOT_RUN`, and known findings. Does NOT declare "Tests Passed" or "Ready for Release".

---

## 15. Quick Flows & Specialized Paths

- **Quick Feature**: Enforces lightweight execution contract using `lightweight-blueprint-template.md` and single-writer controls.
- **Quick Fix**: Enforces patch execution contract using `patch-blueprint-template.md`, root-cause evidence, and regression boundary.
- **Documentation-Only & Analysis-Only**: Uses read-only execution tasks with zero code execution (`NO_SOURCE_WRITE`).

---

## 16. Change Control & Auto-Invalidation

If upstream Blueprint, Freeze, or Implementation Approval hashes drift:
- The execution session IS IMMEDIATELY `INVALIDATED`.
- Active writes ARE `HALTED`.
- Downstream Debug handoffs become `STALE`.

---

## 17. Forbidden Routing Guards (STRICTLY BLOCKED)

- `NOT_STARTED / ENTRY_VALIDATING → EXECUTING` (BLOCKED)
- `EXECUTING → TESTED / COMMITTED / RELEASED` (BLOCKED)
- `ORCHESTRATOR → DIRECT_SOURCE_WRITE` (BLOCKED)
- `NON_WRITER_AGENT → EXCLUSIVE_SOURCE_WRITE` (BLOCKED)
- `EXECUTION → GIT_WRITE / RELEASE_EXECUTION` (BLOCKED)
