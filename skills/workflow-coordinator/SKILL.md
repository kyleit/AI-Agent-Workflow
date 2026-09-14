---
name: workflow-coordinator
description: "The single canonical entry gate of the AIWF framework. Use at the start of every feature, bug fix, or task request to classify intent, verify the Bootstrap Receipt, load workflow state, enforce the documentation sync gate and approval gates, and dispatch to the correct specialist skill (quick-fix, quick-feature, brainstorming, blueprint-to-implementation, debug, verify, git-governance, release-governance). Specialist skills must never be invoked directly from a raw user prompt."
command: tick
aliases:
  - coordinate
  - dispatch
category: workflow
tags:
  - orchestrator
  - workflow
  - runtime
  - stateless
version: 3.16.0
license: MIT
repository: https://gitlab.com/your-org/ai-workflow-skills
created_at: 2026-07-17
updated_at: 2026-07-29
canonical_entrypoint: true
entrypoint_authority: canonical
wrapper_entrypoint: aiwf
role: canonical_workflow_entrypoint
authority: route_and_delegate
bootstrap_receipt_required: true
accepted_bootstrap_skill: initialize-workflow
accepted_wrapper: aiwf
fail_closed_on_missing_receipt: true
raw_intent_delegation: raw-intent-normalization
requirement_delegation: requirement-specification
brainstorming_delegation: brainstorming
plan_delegation: brainstorming-to-plan
blueprint_delegation: plan-to-blueprint
implementation_delegation: blueprint-to-implementation
debug_delegation: implementation-to-debug
verification_delegation: debug-to-verify
test_governance_delegation: test-execution-governance
git_governance_delegation: git-governance
release_governance_delegation: release-governance
canonical_entrypoint: true
canonical_entrypoint_count: 1
bootstrap_receipt_required: true
accepted_bootstrap_skill: initialize-workflow
artifact_persistence_gate_required: true
artifact_root_pattern: docs/aiwf-runs/<workflow-id>
no_blueprint_no_code: true
documentation_first: true
transactional_doc_source_sync_required: true
documentation_sync_gate_required: true
min_blueprint_readiness_score: 95
code_block_gate_required: true
source_write_guard_required: true
fail_closed_without_bootstrap: true
fail_closed_without_artifact_persistence: true
fail_closed_without_blueprint: true
fail_closed_without_code_block_gate: true
fail_closed_on_stale_documents: true
fail_closed_without_doc_sync_gate: true
autonomous_greenfield_routing: true
recursive_artifact_set_required: true
dynamic_family_feature_phase_count: true
prompt_instruction_dependency: false
---

## Approval Emission Firewall

For reasoning-heavy workflow artifacts, the coordinator MUST verify that the
Agent authored document content through native file operations. Commands such
as Python/PowerShell/Node one-liners, shell heredocs, `echo >`, `Set-Content`,
or `Out-File` MUST NOT generate or rewrite Markdown, JSON evidence, Blueprint,
specification, roadmap, plan, question, or report content. Deterministic
scripts may only inspect, parse, hash, validate, run gates, or create empty
directories. A script-authored artifact is invalid and the workflow remains
`BLOCKED` until the Agent rewrites it with native file tools.

The coordinator MUST suppress every Blueprint approval prompt until the
documentation transaction has completed and both independent machine gates
have passed on the current artifact hash. “Complete” means the upstream
inventory is reconciled into the dynamically derived
`Master -> Family -> Small Feature -> Phase` artifact set, all concrete file
rows have adjacent full-file blocks, and the runtime Blueprint validator has
returned exactly `APPROVAL_READY` with score `100` and no findings. The strict
recursive code-block gate must then return `PASS` with no blocking per-block
finding and its retained JSON must be read back.

An approval question shown before that point is a workflow violation, even if
it is labeled “Technical Design Blueprint” or the document is long. It must
not be used to ask the owner to review a draft, to resolve validator output,
or to advance a stalled repair loop. On any missing, stale, unreadable, or
failed result, remain `BLOCKED` and continue Agent-led documentation repair;
never ask for approval and never permit implementation.

The coordinator must materialize Integration-Verify for every work item with
multiple phases and Interop-Handoff whenever a second dependent product or
repository exists. It must block Release Preparation until the applicable
artifact contains the business-language E2E scenario, container-built
environment, contract proof, reverse documentation update, release order, and
wrong-order failure behavior.

## Physical Documentation Transaction Boundary

For greenfield and large cross-layer requests, the coordinator owns a
documentation transaction before implementation. That transaction may write
AIWF state and `docs/` artifacts only until the complete upstream chain and
recursive Blueprint artifact set pass validation. Product source, generated
assets, dependency manifests, databases, binaries, and product build/test
execution are implementation activities outside this transaction.

Every implementation report, IDE plan, walkthrough, or approval claim is
untrusted until its referenced file exists under the current workspace and
its runtime receipt is bound to the current work item and artifact hash.
Permission bypass flags never change this rule. Missing or external
authorization is a hard stop.

The host's generic planner output is not an AIWF artifact. If the Agent is
running in a plan-oriented host mode and receives only an external brain file,
it MUST materialize the corresponding repository-relative intent/spec/plan
artifacts and continue the coordinator route. A response containing only an
external plan link is `BLOCKED: ARTIFACT_PERSISTENCE_REQUIRED`.

The coordinator MUST enforce the owner-question boundary before every
transition. A pending blocking question may have a persisted draft intent or
clarifying specification, but it MUST NOT produce an approved requirement,
feasibility-approved brainstorming, approved roadmap/plan, Blueprint approval
request, or implementation handoff. "Recommended", "adopted", "selected", or
"reviewed" written by the Agent is not an owner response. Only a response to
the exact current question, with its receipt/provenance persisted in the same
workspace, can unlock the next transition.

Once the owner answers the active blocking question, the coordinator MUST
resume and drive the same workflow through Requirement Specification,
Architecture/Brainstorming, Roadmap, Execution Plan, and `plan-to-blueprint`
without stopping at an intermediate document. It may stop only for another
blocking owner question, an exact validator blocker, or an independently
validated Blueprint Approval request. A final response that says a stage is
complete while `workflow.json` still points to that stage and the next required
artifact is absent is invalid; reconcile the state and continue first.

# Skill: workflow-coordinator (AIWF Canonical Workflow Coordinator)

## 2. Autonomous Greenfield Routing Algorithm

The coordinator owns classification and decomposition. It MUST derive workflow
structure from the raw request and repository evidence; it MUST NOT wait for a
user-supplied recipe or depend on phrases that restate framework rules.

For a request that initializes a new or empty project, the coordinator MUST:

1. Mark the normalized intent `project_initialization: true` and retain every
   stack, platform, UI-control, asset, runtime, persistence, and verification
   constraint as a traceable requirement.
2. Route through the full requirements, architecture, plan, and
   `plan-to-blueprint` chain. `quick-feature` and `quick-fix` are forbidden
   when the request creates a cross-layer project baseline.
3. Derive delivery families from real architecture boundaries (for example
   `backend`, `frontend`, `wails`) and create a named small-feature directory
   whenever a family remains large after boundary grouping. Never invent a
   fixed number of families or phases.
4. Derive local `P01`, `P02`, ... sequences inside each family/small-feature
   delivery unit. Block IDs remain globally unique across the artifact set.
5. Require one master Blueprint plus every discovered phase Blueprint before
   approval review. The recursive artifact-set validator, strict code-block
   gate, coverage validator, initialization validator, and semantic document
   validator are mandatory reviewers.
6. Reconcile the Master against every linked Roadmap Phase Inventory and
   Implementation Plan File Impact Map. Emit an `Upstream Delivery Unit
   Coverage Matrix`; every upstream phase must point to a distinct discovered
   phase artifact, and every concrete planned file must appear in the Master
   and its owning phase with a real implementation-ready block.
7. Automatically loop repair on exact validator findings. The coordinator may
   present approval only when all validators pass, the complete file matrix is
   mapped to implementation-ready full-file blocks, and the master data-flow
   and sequence diagrams remain intact. Any missing or thin phase is `BLOCKED`.
   A legacy/free-form blueprint, a blueprint without valid YAML frontmatter,
   or an agent-authored readiness checklist without retained validator JSON is
   never approval-ready. The coordinator MUST discard the claimed PASS, run
   the canonical validator/strict gate, and repair the artifact set until the
   runtime result is independently available.
   Requirement Specification scope is the minimum immutable contract during
   repair. Rewriting a Plan or Roadmap to hide an omitted screen, route,
   schema object, API capability, or test does not reduce the required scope;
   the coordinator MUST validate those items directly from the linked
   Requirement Specification.

   Approval review has two independent machine stages. The strict recursive
   code-block gate checks materialized full-file blocks; the canonical runtime
   Blueprint validation loop checks document shape, upstream coverage,
   greenfield initialization obligations, surface matrices, phase contracts,
   and preserved diagrams. Both stages MUST pass before an approval prompt is
   presented. A gate-only PASS, a missing runtime result, or
   `test_status: NOT_RUN` is never approval-ready.

   The coordinator MUST also enforce the authoring transaction, not merely
   inspect a final summary: read the complete upstream phase/file inventory;
   materialize every derived family and phase under `Master -> Family -> Small
   Feature -> Phase`; require literal canonical template headings and `File` /
   `Code Block IDs` matrix columns; reconcile one complete adjacent full-file
   block to every concrete file row; then run the runtime validator and strict
   recursive gate again after every repair. For a greenfield cross-layer
   request, a master-only document or a few representative blocks is always
   `BLOCKED`, regardless of its length or self-reported score. The owner
   approval question MUST NOT be emitted until the validator returns exactly
   `status=APPROVAL_READY`, `score=100`, and no findings. Never edit a local
   quality-gate configuration merely to manufacture PASS.

This contract is behavioral and deterministic. A detailed prompt can add
requirements, but it cannot be required to activate this routing or to make a
Blueprint complete.

All user-facing workspace-document links MUST use project-relative Markdown
paths. Never emit `file:///`, drive-letter paths, or other absolute local-file
URIs in coordinator output; absolute paths are for internal tool calls only.

## Progressive Refinement Invariant

For every raw feature request, the coordinator MUST preserve a monotonic
capability ledger across `raw-intent-normalization`,
`requirement-specification`, `brainstorming`, `brainstorming-to-plan`, and
`plan-to-blueprint`. The next artifact must cite the previous artifact and
carry forward every discovered item. An agent may split or refine a delivery
unit, but may not delete an upstream route, screen, schema object, endpoint,
actor, acceptance criterion, or test obligation to make a later gate pass.
Missing/stale upstream artifacts, failed transition validation, or a reduced
capability ledger is `BLOCKED` and triggers repair at the earliest failing
transition.

## AI-First Decision Boundary

The coordinator assigns reasoning to the Agent and enforcement to the runtime.
The Agent must inspect the raw request and current evidence, build the
ambiguity and decision ledger, explain options and trade-offs, and ask the
owner for every blocking decision before Specification freeze. Runtime code
may validate provenance, ledger completeness, state transitions, and artifact
scope, but must not invent or approve a product or architecture decision. A
missing Agent ledger is `CLARIFYING`/`BLOCKED`, never an invitation for a
script to guess.

### Clarification Transaction Integrity

The coordinator MUST treat each owner clarification as an ordered transaction:
active question -> presented options -> owner response -> captured decision.
An ordinal or short response is valid only for the active question that is
still pending. Before a phase transition, the Agent MUST compare the captured
decision with the exact selected option and stop on any semantic mismatch,
missing receipt, stale question, or cross-question reuse. The coordinator and
runtime MUST never reinterpret, normalize, or silently replace the owner's
selected policy with a recommendation or a model-generated default.

## 1. Overview & Role
Skill `workflow-coordinator` là Cổng Điều hướng Chính thức (`CANONICAL_ENTRYPOINT`) duy nhất của AIWF framework (`canonical_entrypoint_count = 1`).

> [!CRITICAL]
> **Mandatory Transactional Synchronization & Sync Gate Rules**:
> 1. `NO REQUIRED DOCUMENT = NO CODE` & `NO BLUEPRINT = NO CODE`: Coordinator BẮT BUỘC từ chối điều hướng tới `blueprint-to-implementation` hoặc bất kỳ hành động sửa mã nguồn nào nếu chưa có bộ tài liệu tiền triển khai hoàn chỉnh.
> 2. `DOCUMENTATION_SYNC_GATE` BẮT BUỘC phải đạt `PASS` (`all_required_documents_exist`, `zero_stale_documents`, `zero_missing_documents`, `all_sha256_verify`).
> 3. Nếu bất kỳ tài liệu nào bị `STALE` hoặc `MISSING`, coordinator BẮT BUỘC chặn lệnh `@aiwf next`, `@aiwf continue`, và từ chối phát hành `FEATURE_IMPLEMENTATION_COMPLETED` hay `READY_FOR_DEBUG`.
> 4. CẤM suy luận phê duyệt từ yêu cầu chat của người dùng. Phải có tệp `blueprint-approval-request.json` và `implementation-approval-request.json` hợp lệ.
> 2. Nếu Bootstrap Receipt không hợp lệ (`BOOTSTRAP_RECEIPT_INVALID`), sai lệch project (`BOOTSTRAP_CONTEXT_MISMATCH`), hoặc mã băm SHA-256 không khớp (`HASH_MISMATCH`): Coordinator lập tức từ chối điều hướng và trả về thông báo lỗi rào cản khởi tạo.
> 3. Cấm điều hướng trực tiếp sang Specialist Skills (`quick-fix`, `quick-feature`, `implementation`, `debug`, `verify`, `git-governance`, `release-governance`) nếu chưa qua `initialize-workflow`.

---

## 3. Receipt Verification Checklist
Trước khi nhận lệnh và điều hướng:
- [ ] Receipt tồn tại và đúng định dạng schema `bootstrap-receipt.schema.json`.
- [ ] `bootstrap_skill` = `initialize-workflow`.
- [ ] `decision` = `BOOTSTRAP_READY` hoặc `BOOTSTRAP_READY_READ_ONLY`.
- [ ] `repository_root` trùng khớp với kết quả `git rev-parse --show-top-level`.
- [ ] `project_id` trùng khớp với project active trong `.agents/state`.
- [ ] `content_hash` khớp 100% mã băm SHA-256.
- [ ] Không có `blocking_findings`.
