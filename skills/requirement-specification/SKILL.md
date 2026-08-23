---
name: requirement-specification
command: specify-requirements
aliases:
  - req-spec
  - requirement
category: workflow
tags:
  - requirement
  - specification
  - contract
  - governance
version: 1.0.0
license: MIT
created_at: 2026-07-29
updated_at: 2026-07-29
role: requirement_specification
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
canonical_entrypoint_authority: false
input_contract: normalized_intent
output_contract: requirement_specification
direct_brainstorming_route_without_approval: false
direct_implementation_route: false
direct_test_execution: false
direct_git_write: false
direct_release: false
approval_authority: none
requirement_contract_version: 1.0.0
requirement_schema_version: 1.0.0
description: Transforms Normalized Intent into a formal Requirement Specification contract before Brainstorming, Roadmap, Plan, Blueprint, and Implementation.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

# Skill: requirement-specification (Requirement Specification Contract Engine)

## 0. Contract & Governance Boundaries

- **Role**: `requirement_specification`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Raw Intent Normalization)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Normalized Intent` (`skills/raw-intent-normalization/schemas/raw-intent.schema.json` v1.0.0)
- **Output Contract**: `Requirement Specification` (`schemas/requirement-specification.schema.json` v1.0.0)
- **Direct Brainstorming Route without Approval**: `false` (STRICTLY FORBIDDEN)
- **Direct Implementation Route**: `false` (STRICTLY FORBIDDEN)
- **Direct Test Execution**: `false` (STRICTLY FORBIDDEN)
- **Direct Git Write**: `false` (STRICTLY FORBIDDEN)
- **Direct Release**: `false` (STRICTLY FORBIDDEN)
- **Approval Authority**: `none` (Requests Owner Approval; does not self-approve)
- **Default Next Route**: `Brainstorming` (ONLY AFTER explicit Owner Approval)

---

## 1. Purpose & Core Principles

The `requirement-specification` skill produces the authoritative, single-source-of-truth **Requirement Specification** document for features, bug fixes, or quick tasks.

### Core Principles
1. **Describes WHAT, Not HOW**: The specification answers what problem is being solved and what behavior is required. It MUST NOT specify code classes, functions, or internal implementation details unless confirmed as hard constraints.
2. **Normalized Intent is NOT Approved Requirement**: Raw Intent or Normalized Intent MUST NOT bypass formal Requirement Specification and Owner Approval.
3. **Mandatory Owner Approval Before Brainstorming**: No transition to Brainstorming, Roadmap, Plan, or Blueprint is permitted until explicit Owner Approval is recorded.
4. **100% Traceability & Verifiability**: Every functional requirement MUST link to at least one verifiable Acceptance Criterion. No orphan requirements or criteria allowed.

---

## 2. Input Contract & Prerequisites Validation

Accepts ONLY a normalized intent payload containing:
- `intent_id`, `work_item_id`, `raw_prompt`, `normalized_goals`
- `domain`, `language_profile`, `risk_flags`, `ambiguity_taxonomy`
- Baseline SHA-256 hash & timestamp.

---

## 2.1 Canonical Path Mandate & Anti-Placeholder Rules

All Specification and Brainstorming artifacts MUST be generated directly into the standard Feature Family folders using **Strict Relative Paths**:
- `docs/features/<slug>/README.md` (Feature Family Index)
- `docs/features/<slug>/brainstorming/<slug>_brainstorming.md`

### 🚫 Strict Policies
- **Policy 11 (Absolute Path Prohibition)**: NEVER write machine full paths (`file:///...`, `e:/...`, `C:\...`). Always use relative paths starting from project root (`docs/features/...`).
- **Anti-Lazy & Complete ACs**: Gherkin Acceptance Criteria MUST be complete with specific `GIVEN`, `WHEN`, `THEN` statements. Generic placeholders (`// TODO`, `...`) trigger an automatic rejection.

---

## 3. 17 Requirement Specification Sections Supported

1. `metadata` (req_spec_id, work_item_id, intent_id, version, status, full_sha256)
2. `problem_statement` (statement, affected_actors, observed_evidence, current_impact)
3. `goals` (goal_id, description, priority)
4. `non_goals` (non_goal_id, description, reason)
5. `actors` (actor_id, name, type, goal, permissions)
6. `use_cases` (use_case_id, title, primary_actor, main_flow, alternative_flows)
7. `functional_requirements` (requirement_id, title, statement, priority, acceptance_criteria_ids)
8. `non_functional_requirements` (nfr_id, category, statement, metric, threshold)
9. `constraints` (constraint_id, type, description)
10. `data_requirements` (entity, owner, sensitivity, lifecycle)
11. `error_requirements` (error_behavior, user_message, recovery)
12. `edge_cases` (edge_case_id, scenario, expected_behavior)
13. `acceptance_criteria` (acceptance_id, requirement_id, given, when, then, verification_method)
14. `assumptions` (assumption_id, statement, risk_if_false)
15. `open_questions` (question_id, question, blocking_status)
16. `out_of_scope` (item, reason)
17. `dependencies` & `risks` & `traceability` & `approval`

---

## 4. 18 NFR Categories Supported

`PERFORMANCE`, `SCALABILITY`, `RELIABILITY`, `AVAILABILITY`, `RECOVERY`, `SECURITY`, `PRIVACY`, `OBSERVABILITY`, `MAINTAINABILITY`, `COMPATIBILITY`, `PORTABILITY`, `ACCESSIBILITY`, `USABILITY`, `RESOURCE_LIMITS`, `AUDITABILITY`, `DATA_INTEGRITY`, `CONCURRENCY`, `DEPLOYMENT`.

---

## 5. 10 Acceptance Verification Methods Supported

1. `STATIC_CHECK`
2. `BUILD_CHECK`
3. `MANUAL_REVIEW`
4. `UNIT_TEST`
5. `INTEGRATION_TEST`
6. `E2E_TEST`
7. `OBSERVATION`
8. `LOG_EVIDENCE`
9. `STATE_INSPECTION`
10. `NOT_YET_DEFINED` (Blocks approval readiness if assigned to a blocking requirement)

---

## 6. Requirement State Machine & Approval Boundary

```text
DRAFT → CLARIFYING → READY_FOR_REVIEW → REVIEWED → AWAITING_OWNER_APPROVAL → APPROVED → Brainstorming
```
*Secondary States*: `APPROVED_WITH_CONDITIONS`, `NEEDS_CHANGES`, `REJECTED`, `SUPERSEDED`, `CANCELLED`, `BLOCKED`.

### Approval Binding Requirements
Explicit Owner Approval MUST be bound to:
- Artifact Path
- Version
- Full SHA-256 Hash
- Approver Identity & Authority
- Timestamp
- Decision & Conditions

Conversational phrases (`"OK"`, `"Tiếp tục"`, `"Làm đi"`) DO NOT constitute approval.

---

## 7. Requirement Change Request (RCR) Policy

Any modification to an approved Requirement Specification invalidates the existing approval SHA-256 hash and requires:
1. Creating a formal Requirement Change Request (RCR).
2. Re-evaluating downstream impact on Brainstorming, Plan, or Blueprint.
3. Generating a new version and new full SHA-256 hash.
4. Obtaining new explicit Owner Approval.

---

## 8. Lightweight Requirement Contract (Quick Flows)

For `QUICK_FIX`, `QUICK_FEATURE`, `DOCUMENTATION_ONLY`, and `ANALYSIS_ONLY`:
- Uses `lightweight-requirement-template.md`.
- Requires: Problem, Goal, Scope, Non-Goals, Expected Behavior, Acceptance Criteria, Risk, and Confirmation Rule.
- Lightweight specs MUST NOT bypass confirmation before Brainstorming or Implementation.

---

## 9. Forbidden Routing Guards

- `DRAFT / CLARIFYING / READY_FOR_REVIEW / REVIEWED / AWAITING_OWNER_APPROVAL → BRAINSTORMING` (BLOCKED)
- `REQUIREMENT → IMPLEMENTATION / TEST / GIT / RELEASE` (BLOCKED)

Default Next Route after explicit Owner Approval: **`Brainstorming`** (`phase-07`).
