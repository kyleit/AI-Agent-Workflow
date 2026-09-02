---
name: aiwf
description: "User-facing entry wrapper for the AI Engineering Workflow Framework (AIWF). Use when the user types aiwf or @aiwf <command> (next, continue, status, tick, coordinator, doctor, state, memory, search, release). Delegates through initialize-workflow to workflow-coordinator; never executes work itself."
command: aiwf
aliases:
  - workflow
  - aiwf-wrapper
category: wrapper
tags:
  - wrapper
  - entrypoint-alias
  - bootstrap-delegator
  - user-entry
version: 3.16.2
license: MIT
repository: https://github.com/kyleit/AI-Agent-Workflow.git
created_at: 2026-07-29
updated_at: 2026-07-29
canonical_entrypoint: false
canonical_target: workflow-coordinator
bootstrap_required: true
bootstrap_skill: initialize-workflow
bootstrap_receipt_required: true
fail_closed_without_bootstrap: true
command_receipt_required: true
command_receipt_owner: workflow-command-audit
command_receipt_path_pattern: .agents/state/audit/commands/YYYY/MM/DD/<command-id>.json
latest_pointer: .agents/state/audit/latest-command.json
artifact_persistence_gate_required: true
artifact_root_pattern: docs/aiwf-runs/<workflow-id>
artifact_index_required: true
no_blueprint_no_code: true
documentation_first: true
transactional_doc_source_sync_required: true
documentation_sync_gate_required: true
min_blueprint_readiness_score: 95
code_block_gate_required: true
source_write_guard_required: true
path_sanitization_policy: REPOSITORY_RELATIVE
repository_root_representation: "."
allow_absolute_paths: false
direct_coordinator_route: forbidden
specialist_routing_before_bootstrap: forbidden
delegation_only: true
user_invokable: true
role: AIWF_USER_ENTRY_WRAPPER
---

## Canonical Public Source Preservation

The canonical public source repository is intentionally:
`https://github.com/kyleit/AI-Agent-Workflow.git`.

AI agents MUST NOT replace this URL with a placeholder, redact it, delete it,
drop it from generated contracts, or silently substitute another repository.
It is an intentional public source configuration and does not violate the
project's privacy or path rules.

> [!CRITICAL]
> ## ⛔ MANDATORY ENFORCEMENT GUARDS — READ BEFORE ANY ACTION
>
> **YOU MUST COMPLY WITH ALL 6 GUARDS BELOW. VIOLATION = IMMEDIATE STOP.**
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
>
> 6. **NATIVE PROMPT GATES ONLY**: Blueprint, implementation, release, git, and deployment approvals MUST be requested through native Agent/IDE `ask_question` first; `aiwf prompt select --options "Continue|Cancel"` is only a fallback bridge. Native `ask_question` MUST be invoked as a structured tool-call object, never as hand-written raw JSON or manually escaped Unicode. If `ask_question` fails with `InputValidationError`, invalid JSON, truncated payload, unescaped backslash/control character, or malformed `\uXXXX`, retry via `aiwf prompt select`. If `aiwf prompt select` returns `PROMPT_UNAVAILABLE`, no user choice happened; use native `ask_question` if available or stop and report structured prompting unavailable. Chat tokens such as `APPROVE ...`, `Y`, `Continue`, or "ok" MUST NOT be requested as the primary approval path. Chat approval is valid only when the Agent explicitly reports that native ask_question and prompt select bridge rendering are unavailable.

> **AGENT RESPONSE BRIDGE**: When the host cannot pipe a native response to stdin, the Agent may supply the selected option through the prompt handler's structured `--response` input or the one-shot `AIWF_PROMPT_RESPONSE` value. IDE integrations may consume `.agents/runtime/prompt-request.json` and write a matching `choice_id` response to `.agents/runtime/prompt-response.json`. The bridge is single-use and exact-option validated. If no response arrives, the CLI emits a machine-readable `status: awaiting_input` envelope and keeps the pending request; its non-zero pending status is intentional, never `Cancel`, and never authorizes a gate. Manual terminal prompting is opt-in via `AIWF_TEXT_PROMPT=1`.

# Skill: aiwf (AIWF User Entry Wrapper)

## 1. Overview
Skill `aiwf` đóng vai trò là Wrapper Skill đại diện ngắn gọn cho người dùng khi gọi luồng làm việc AI Engineering Workflow Framework (AIWF).

Cú pháp sử dụng:
```text
@aiwf <command | raw_request> [arguments]
```
hoặc (nếu môi trường host/platform hỗ trợ ánh xạ lệnh):
```text
/aiwf <command | raw_request> [arguments]
```

Trong môi trường AGY/agent headless, người dùng có thể nhập prompt tự nhiên không có `/aiwf`.
Runtime command bus và agent prompt service BẮT BUỘC tự normalize prompt đó thành:

```text
/aiwf <raw_request>
```

Agent không được coi prompt thiếu `/aiwf` là lý do để bypass workflow, bỏ qua memory, hoặc implement trực tiếp.

> [!CRITICAL]
> **Mandatory Transactional Documentation-Source Sync Contract**:
> 1. `NO REQUIRED DOCUMENT = NO CODE` & `NO BLUEPRINT = NO CODE`.
> 2. `NO DOCUMENT UPDATE = NO SOURCE CHANGE COMPLETION`: Thay đổi mã nguồn và tài liệu liên quan BẮT BUỘC nằm trong cùng giao dịch `SOURCE_DOCUMENT_CHANGESET`.
> 3. Phải thông qua **`DOCUMENTATION_SYNC_GATE`** (`all_required_documents_exist`, `zero_stale_documents`, `zero_missing_documents`, `all_sha256_verify`) trước khi phát hành phase completion hoặc phản hồi chat.

> [!WARNING]
> **IDE Implementation Mode is STRICTLY FORBIDDEN**:
> AI agents MUST NOT use IDE "Implement" mode, IDE "Apply" button, IDE proposed changes,
> IDE virtual patches, or any mechanism that does not result in physical file writes to the
> project working tree. Implementation is ONLY valid when files are physically created/modified
> on disk via file creation/edit tools.
> Ref: Physical Repository Write Policy (AI_RULES.md Section 33)

---

## 2. Mandatory Delegation & Pre-Implementation Flow
```text
aiwf / /aiwf
→ initialize-workflow (Bootstrap & Root Resolution)
→ valid bootstrap receipt (SHA-256 Verified)
→ workflow-coordinator (Canonical Entrypoint & Fail-Closed Guard)
→ 00-intake (Raw Intent & Normalization)
→ 01-requirements (Specification & Acceptance Criteria)
→ 02-brainstorming (Brainstorming & Feasibility)
→ 03-plan (Execution Plan & Task Breakdown)
→ 04-technical (Technical Architecture Documents)
→ 05-blueprint (Blueprint Generation & Validation)
→ CODE_BLOCK_GATE (canonical strict-code-block-gate PASS, strict language profiles, Blueprint hash locked)
→ Blueprint Approval via native Agent/IDE ask_question first; aiwf prompt select fallback bridge only
→ Blueprint Freeze
→ Implementation Approval via native Agent/IDE ask_question first; aiwf prompt select fallback bridge only
→ Implementation Entry Receipt (06-implementation/implementation-entry-receipt.json)
→ SOURCE_WRITE_GUARD (Authorizes Main Writer)
→ blueprint-to-implementation (Code Execution)
→ ARTIFACT_PERSISTENCE_GATE (Validate required artifact set & atomic persist)
→ update artifact-index.json
→ workflow-command-audit (Validate & Atomic Persist Command Receipt)
→ return user-facing response
```

---

## 3. Command Envelope & Supported Commands

Hỗ trợ đầy đủ 10 lệnh đại diện:
`help`, `status`, `next`, `continue`, `resume`, `debug`, `verify`, `cancel`, `recover`, `new-request`.

---

## 4. Default Governance Safety Flags
- `test_execution_authorized`: `false` (Đòi hỏi `TEST_EXECUTION_APPROVAL` riêng)
- `git_write_authorized`: `false` (Đòi hỏi `GIT_APPROVAL` riêng)
- `release_authorized`: `false` (Đòi hỏi `RELEASE_APPROVAL` riêng)
- `deploy_authorized`: `false` (Đòi hỏi `DEPLOYMENT_APPROVAL` riêng)
- `production_migration_authorized`: `false`
- `default_collaboration_mode`: `MODE_B_MULTI_AGENT_SINGLE_WRITER`
- `state_authority`: `.agents/state` (`.agents/.session.json` is DEPRECATED)
- `physical_write_enforcement`: `true` (Ref: AI_RULES.md Section 33 — Physical Repository Write Policy)

---

## 5. Observable Command Output Format

Mọi lệnh trả về kết quả kèm thông số chứng minh Command Receipt & Path Sanitization:

```text
AIWF Command: <command_name>
Command ID: <command_id>
Initialize workflow invoked: True
Workflow ID: <workflow_id>
Previous phase: <previous_phase>
Current phase: <current_phase>
Command result: <COMPLETED/NO_CHANGE/BLOCKED/...>
State changed: <true/false>
Source changed: <true/false>
Files changed:
  - <repository-relative paths only>
Pending approval: <none/approval_type>
Blocking findings:
  - <finding_or_none>
Recommended next command: <recommended_command>
Command receipt: .agents/state/audit/commands/YYYY/MM/DD/<command-id>.json
Receipt persisted: True
Receipt SHA-256: <full_sha256>
Path sanitization: PASS
Absolute paths remaining: 0
```
