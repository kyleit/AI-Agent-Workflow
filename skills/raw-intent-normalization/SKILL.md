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
version: 1.1.0
license: MIT
created_at: 2026-07-29
updated_at: 2026-09-13
role: raw_intent_normalization
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
canonical_entrypoint_authority: false
direct_implementation_route: false
direct_test_execution: false
direct_git_write: false
direct_release: false
approval_authority: none
raw_intent_schema_version: 1.1.0
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

### Repository-First Intake Persistence

The normalized-intent transaction is a physical repository artifact
transaction. Before asking a blocking owner question or returning a planning
summary, the Agent MUST write the current intake state under the active
workspace using repository-relative paths:

- `docs/features/<family>/README.md` as the family index;
- `docs/features/<family>/intent/<slug>_normalized_intent.md` containing the
  raw request, preserved constraints, scope inventory, ambiguity ledger, and
  current status;
- `docs/features/<family>/questions/Q<nn>_<slug>.md` for the active question,
  including its options, impact, provenance, and waiting state.

The family and slug are derived from the request and workspace; they are not
hard-coded to a product domain. If the request is greenfield, the Agent MUST
create the documentation directories and empty-repository baseline inside the
documentation transaction, without creating product source.

An IDE brain artifact, chat response, terminal transcript, screenshot, or
external `implementation_plan.md` is supplemental evidence only. It MUST NOT
be treated as the normalized-intent artifact, a persisted question, a workflow
checkpoint, or a PASS. If the Agent cannot physically persist the
repository-relative intake artifact, it MUST stop with
`BLOCKED: ARTIFACT_PERSISTENCE_REQUIRED` and state the missing path.

### Repository-Relative Document Hygiene

The user prompt is input, not a document template. When persisting it, the
Agent MUST rewrite Markdown links and workspace paths to repository-relative
forms such as `skills/<name>/SKILL.md` or `docs/features/<family>/...`. It MUST
not copy `file:///...`, drive-letter paths, `/Users/...`, `/Volumes/...`, or
other machine-absolute paths into Markdown artifacts. Preserve the referenced
resource's meaning in a separate relative `skill_references` or `source`
field; do not preserve an unsafe absolute link merely because it appeared in
the prompt.

---

### Raw Intent Purity And Workflow Constraint Separation

The persisted `raw_intent` is a product statement, not an instruction manual
for the Agent. It MUST contain only the owner's desired product outcome,
observable product behavior, user-facing scope, and product constraints that
define what the system is. It MUST NOT contain workflow instructions,
authoring instructions, Skill names, gate commands, implementation recipes,
approval requests, dry-run policy, or directions addressed to an AI/agent.

When one user message mixes product intent with process or delivery demands,
the Agent MUST split it before writing the normalized artifact:

1. `raw_product_intent`: product-only statement, rewritten in outcome-focused
   language and free of Agent-directed instructions.
2. `user_goal`: the business or functional outcome sought by the owner.
3. `user_proposed_solutions`: technologies and mechanisms proposed by the
   owner, retained as candidate solution constraints with provenance.
4. `workflow_constraints`: delivery and verification policies requested by the
   owner, including documentation completeness, full-file code blocks,
   real-project source verification, apply-readiness, and prohibition of
   mock/dry-run evidence. These constraints are for downstream Skills and
   gates; they MUST NOT be copied into `raw_product_intent`.
5. `excluded_from_raw_intent`: an explicit ledger of removed process phrases
   and the downstream artifact or gate that enforces each one.

The raw-intent artifact MUST preserve provenance for both product and process
statements, but provenance is not permission to mix them. A source prompt may
be retained as a separate `source_prompt_provenance` field or evidence file;
it MUST NOT be presented as the normalized `raw_intent` when it contains
Agent-directed instructions.

Before advancing, the Agent MUST perform a purity review:

- `raw_product_intent` can be read by a product owner without mentioning
  Skills, agents, blueprints, code blocks, approvals, gates, or commands;
- every workflow constraint has an owner, enforcement stage, and evidence
  field outside `raw_product_intent`;
- no workflow instruction has been silently dropped; it is either mapped to a
  downstream contract or recorded as an unresolved blocker;
- the artifact is read back after persistence and the purity result is stored
  in the intake evidence.

Raw-intent normalization MUST NOT claim that a Blueprint is complete merely
because a workflow constraint was recorded. Completeness, full-file material,
real source alignment, and runtime verification are decided by the
corresponding downstream Skills and gates.

### Greenfield Completeness Handoff

If the normalized product intent describes a project with no existing source
baseline, the Agent MUST classify it as `GREENFIELD_CROSS_LAYER` when it spans
two or more runtime surfaces such as backend, database, web frontend, desktop
shell, or local assets. It MUST hand downstream Blueprint Skills a complete
coverage inventory for actors, routes/screens, entities/schema, API/events,
runtime modes, failure/retry behavior, security, persistence/retention,
assets, and real acceptance evidence.

For `GREENFIELD_CROSS_LAYER`, downstream Blueprint generation MUST enumerate
every concrete file required to produce the declared product surface and map
each file to exactly one implementation-ready `full-file` block (or an
explicit non-placeholder asset manifest). A phase that contains only
signatures, representative snippets, pseudocode, or a partial file is
incomplete. The strict code-block gate MUST return `BLOCKED` and the workflow
MUST regenerate the affected Blueprint before any approval request.

The handoff MUST distinguish these states:

- `DOCUMENTATION_COMPLETE`: all required artifacts and complete blocks exist;
- `CODE_BLOCKS_VERIFIED`: strict metadata, profile, path, and materialization
  checks pass against the declared empty-repository baseline;
- `PRODUCT_RUNTIME_VERIFIED`: the applied files build, start, and pass real
  integration/browser/desktop E2E.

The first two states MUST NOT be reported as the third. `NOT_RUN`, mock,
inferred, or dry-run output is never runtime verification.

---

## 3. Goal vs. Proposed Solution Separation

Every Raw Intent normalization MUST explicitly separate:
- **`user_goal`**: The functional objective or desired business outcome.
- **`user_proposed_solutions`**: Specific mechanisms, frameworks, or code paths suggested by the user. User-proposed solutions are treated as candidates, not hard constraints.

---

## 4. Missing Information Classification

Unknowns discovered during intake are classified into three strict tiers:
1. **`DISCOVERABLE`**: Information obtainable by inspecting workspace code or docs. *Action: Auto-discover quietly.*
2. **`NON_BLOCKING`**: Information that can be safely inferred using project conventions and cannot change scope, data, API, UX, runtime, or security behavior. *Action: Record safe assumption.*
3. **`BLOCKING`**: High-impact ambiguity with severe risk or multiple conflicting interpretations. *Action: Ask concise targeted question and stop the transition.*

For a greenfield product, missing routes/screens, domain entities, persistence
semantics, API behavior, runtime modes, network/probe semantics, failure
recovery, security, or acceptance behavior are `BLOCKING` unless the user has
explicitly specified them. The Agent MUST NOT promote these items to
`NON_BLOCKING` merely because a framework convention exists. A convention may
be proposed as a labeled option, never silently selected as fact.

The Agent MUST maintain a greenfield coverage checklist for actors/scope,
screens/routes, entities/schema, API/events, runtime behavior, failure/retry,
security, persistence/retention, and real acceptance evidence. Every unchecked
dimension remains `BLOCKING` and keeps the workflow in `CLARIFYING` until the
owner answers it or the Agent records inspectable approved evidence. This is a
reasoning obligation for the Agent, not a hard-coded product decision for a
runtime script.

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

### Clarification Checkpoint Enforcement

Before emitting `RESTATED` or `NORMALIZED`, the Agent MUST produce an
ambiguity ledger with `fact`, `source`, `classification`, `impact`, and
`resolution`. If any `BLOCKING` item has no confirmed answer, the workflow
MUST enter `CLARIFYING`, ask the owner through the native structured question
mechanism, persist the pending question, and stop. It MUST NOT generate a
Requirement Specification, choose an architecture, or report readiness while
that question is pending. `assumption` is not a substitute for owner choice
for a blocking item.

### Owner Response Fidelity Contract

Every clarification is a transaction against exactly one active question. The
Agent MUST capture the active question, the complete option set, the owner's
answer, and the resulting decision before updating the ledger. A response such
as `Option 1`, `Yes`, or `Continue` MUST be resolved only against the currently
active question; it MUST NOT be matched against a previous question, a cached
recommendation, model memory, or a similarly named decision. The ledger MUST
preserve the selected option's exact meaning and its owner-response evidence.

Before advancing, the Agent MUST perform a semantic consistency pass:

1. Re-read the last question and its options.
2. Map the owner's answer to one and only one option in that question.
3. Compare every value written to the ledger with that option's actual text.
4. If the answer is ambiguous, the question is stale, or the proposed ledger
   value differs from the selected option, remain `CLARIFYING` and ask again.

The Agent MUST NOT invent an owner-response ID, claim confirmation without a
captured response, or compress a selected option into a different policy. A
recommendation is not a decision until the owner selects it. Runtime scripts
may validate that this evidence is present and internally consistent, but they
must not reconstruct the decision.

### AI-First Decision Ownership

The persisted `CLARIFYING` artifact is the authoritative output of this
stage. The Agent MUST return the owner question only after the file write and
read-back verification succeed. It MUST resume from that exact repository
question transaction, not from a copied IDE plan or model memory.

An option proposed by the Agent is not an owner decision. The initial product
brief, a recommended option, silence, a generic approval phrase, or the
Agent's statement that an option was "adopted" MUST NOT resolve a blocking
question. Resolution requires the owner's answer to the current question and
an exact response receipt or native response provenance. Until then, the
question remains `PENDING_OWNER_RESPONSE`, the workflow remains
`CLARIFYING`, and no downstream artifact may be marked approved or ready.

The Agent owns the reasoning work: inspect the request, enumerate the missing
decision dimensions, present viable options, explain trade-offs, and ask one
blocking question at a time. Runtime scripts are guardrails only. They may
validate ledger shape, state, provenance, and transition boundaries, but MUST
NOT invent a domain decision, silently choose an option, or replace the
Agent's analysis with a hard-coded product heuristic. If the Agent has not
produced a ledger, the runtime may fail closed with a generic
clarification-required state; it must not fabricate the ledger's content.

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
