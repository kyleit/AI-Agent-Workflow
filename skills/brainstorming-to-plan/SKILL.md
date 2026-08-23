---
name: brainstorming-to-plan
command: plan
aliases:
  - planning
  - roadmap-plan
category: workflow
tags:
  - planning
  - roadmap
  - execution-plan
  - governance
version: 3.3.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-29
role: roadmap_and_plan_orchestrator
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
input_contract: feasibility_approved_brainstorming
output_contract: roadmap_and_plan_artifacts
allowed_input_brainstorming_statuses:
  - FEASIBILITY_APPROVED
  - FEASIBILITY_APPROVED_WITH_CONDITIONS
readiness_gate: PLAN_READINESS
readiness_threshold: 95
plan_architecture_review_type: PLAN_ARCHITECTURE
approval_authority: none
default_collaboration_mode: MODE_B_MULTI_AGENT_SINGLE_WRITER
default_next_route: blueprint
description: Constructs delivery roadmaps (milestone-level) and execution plans (task-level) from feasibility-approved brainstorming artifacts, assigns agent roles, enforces safe-write strategies, evaluates Plan Readiness (95/100), requests Plan Architecture Review, and prepares handoff for Technical Blueprint.
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

# Skill: brainstorming-to-plan (Roadmap & Execution Plan Engine)

## 0. Contract & Governance Boundaries

- **Role**: `roadmap_and_plan_orchestrator`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Architecture Feasibility Approval)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Feasibility-Approved Brainstorming` (`schemas/brainstorming-handoff.schema.json` v1.0.0)
- **Output Contracts**:
  - `Roadmap Artifact` (`schemas/roadmap.schema.json` v1.0.0)
  - `Execution Plan Artifact` (`schemas/plan.schema.json` v1.0.0)
- **Allowed Input Brainstorming Statuses**: `FEASIBILITY_APPROVED`, `FEASIBILITY_APPROVED_WITH_CONDITIONS`
- **Readiness Gate**: `PLAN_READINESS` (Evaluated by `readiness-and-approval-gates`, threshold `95/100`)
- **Plan Architecture Review**: `PLAN_ARCHITECTURE` (Reviewed by `architecture-review`)
- **Direct Source Write**: `false` (STRICTLY FORBIDDEN)
- **Direct Implementation Route**: `false` (STRICTLY FORBIDDEN)
- **Direct Test Execution**: `false` (STRICTLY FORBIDDEN)
- **Direct Git Write**: `false` (STRICTLY FORBIDDEN)
- **Direct Release**: `false` (STRICTLY FORBIDDEN)
- **Approval Authority**: `none` (Requests Plan Architecture Review; cannot self-approve)
- **Default Collaboration Mode**: `MODE_B_MULTI_AGENT_SINGLE_WRITER`
- **Default Next Route**: `blueprint` (ONLY AFTER Plan Architecture Approval)

---

## 1. Purpose & Core Principles

The `brainstorming-to-plan` skill converts feasibility-approved brainstorming recommendations into milestone-level **Roadmaps** and task-level **Execution Plans**.

### Core Principles
1. **Requires Feasibility-Approved Input**: Accepts ONLY brainstorming artifacts with status `FEASIBILITY_APPROVED` or `FEASIBILITY_APPROVED_WITH_CONDITIONS` and a verified full SHA-256 hash.
2. **Clear Boundary Separation**:
   - **Roadmap**: Milestone-level delivery phases, outcomes, dependencies, sequencing, exit criteria.
   - **Execution Plan**: Task-level decomposition, ownership assignment, file/module impact, collaboration mode, verification/rollback strategy.
   - **Technical Blueprint**: Full API signatures, data schemas, fine-grained implementation steps (Phase 09).
3. **No Direct Source Modification**: Planning artifacts plan execution; they MUST NOT modify source code or execute tests.
4. **Mandatory Gate & Review**: Execution Plans MUST pass `PLAN_READINESS` (score >= 95/100, zero blockers) and obtain Plan Architecture Approval (`review_type: PLAN_ARCHITECTURE`) before handoff to Technical Blueprint.

---

## 1.1 Canonical Feature Family Layout & Golden Plan Standard

All Roadmap and Plan artifacts MUST be generated directly into the standard Feature Family folders using **Strict Relative Paths**:
- `docs/features/<slug>/roadmaps/<slug>_roadmap.md`
- `docs/features/<slug>/plans/<slug>_plan.md`

### 🌟 Golden Plan Reference
Refer to the canonical execution plan:
- `docs/features/go-build-system/plans/FEAT-500_golang_native_runtime_plan.md`

### 🚫 Strict Anti-Placeholder & Relative Path Mandate
- NEVER use machine absolute paths (`file:///...`, `e:/...`, `C:\...`).
- NEVER use vague task descriptions (`// TODO`, `implement details`, `update code`).
- Tasks must define explicit task IDs (`t-01`, `t-02`), assigned specialist agent, target files, and verification steps.

---

## 2. Input Contract & Prerequisites Validation

Accepts ONLY a feasibility-approved brainstorming handoff containing:
- `brainstorming_id`, `version`, `full_sha256`
- `requirement_spec_id`, `requirement_full_sha256`
- Feasibility approval status: `FEASIBILITY_APPROVED` or `FEASIBILITY_APPROVED_WITH_CONDITIONS`
- Selected option, accepted trade-offs, accepted risks, and architecture constraints.

Unapproved feasibility statuses (`NEEDS_CHANGES`, `REJECTED`, `NEEDS_MORE_INFORMATION`, `BLOCKED`) ARE STRICTLY REJECTED.

---

## 3. Roadmap Construction & Milestone Model

Constructs milestone-level roadmaps specifying:
- **Milestone Properties**: `milestone_id`, `title`, `objective`, `outcome`, `scope`, `entry_conditions`, `exit_criteria`, `dependencies`, `owner_role`.
- **Dependency Types Supported**: `HARD_DEPENDENCY`, `SOFT_DEPENDENCY`, `APPROVAL_DEPENDENCY`, `ARTIFACT_DEPENDENCY`, `EXTERNAL_DEPENDENCY`, `DATA_DEPENDENCY`, `INFRASTRUCTURE_DEPENDENCY`, `MIGRATION_DEPENDENCY`.
- **Cycle Detection**: Detects dependency cycles. Unintentional cycles trigger `BLOCKED` status.

---

## 4. Execution Plan & Task Decomposition

Decomposes selected solution options into structured, non-ambiguous tasks:
- **Task Properties**: `task_id`, `title`, `objective`, `description`, `owner_role`, `assigned_agent`, `scope`, `dependencies`, `expected_files`, `expected_modules`, `verification`, `rollback`.
- Vague tasks ("Implement feature", "Fix bugs", "Update code") ARE STRICTLY FORBIDDEN.

---

## 5. Ownership Model & Collaboration Modes

### Role Assignment Rules
- `Main Orchestrator`: Task delegation & gate monitoring only.
- `Planner`: Creates execution plan; does NOT write source code.
- `Main Writer`: Exclusive writer role for source modifications during implementation.
- `TESTER Agent`: Exclusive owner of test execution. Tests default to `NOT_RUN`.

### Collaboration Modes
- `MODE_A_SINGLE_AGENT`: Isolated small tasks.
- `MODE_B_MULTI_AGENT_SINGLE_WRITER`: **Default Mode**. Multiple specialist agents analyze/review, but only Main Writer executes source edits.
- `MODE_C_SAFE_MULTI_WRITE`: Blocked (`MODE_C_NOT_ELIGIBLE`) unless explicit OCC, file leases, atomic writes, and collision recovery runtime prerequisites exist.

---

## 6. File/Module Impact & Safe-Write Strategy

- Maps expected files/modules affected by task: `CONFIRMED`, `LIKELY`, `POSSIBLE`, `UNKNOWN`.
- `UNKNOWN` on high-risk tasks triggers open decision or discovery task.
- Safe-write strategy requires `single_writer: true` under Mode B.

---

## 7. Verification & Rollback Strategies

- **Verification**: Distinguishes `STATIC_VALIDATION`, `BUILD_VERIFICATION`, `TEST_EXECUTION`, `MANUAL_REVIEW`, `INDEPENDENT_REVIEW`, `ARCHITECTURE_CONFORMANCE`.
- **Test Execution Guard**: Test execution owner is strictly `TESTER` Agent. In the absence of approval, tests are marked **`NOT_RUN`**.
- **Rollback Strategy**: High-risk tasks (migration, data modification, breaking changes) MUST include high-level rollback steps and triggers. Missing rollback triggers a gate blocker.

---

## 8. Plan State Machine Lifecycle

```text
DRAFT → DECOMPOSING → OWNERS_ASSIGNING → DEPENDENCIES_VALIDATING → READY_FOR_REVIEW → REVIEWED → AWAITING_ARCHITECTURE_REVIEW → ARCHITECTURE_APPROVED → Technical Blueprint
```
*Secondary States*: `ARCHITECTURE_APPROVED_WITH_CONDITIONS`, `NEEDS_CHANGES`, `BLOCKED`, `SUPERSEDED`, `CANCELLED`.

---

## 9. Gate Hooks & Plan Architecture Review Integration

1. **Readiness Evaluation**: Calls `skills/readiness-and-approval-gates/SKILL.md` for gate `PLAN_READINESS`.
   - Requires score >= **95/100**.
   - Enforces **Strict Blocking Rule**: Missing owner, missing hard dependency, missing rollback for high-risk task, file ownership conflict, or architecture conflict MUST set gate decision to `BLOCKED`.
2. **Plan Architecture Review Request**: Sends request to `skills/architecture-review/SKILL.md` with `review_type: PLAN_ARCHITECTURE`.
3. **Handoff to Technical Blueprint**: Proceeds ONLY when Plan Architecture Approval status is `APPROVED` or `APPROVED_WITH_CONDITIONS`.

---

## 10. Quick Flow & Specialized Paths

- **Quick Feature**: Combines lightweight Roadmap + Plan using `lightweight-plan-template.md`.
- **Quick Fix**: Generates lightweight patch plan with regression boundary & patch contract handoff.
- **Documentation-Only & Analysis-Only**: Uses read-only planning tasks with zero code execution (`NO_SOURCE_WRITE`).

---

## 11. Change Control & Invalidation

If underlying Requirement Specification or Brainstorming artifacts change (version string or full SHA-256 hash drift):
- Existing Roadmap and Execution Plan artifacts are IMMEDIATELY marked **`INVALIDATED`**.
- Downstream Blueprint handoffs become **`STALE`**.
- Re-evaluation and new Plan Architecture Review ARE REQUIRED.

---

## 12. Forbidden Routing Guards (STRICTLY BLOCKED)

- `DRAFT / DECOMPOSING / READY_FOR_REVIEW → BLUEPRINT / IMPLEMENTATION` (BLOCKED)
- `UNAPPROVED FEASIBILITY BRAINSTORMING → ROADMAP / PLAN` (BLOCKED)
- `UNAPPROVED PLAN → BLUEPRINT / IMPLEMENTATION` (BLOCKED)
- `PLAN → IMPLEMENTATION / TEST / GIT / RELEASE` (BLOCKED)
