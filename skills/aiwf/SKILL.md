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
autonomous_project_initialization_routing: true
recursive_blueprint_decomposition_required: true
prompt_must_not_supply_workflow_instructions: true
---

## Hard Approval Sequencing Rule

For a greenfield or large cross-layer request, the Agent MUST NOT emit, call,
or simulate a Blueprint approval question while authoring is incomplete. The
only valid order is:

1. Persist the complete upstream chain and the recursively derived
   `Master -> Family -> Small Feature -> Phase` artifact set.
2. Run the canonical runtime Blueprint validator against the current master
   and work item, then repair every finding until it returns exactly
   `status=APPROVAL_READY`, `score=100`, and an empty findings list.
3. Run the canonical recursive `strict-code-block-gate` against the same
   immutable artifact set and retain its JSON result with the current master
   hash. It MUST return `decision=PASS` with no blocking per-block result.
4. Re-read both retained JSON results and only then use the host's native
   `ask_question` for the owner approval.

The native approval question is forbidden as a progress checkpoint, as a
request to review an unvalidated draft, or as a substitute for a failed gate.
If either validator cannot run, returns `BLOCKED`, has no retained evidence,
or the artifact hash changes, the workflow remains `BLOCKED` and the Agent
continues the documentation repair loop without asking for approval. A
self-authored `PASS`, a detailed master, or a technical-design approval prompt
never satisfies this rule.

## Documentation-First Execution Firewall

For a new project or a large feature, the first Agent transaction is
documentation-only. It may inspect the workspace and write AIWF state plus
workflow artifacts under `docs/`, but MUST NOT create, modify, delete,
compile, install dependencies for, run, or package product source before the
Blueprint Approval Gate has produced a current work-item-bound approval and
the implementation-entry gate has passed.

Permission bypass flags, full-access mode, plan mode, a previous conversation,
an IDE plan, an old authorization file, or the Agent's own approval claim are
not workflow approval. Before any product-source write, the Agent MUST obtain
current runtime authorization and verify that the Blueprint is repo-relative,
inside the current workspace, hash-current, and bound to the active work item.
If any check is unavailable, the action is `NO-GO`.

During this first transaction, implementation detail belongs in the Blueprint
artifact set as complete full-file blocks and executable task contracts.
Product builds, dependency installation, generated binaries, runtime
databases, and product E2E MUST wait until the approved Blueprint is consumed
by `blueprint-to-implementation`.

The Agent MUST NOT create a scratch helper script for any reasoning-heavy
authoring or repair. This includes scripts named `update_*`, `fix_*`,
`rewrite_*`, `sync_*`, or `generate_*` and includes scripts that appear to
"just" patch one line, normalize Markdown, or fill code blocks. The Agent must
use native file tools on the document itself. Any workspace-writing scratch
script is an immediate `BLOCKED` authoring-policy violation; do not run it,
do not delete the evidence, and do not claim that a later gate repairs it.
After every Agent authoring turn and before every approval attempt, the
authoring-policy audit MUST be run. A failed audit ends the current turn and
requires native re-authoring of the affected artifact.

An IDE brain file, chat report, screenshot, mock result, dry run, or
self-authored walkthrough never substitutes for artifacts under
`docs/features/<family>/`. The Agent may report completion only after the
artifact chain is present on disk and independently validated.

After a valid owner response resolves a blocking clarification, the Agent MUST
continue the same workflow transaction through every remaining pre-implementation
stage until one of these terminal states is reached: a new blocking owner
question, an independently validated Blueprint Approval request, or an exact
runtime blocker. It MUST NOT stop after writing a specification, brainstorming
note, roadmap, or plan and claim the workflow is complete. The workflow state,
suggested next skill, and final message MUST agree with the artifacts on disk;
if they do not, the Agent MUST reconcile state and resume the next stage before
returning control.

The host's generic `plan` mode is not an AIWF workflow stage and does not
authorize an external plan-only response. When that mode produces an IDE brain
file or asks for approval outside the workspace, the Agent MUST continue the
AIWF route, persist the equivalent repository artifacts, and remain blocked if
it cannot do so. The final response MUST point to repository-relative files,
never only to `file:///...` brain artifacts.

All user-facing workspace-document links MUST use project-relative Markdown
paths. Never emit `file:///`, drive-letter paths, or other absolute local-file
URIs in Agent output; absolute paths are for internal tool calls only.

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
> 6. **NATIVE PROMPT GATES FIRST**: Blueprint, implementation, release, git, and deployment approvals MUST be requested through native Agent/IDE `ask_question` first; `aiwf prompt select --options "Continue|Cancel"` is the fallback bridge. Native `ask_question` MUST be invoked as a structured tool-call object, never as hand-written raw JSON or manually escaped Unicode. If `ask_question` fails with `InputValidationError`, invalid JSON, truncated payload, unescaped backslash/control character, or malformed `\uXXXX`, retry via `aiwf prompt select`. If both structured paths are unavailable, the runtime MUST return `PROMPT_UNAVAILABLE` and the Agent MUST state that fact. A clear approval in the next user turn (including `approve`, `approved`, `yes`, `continue`, or `ok`) MAY then be accepted only when an exact pending request is still present, its gate and work-item/Blueprint match the active workflow, and the Agent immediately persists the approval through the canonical AIWF command and verifies its receipt. This is a fallback, never the primary approval path; no approval text may unlock a gate without that pending-request and artifact-binding check.

> **AGENT RESPONSE BRIDGE**: When the host cannot pipe a native response to stdin, the Agent may supply the selected option through the prompt handler's structured `--response` input or the one-shot `AIWF_PROMPT_RESPONSE` value. IDE integrations may consume `.agents/runtime/prompt-request.json` through their native bridge. The bridge is single-use and exact-option validated. If no response arrives, the CLI emits `status: PROMPT_UNAVAILABLE` with the active gate binding and stops; it never emits an invisible `awaiting_input` instruction, never chooses `Cancel`, and never authorizes a gate. The Agent may perform one bound chat fallback after validating the pending request. Manual terminal prompting is opt-in via `AIWF_TEXT_PROMPT=1`.

> **CHAT FALLBACK BINDING**: A chat fallback is valid only after the runtime has produced `PROMPT_UNAVAILABLE` (or the host has explicitly reported both structured prompt paths unavailable). The Agent MUST read `.agents/runtime/prompt-request.json`, require `status: pending`, exact `choice_id`, approval gate, and active work-item/Blueprint match, then run the gate-specific canonical command. For Blueprint approval this is `aiwf blueprint --path <pending Blueprint path> --approve`; the Agent MUST verify the resulting scoped approval artifact and command receipt before continuing. If any binding check is missing or mismatched, keep the gate stopped and explain the exact missing artifact.

# Skill: aiwf (AIWF User Entry Wrapper)

## 0. Autonomous Large-Request Contract

### Greenfield Authoring Firewall

Reasoning-heavy artifact content MUST be authored through the Agent's native
file creation/edit capability. Shell, PowerShell, Python, JavaScript, Node,
or ad-hoc one-liners MUST NOT write, append, replace, template, or generate
content in `docs/**`, Blueprint files, specifications, roadmaps, plans,
questions, reports, or retained evidence. They may create empty directories,
read files, calculate hashes, parse structured data, run validators, and
collect evidence after the Agent has authored the content. A script-generated
Markdown artifact is invalid even when its text looks complete.

For a greenfield cross-layer request, the Agent MUST treat Blueprint authoring
as a complete delivery design, not a summary of a few example files. Before
creating any Blueprint file, it MUST build a coverage ledger from the complete
Requirement, Roadmap, and Plan. The ledger has one row for every requested
capability, runtime boundary, concrete file, screen or route, API operation,
persistence object or migration, asset, control, state, test, and integration
point. A technology name in prose is not a ledger row.

When the corresponding boundary is in scope, the ledger normally covers:
backend manifest and lock, entrypoint, config, domain types, database and
migrations, repositories, application services, workers or probers, DTOs,
Fiber routes and middleware, error handling, shutdown, and tests; frontend
package lock, `index.html`, compiler/bundler/Tailwind/PostCSS configuration,
local font manifest or files, entrypoint, hash router, API client,
layout/navigation, every route screen and loading/empty/error state, every
requested custom control, custom dialog host, and UI/E2E tests; and Wails
manifest, build/embed entrypoint, lifecycle, IPC bindings, tray integration,
shutdown/recovery, and desktop tests. The Agent may add surfaces but MUST NOT
omit one without an explicit approved scope decision.

Every ledger row MUST map to exactly one owning family, small feature when the
family remains large, phase, file-matrix row, full-file block, test, and
evidence path. The Agent MUST reconcile this mapping in both directions before
review. A single direct phase containing a short representative list is not a
valid decomposition for a cross-layer greenfield request.

The Agent MUST never edit, rewrite, relax, delete, or regenerate any project
`.agents/contracts/**`, `.agents/policies/**`, `.agents/profiles/**`, gate
script, or gate configuration while repairing a Blueprint. If a validator
reports a missing or malformed framework contract, the Agent MUST leave it
untouched, record `BLOCKED`, and route the issue to the framework maintainer.
A validation repair may edit only the Blueprint artifact set and retained
evidence.

For each `code_block_too_thin` or incomplete-block finding, the Agent MUST
rewrite the entire affected block from metadata through closing fence. It MUST
preserve or increase the projected physical line count and include complete
imports, types, exported API, validation, error paths, cancellation/lifecycle
behavior, integration calls, and required states for that file. Lowering a
`Lines` value, splitting prose around a snippet, or calling a minimal demo
copy-ready is a hard failure.

The Agent MUST write readiness evidence last. Any self-authored PASS,
approval question, or `awaiting_owner_approval` status before both canonical
machine results are read back is invalid and MUST be removed during repair.

The runtime authoring-policy audit is also mandatory. Before approval, it scans
the active Agent scratch provenance for scripts that target the workspace and
perform document writes, rewrites, renames, or deletes. Any finding such as
`script_authored_document_detected:*` is a hard BLOCKED result, regardless of
document length, structural score, or the Agent's reported PASS. Do not delete
or hide scratch evidence to make this audit pass; repair by re-authoring the
affected artifacts with native Agent file tools.

The raw user request is the product brief, not a workflow script. The Agent
MUST read the downstream Skills and apply their contracts without requiring the
user to add control phrases such as `NO CODE - NO BLUEPRINT`, `BLUEPRINT NO GO`,
or a manually prescribed phase count. Those phrases are safeguards expressed
by the framework itself, not input requirements.

When the raw request contains any combination of a new project, initialization,
greenfield, from-scratch, scaffold, or empty repository intent and names two or
more technical boundaries, `aiwf` MUST preserve and forward
`project_initialization: true` plus the complete constraint inventory. It MUST
route through `initialize-workflow`, `workflow-coordinator`, requirements,
architecture, plan, and `plan-to-blueprint`; it MUST NOT route to a lightweight
feature/fix path merely because no source files exist.

For that class of request, downstream generation MUST autonomously produce and
validate the recursive artifact shape `Master -> Family -> Small Feature ->
Phase`, using only the families and small features derived from the actual
scope. The user is never required to specify the hierarchy, phase count, code
block wording, or validation commands. A response is approval-ready only after
the runtime has recursively validated every artifact, file row, full-file code
 block, coverage row, bootstrap obligation, and preserved data-flow diagram.
Free-form legacy Markdown that omits the canonical YAML frontmatter, phase
artifacts, implementation-ready block inventory, or required surface matrices
is invalid even when it looks detailed. The Agent MUST use the canonical
`plan-to-blueprint` template/contract and MUST NOT report PASS from its own
checklist. If the canonical validator or strict gate was not actually run and
its retained JSON evidence was not read back, the only legal result is
`BLOCKED`, followed by an autonomous repair loop.
When upstream Roadmap or Plan artifacts exist, their phase inventory and file
impact map are binding scope. AIWF MUST generate an Upstream Delivery Unit
Coverage Matrix, materialize every upstream phase as a distinct discovered
phase artifact, and materialize every concrete planned implementation path in
the Master plus its owning phase. Local block PASS cannot hide an upstream
omission; the repair loop remains active until this reconciliation passes.

The wrapper MUST also treat Blueprint frontmatter as untrusted agent output:
`status: APPROVED` or `status: FROZEN` cannot unlock implementation. Only a
scoped runtime approval record for the exact work item and Blueprint path,
followed by implementation-entry validation, can authorize source writes.

### Progressive Refinement Contract

AIWF MUST refine a raw request through the complete chain
`Raw Intent -> Normalized Intent -> Requirement Specification -> Architecture /
Brainstorming -> Roadmap -> Execution Plan -> Blueprint Artifact Set`. A later
artifact may add decisions and implementation detail, but may not replace,
shrink, or silently reinterpret upstream capabilities, constraints, actors,
use cases, routes, data objects, acceptance criteria, or verification needs.
Each transition MUST persist traceability and run its matching validator before
the next transition. Jumping directly from raw intent to a free-form Blueprint
is invalid; if a required intermediate artifact is absent or stale, the
workflow remains `BLOCKED` and repairs that artifact first.

For a product-only prompt, workflow instructions are internal Skill behavior.
The Agent MUST not ask the user to restate phase names, file matrices, code-block
rules, or validation commands. User interaction is reserved for product
decisions that genuinely change scope or acceptance behavior.

### AI-First Clarification Contract

The Agent performs the reasoning: it discovers ambiguity, compares options,
explains impact, and asks the owner one blocking question at a time. Runtime
scripts only enforce evidence and phase boundaries. They MUST NOT silently
choose scope, architecture, API, schema, UX, runtime, security, or failure
handling. If the Agent does not provide a valid decision ledger, the workflow
stops in `CLARIFYING`/`BLOCKED` with a generic request for Agent analysis; no
Specification or Blueprint may claim readiness.

### Reasoning Must Stay With The Agent

The Agent must author all reasoning-heavy artifacts and implementation
contracts: decisions, requirements, architecture, coverage, file matrices,
diagrams, task decomposition, interfaces, and complete copy-ready code blocks.
It must use native read/edit capabilities for that work. Python, PowerShell,
JavaScript, or other scripts may only perform deterministic inspection,
hashing, parsing, linting, validation, gate execution, and evidence collection;
they must not generate or rewrite Blueprint prose or product code. A generated
artifact is not valid merely because it contains many lines or claims `PASS`.

Every owner clarification is bound to the active question and its exact option
text. The Agent must preserve the question, options, answer, and provenance,
then perform a semantic consistency check before recording the decision. Short
answers such as `Option 1` are resolved only against the current question; a
mismatch keeps the workflow in `CLARIFYING` and triggers a re-question. No
skill or runtime script may invent a response receipt or translate a selected
option into a different policy.

For a greenfield or large feature, AIWF must produce a complete artifact set:
master blueprint -> domain family -> small feature (when still large) -> phase.
The number of phases is decided by dependency and execution cohesion, not a
fixed count or a mechanical line limit. The master must reconcile every
upstream capability and every phase must carry its own executable task contract
and complete file blocks. A master-only blueprint or a blueprint that merely
declares `PASS` remains `BLOCKED` until the independently discovered artifact
set passes validation.

Before Requirement Approval on a greenfield application, the Agent must audit
and resolve the complete decision surface: actors/scope, screens/routes,
entities/schema, API/events, runtime behavior, failure/retry, security,
persistence/retention, and real acceptance evidence. Any dimension not explicit
in the prompt or backed by approved inspectable evidence stays `BLOCKING`; the
Agent asks one question at a time. A later Brainstorming or Blueprint artifact
cannot be used to hide an unanswered requirement decision.

## 1. Overview
Skill `aiwf` đóng vai trò là Wrapper Skill đại diện ngắn gọn cho người dùng khi gọi luồng làm việc AI Engineering Workflow Framework (AIWF).

### Canonical gate invocation

When inspecting the source-write gate from any target project, agents MUST use
`aiwf gate status`. Never construct `python tools/aiwf-hooks/aiwf_gate.py ...`
from the target project: bridge-mode projects may not contain a copied
`tools/` tree, and the relative path therefore points at the wrong repository.
If the installed command is unavailable, use the bridge fallback
`python .agents/aiwf-hooks/aiwf_gate.py status`. The direct
`python tools/aiwf-hooks/aiwf_gate.py ...` form is valid only when the current
working directory is the AIWF framework source repository itself.

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
