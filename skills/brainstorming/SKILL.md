---
name: brainstorming
command: brainstorm
aliases:
  - idea
  - discover
category: workflow
tags:
  - requirements
  - discovery
  - brainstorming
  - options
  - feasibility
version: 3.2.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-29
role: solution_brainstorming
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
input_contract: approved_requirement_specification
output_contract: brainstorming_artifact
allowed_input_requirement_statuses:
  - APPROVED
  - APPROVED_WITH_CONDITIONS
readiness_gate: BRAINSTORMING_READINESS
readiness_threshold: 95
feasibility_review_type: FEASIBILITY
approval_authority: none
default_next_route: roadmap_or_plan
description: Explores, frames, and compares technical solution options from an approved Requirement Specification, evaluates trade-offs and risks, requests Architecture Feasibility Review, and prepares handoff for Plan/Roadmap.
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

# Skill: brainstorming (Solution Brainstorming & Option Analysis Engine)

## 0. Contract & Governance Boundaries

- **Role**: `solution_brainstorming`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Requirement Specification Approval)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Approved Requirement Specification` (`schemas/requirement-specification.schema.json` v1.0.0)
- **Output Contract**: `Brainstorming Artifact` (`schemas/brainstorming.schema.json` v1.0.0)
- **Allowed Input Requirement Statuses**: `APPROVED`, `APPROVED_WITH_CONDITIONS`
- **Readiness Gate**: `BRAINSTORMING_READINESS` (Evaluated by `readiness-and-approval-gates`, threshold `95/100`)
- **Feasibility Review**: `FEASIBILITY` (Reviewed by `architecture-review`)
- **Direct Source Write**: `false` (STRICTLY FORBIDDEN)
- **Direct Implementation Route**: `false` (STRICTLY FORBIDDEN)
- **Direct Test Execution**: `false` (STRICTLY FORBIDDEN)
- **Direct Git Write**: `false` (STRICTLY FORBIDDEN)
- **Direct Release**: `false` (STRICTLY FORBIDDEN)
- **Approval Authority**: `none` (Requests Feasibility Review; cannot self-approve)
- **Default Next Route**: `roadmap_or_plan` (ONLY AFTER Feasibility Approval)

---

## 1. Purpose & Core Principles

The `brainstorming` skill explores, frames, and compares candidate technical approaches to fulfill an **Approved Requirement Specification**.

### Core Principles
1. **Requires Approved Requirement Input**: Brainstorming ONLY accepts requirement specifications with status `APPROVED` or `APPROVED_WITH_CONDITIONS` and a verified full SHA-256 hash.
2. **Explores WHAT Options, Not Code Implementation**: Brainstorming evaluates high-level architectural approaches, trade-offs, and risks. It DOES NOT write source code or define fine-grained function signatures.
3. **Brainstorming CANNOT Modify Requirements**: Goals, Non-Goals, Scope, or Acceptance Criteria MUST NOT be altered during Brainstorming. If a requirement change is needed, a formal Requirement Change Request (RCR) MUST be filed.
4. **Mandatory Feasibility Review Integration**: Every recommended option MUST pass `BRAINSTORMING_READINESS` (score >= 95/100, zero blockers) and obtain Architecture Feasibility Approval (`review_type: FEASIBILITY`) before handoff to Plan/Roadmap.

---

## 2. Input Contract & Handoff Validation

Brainstorming accepts ONLY an approved requirement specification containing:
- `requirement_spec_id`, `version`, `full_sha256`
- Approval status: `APPROVED` or `APPROVED_WITH_CONDITIONS` (with conditions tracked)
- Goals, Non-Goals, Actors, Use Cases, Functional Requirements, NFRs, Constraints, Acceptance Criteria, Assumptions, and Traceability.

Unapproved requirement statuses (`DRAFT`, `CLARIFYING`, `READY_FOR_REVIEW`, `AWAITING_OWNER_APPROVAL`, `REJECTED`, `BLOCKED`) ARE STRICTLY REJECTED.

---

## 3. Problem Framing & Constraint Extraction

Preserves approved requirement semantics while creating a technical decision frame:
- Differentiates `CONFIRMED_REQUIREMENT`, `HARD_CONSTRAINT`, `ASSUMPTION`, `DISCOVERY_FACT`, and `OPEN_DECISION`.
- Identifies in-scope vs out-of-scope boundaries without expanding scope.

---

## 4. 16 Decision Drivers Supported

`FUNCTIONAL_FIT`, `SECURITY`, `PRIVACY`, `COMPATIBILITY`, `PERFORMANCE`, `RELIABILITY`, `OPERABILITY`, `MAINTAINABILITY`, `COMPLEXITY`, `MIGRATION_RISK`, `DELIVERY_RISK`, `RESOURCE_USAGE`, `USER_EXPERIENCE`, `PORTABILITY`, `OBSERVABILITY`, `REVERSIBILITY`.

---

## 5. Option Generation & Trade-Off Matrix

- Generates candidate solution options (`Option A`, `Option B`, etc.) evaluating coverage against decision drivers.
- If only one viable option exists, explicit rationale MUST be documented.
- **Trade-off Ratings**: `STRONG`, `ACCEPTABLE`, `WEAK`, `UNACCEPTABLE`, `UNKNOWN`.
- Options violating hard constraints ARE MARKED `NOT_FEASIBLE`.

---

## 6. Risk Analysis & Evidence-Based Recommendation

- Evaluates risks across categories: `SCOPE`, `SECURITY`, `PRIVACY`, `DATA`, `COMPATIBILITY`, `PERFORMANCE`, `RELIABILITY`, `OPERATIONS`, `MIGRATION`, `CONCURRENCY`, `DEPENDENCY`, `DELIVERY`, `MAINTAINABILITY`, `USER_EXPERIENCE`.
- Recommends the optimal solution supported by empirical evidence and key trade-offs. Retains rejected options in history with clear rejection reasons.

---

## 7. Open Decisions & Architecture Questions

- **Open Decisions for Owner**: Formulates clear, non-technical decision options for the Repository Owner when business trade-offs require input.
- **Architecture Questions for Architect**: Formulates specific questions across `BOUNDARY`, `INTERFACE`, `DATA_FLOW`, `PERSISTENCE`, `SECURITY`, `PERFORMANCE`, `MIGRATION` for Feasibility Review.

---

## 8. Brainstorming State Machine Lifecycle

```text
DRAFT → ANALYZING → OPTIONS_GENERATED → COMPARING → RECOMMENDATION_READY → READY_FOR_REVIEW → REVIEWED → AWAITING_FEASIBILITY_REVIEW → FEASIBILITY_APPROVED → Roadmap / Plan
```
*Secondary States*: `FEASIBILITY_APPROVED_WITH_CONDITIONS`, `NEEDS_CHANGES`, `BLOCKED`, `SUPERSEDED`, `CANCELLED`.

---

## 9. Gate Hooks & Feasibility Review Integration

1. **Readiness Evaluation**: Calls `skills/readiness-and-approval-gates/SKILL.md` for gate `BRAINSTORMING_READINESS`.
   - Requires score >= **95/100**.
   - Enforces **Strict Blocking Rule**: Missing approved requirement, requirement hash mismatch, mandatory constraint violation, or open blocking decisions MUST set gate decision to `BLOCKED`.
2. **Feasibility Review Request**: Sends request (`templates/feasibility-review-request.md`) to `skills/architecture-review/SKILL.md` with `review_type: FEASIBILITY`.
3. **Handoff to Roadmap/Plan**: Proceeds ONLY when Feasibility Approval status is `APPROVED` or `APPROVED_WITH_CONDITIONS`.

---

## 10. Quick Flow & Specialized Paths

- **Quick Feature**: Uses `lightweight-brainstorming-template.md` (lightweight option analysis; requires readiness and feasibility review if architectural impact exists).
- **Quick Fix**: Performs Patch Option Analysis & Regression Risk assessment before Patch Contract.
- **Documentation-Only & Analysis-Only**: Uses lightweight analysis without source code modification (`NO_SOURCE_WRITE`).

---

## 11. Requirement Change Control & Invalidation

If the underlying Requirement Specification changes (new version or full SHA-256 hash change):
- The Brainstorming artifact is IMMEDIATELY marked **`INVALIDATED`**.
- Downstream planning artifacts become **`STALE`**.
- Re-evaluation and new Feasibility Review ARE REQUIRED.

---

## 12. Forbidden Routing Guards (STRICTLY BLOCKED)

- `DRAFT / ANALYZING / OPTIONS_GENERATED / RECOMMENDATION_READY → PLAN / BLUEPRINT / IMPLEMENTATION` (BLOCKED)
- `UNAPPROVED REQUIREMENT → BRAINSTORMING` (BLOCKED)
- `BRAINSTORMING WITHOUT FEASIBILITY APPROVAL → PLAN / ROADMAP` (BLOCKED)
