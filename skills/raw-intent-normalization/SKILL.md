---
name: raw-intent-normalization
command: normalize-intent
aliases:
  - raw-intent
  - intent-intake
category: workflow
tags:
  - intake
  - normalization
  - intent
  - discovery
version: 1.0.0
license: MIT
created_at: 2026-07-29
updated_at: 2026-07-29
role: raw_intent_normalization
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
canonical_entrypoint_authority: false
direct_implementation_route: false
direct_test_execution: false
direct_git_write: false
direct_release: false
approval_authority: none
raw_intent_schema_version: 1.0.0
description: Normalizes raw user prompts into structured Normalized Intent using context discovery, goal separation, ambiguity taxonomy, and risk flags.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

# Skill: raw-intent-normalization (Raw Intent Intake & Normalization Engine)

## 0. Contract & Governance Boundaries

- **Role**: `raw_intent_normalization`
- **Activation Mode**: `delegated` (Delegated exclusively by `workflow-coordinator`)
- **Canonical Entrypoint**: `workflow-coordinator` (Does NOT act as a competing entrypoint)
- **Direct Implementation Route**: `false` (STRICTLY FORBIDDEN)
- **Direct Test Execution**: `false` (STRICTLY FORBIDDEN)
- **Direct Git Write**: `false` (STRICTLY FORBIDDEN)
- **Direct Release**: `false` (STRICTLY FORBIDDEN)
- **Approval Authority**: `none` (Detects candidate signals only; cannot execute gates)
- **Default Next Route**: `Requirement Specification` (`phase-05`)

---

## 1. Purpose & Core Principles

The `raw-intent-normalization` skill takes unrefined, ambiguous, or conversational user prompts ("Raw Intent") and transforms them into a structured, validated **Normalized Intent** schema (`raw-intent.schema.json` v1.0.0).

### Core Principles
1. **Raw Prompt is NEVER an Approved Requirement**: Initial user messages must be normalized and pass formal requirement contracts before planning or implementation.
2. **Context Discovery Before Clarification**: Check all local project evidence, docs, code, and session history before asking the user any questions.
3. **Separate User Goal from Proposed Solution**: Maintain independent abstractions for what the user wants to achieve vs how they propose to build it.
4. **3-Way Information Classification**: Categorize all unknowns into `BLOCKING`, `NON_BLOCKING`, or `DISCOVERABLE`.

---

## 2. Context Discovery Before Clarification

Before generating clarification questions, the system MUST inspect:
- Current user message and conversation history.
- Approved workflow artifacts (`docs/aiwf-redesign/**`).
- Project state files (`.agents/state/*.json`).
- Repository documentation, source code, configs, and existing blueprints.
- Read-only test files and examples.

Questions for facts classified as `DISCOVERABLE` are **STRICTLY PROHIBITED**.

---

## 3. Goal vs. Proposed Solution Separation

Every Raw Intent normalization MUST explicitly separate:
- **`user_goal`**: The functional objective or desired business outcome.
- **`user_proposed_solutions`**: Specific mechanisms, frameworks, or code paths suggested by the user. User-proposed solutions are treated as candidates, not hard constraints.

---

## 4. Missing Information Classification

Unknowns discovered during intake are classified into three strict tiers:
1. **`DISCOVERABLE`**: Information obtainable by inspecting workspace code or docs. *Action: Auto-discover quietly.*
2. **`NON_BLOCKING`**: Information that can be safely inferred using project conventions. *Action: Record safe assumption.*
3. **`BLOCKING`**: High-impact ambiguity with severe risk or multiple conflicting interpretations. *Action: Ask concise targeted question.*

---

## 5. Ambiguity Taxonomy (17 Supported Types)

1. `SCOPE_AMBIGUITY`
2. `GOAL_AMBIGUITY`
3. `ACTOR_AMBIGUITY`
4. `BEHAVIOR_AMBIGUITY`
5. `DATA_AMBIGUITY`
6. `COMPATIBILITY_AMBIGUITY`
7. `SECURITY_AMBIGUITY`
8. `ERROR_HANDLING_AMBIGUITY`
9. `PERFORMANCE_AMBIGUITY`
10. `PLATFORM_AMBIGUITY`
11. `DELIVERABLE_AMBIGUITY`
12. `APPROVAL_AMBIGUITY`
13. `CONFLICTING_REQUIREMENTS`
14. `STALE_CONTEXT`
15. `TERM_AMBIGUITY`
16. `POSSIBLE_TYPO`
17. `SOLUTION_GOAL_CONFUSION`

---

## 6. Intent Type Taxonomy (16 Supported Types)

1. `QUICK_FIX`
2. `BUG_FIX`
3. `QUICK_FEATURE`
4. `STANDARD_FEATURE`
5. `REFACTOR`
6. `ARCHITECTURE_CHANGE`
7. `INFRASTRUCTURE_CHANGE`
8. `SECURITY_CHANGE`
9. `DOCUMENTATION_ONLY`
10. `ANALYSIS_ONLY`
11. `RELEASE_ONLY`
12. `RESUME`
13. `CANCEL`
14. `RECOVERY`
15. `UNKNOWN`
16. `MIXED`

*Note: `UNKNOWN` and `MIXED` MUST NOT route to implementation.*

---

## 7. Clarification Policy Rules

- **Limit**: Max 1 decision per question, max 2-4 options per question.
- **Tone**: Clear, jargon-free, outcome-focused.
- **Recommendations**: Always provide a recommended option and safe default for non-blocking items.
- **No Repeat Questions**: Do NOT ask previously answered questions during workflow resume.

---

## 8. Intent Restatement Template

Every normalized intent MUST output an Intent Restatement containing:
- **Understood Goal**: Abstracted objective.
- **Expected Outcomes**: Observable behaviors.
- **Scope Boundary**: Included vs out-of-scope items.
- **Proposed Solution**: User's suggested technical path.
- **Constraints & Preferences**: Hard limits vs choices.
- **Working Assumptions**: Safe defaults applied.
- **Open Blockers**: Remaining questions if any.
- **Next Step**: Transition to `Requirement Specification`.

---

## 9. Approval Signal Guard

Statements like `"OK"`, `"Làm luôn"`, `"Code đi"`, `"Commit đi"`, `"Release đi"` are classified as `approval_signal_candidate`.

**CRITICAL RULE**: Approval signals detected during Raw Intent intake MUST NOT execute approvals, open gates, mutate code, or trigger git/release actions. They require formal artifact/version/hash approval records.

---

## 10. Risk Flags Taxonomy (8 Supported Types)

1. `DATA_DELETION`
2. `BREAKING_API`
3. `AUTH_CHANGE`
4. `SECRET_HANDLING`
5. `PRODUCTION_CHANGE`
6. `GIT_WRITE`
7. `RELEASE_ACTION`
8. `MIGRATION`

Any active risk flag triggers safety checks and requires explicit gate authorization in subsequent phases.

---

## 11. State Machine Lifecycle

```text
RAW → DISCOVERING → INTERPRETING → CLARIFYING → RESTATED → NORMALIZED
                                                          ↓
                                              Requirement Specification (Phase 05)
```
*Secondary States*: `BLOCKED`, `CANCELLED`, `FAILED`.

---

## 12. Forbidden Routing Guards

The following routes are **STRICTLY FORBIDDEN**:
- `RAW → IMPLEMENTATION` (BLOCKED)
- `DISCOVERING → IMPLEMENTATION` (BLOCKED)
- `INTERPRETING → IMPLEMENTATION` (BLOCKED)
- `CLARIFYING → IMPLEMENTATION` (BLOCKED)
- `NORMALIZED → BRAINSTORMING / PLAN / BLUEPRINT / IMPLEMENTATION / TEST / GIT / RELEASE` (BLOCKED)
- `UNKNOWN / MIXED → IMPLEMENTATION` (BLOCKED)

Default next route: **`Requirement Specification`** (`phase-05`).
