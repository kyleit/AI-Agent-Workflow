---
name: plan-to-blueprint
command: blueprint
aliases:
  - design
  - architecture
  - technical-blueprint
category: workflow
tags:
  - blueprint
  - design
  - architecture
  - contracts
  - governance
version: 3.3.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-29
role: blueprint_design_orchestrator
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
input_contract: plan_architecture_approved_plan
output_contract: technical_blueprint_artifact
allowed_input_plan_statuses:
  - ARCHITECTURE_APPROVED
  - ARCHITECTURE_APPROVED_WITH_CONDITIONS
readiness_gate: BLUEPRINT_READINESS
readiness_threshold: 95
architecture_review_type: BLUEPRINT_APPROVAL
approval_authority: none
freeze_is_implementation_approval: false
default_next_route: implementation_entry_gate
description: Transforms an architecture-approved execution plan into a production-grade Technical Blueprint, specifying component boundaries, interface contracts, data models, concurrency, error handling, file impact maps, implementation sequences, and verification matrices. Evaluates Blueprint Readiness (95/100), requests Blueprint Architecture Approval, executes Blueprint Freeze, and prepares handoff for Implementation Entry.
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

# Skill: plan-to-blueprint (Technical Blueprint Engine)

## 0. Contract & Governance Boundaries

- **Role**: `blueprint_design_orchestrator`
- **Activation Mode**: `delegated` (Delegated by `workflow-coordinator` after Plan Architecture Approval)
- **Canonical Entrypoint**: `workflow-coordinator`
- **Input Contract**: `Plan-Architecture-Approved Plan` (`schemas/roadmap-plan-handoff.schema.json` v1.0.0)
- **Output Contracts**:
  - `Technical Blueprint Artifact` (`schemas/blueprint.schema.json` v1.0.0)
  - `Blueprint Freeze Record` (`schemas/blueprint-freeze.schema.json` v1.0.0)
  - `Implementation Entry Handoff` (`schemas/implementation-entry-handoff.schema.json` v1.0.0)
- **Allowed Input Plan Statuses**: `ARCHITECTURE_APPROVED`, `ARCHITECTURE_APPROVED_WITH_CONDITIONS`
- **Readiness Gate**: `BLUEPRINT_READINESS` (Evaluated by `readiness-and-approval-gates`, threshold `95/100`)
- **Blueprint Architecture Approval**: `BLUEPRINT_APPROVAL` (Reviewed by `architecture-review`)
- **Freeze Is Implementation Approval**: `false` (Blueprint Freeze DOES NOT grant Implementation Authorization!)
- **Direct Source Write**: `false` (STRICTLY FORBIDDEN)
- **Direct Implementation Execution**: `false` (STRICTLY FORBIDDEN)
- **Direct Test Execution**: `false` (STRICTLY FORBIDDEN)
- **Direct Git Write**: `false` (STRICTLY FORBIDDEN)
- **Direct Release**: `false` (STRICTLY FORBIDDEN)
- **Approval Authority**: `none` (Requests Blueprint Architecture Approval; cannot self-approve)
- **Default Next Route**: `implementation_entry_gate` (ONLY AFTER Blueprint Freeze & Implementation Entry Authorization)

> [!CRITICAL]
> **Cross-Skill Strict Policy & Physical Write Invariant**:
> **STRICT ENGINEERING POLICY IS AUTHORITATIVE.**
> The skill MUST load the Core Engineering Policy (`.agents/policies/strict-engineering.md`), Physical Repository Write Policy (`.agents/policies/physical-repository-write.md`), all active Language Profiles (`.agents/profiles/*.yaml`), and the Project Architecture Contract (`.agents/contracts/engineering-quality-gates.yaml`) before generating technical design specifications.
> A skill MUST NOT weaken, bypass, suppress, reinterpret, or locally override a blocking gate.
> Blueprint MUST compute affected language matrices, enforce the 500-line budget limit per file (defining family-folder split strategies for files >500 projected lines), and bind policy SHA-256 hashes in the Blueprint frontmatter.
> If compliance requires an architecture change outside the skill's current approved authority, the skill MUST raise architecture/blueprint drift and route through AIWF change control.

---

## 1. Purpose & Core Principles

The `plan-to-blueprint` skill upgrades an architecture-approved execution plan into a production-grade **Technical Blueprint**.

### Core Principles
1. **Requires Architecture-Approved Plan Input**: Accepts ONLY execution plans with status `ARCHITECTURE_APPROVED` or `ARCHITECTURE_APPROVED_WITH_CONDITIONS` and a verified full SHA-256 hash.
2. **Defines Technical Design (HOW), Not Source Code**: The blueprint specifies component boundaries, interface contracts, data models, data flows, concurrency, error handling, file impact maps, implementation sequences, and verification matrices. It DOES NOT modify feature source code.
3. **Zero Unresolved Blocking Placeholders**: All placeholders (`TODO`, `TBD`, generic instructions) MUST be cataloged. The presence of any blocking placeholder triggers an AUTOMATIC FAIL during readiness evaluation.
4. **Blueprint Freeze ≠ Implementation Approval**: Blueprint Freeze records artifact immutability. Implementation authorization requires passing `IMPLEMENTATION_ENTRY` gate separately.

---

## 1.1 The 5 Pillars of Technical Blueprint Excellence (MANDATORY STANDARDS)

Every generated Technical Blueprint MUST strictly embed and satisfy all 5 Golden Pillars:

### 🌟 Pillar 1: Golden Blueprint Reference Architecture
The model MUST consult and pattern-match against the project's canonical master blueprints:
- `docs/features/ai-agent-os/blueprints/master/FEAT-OS-001_master_blueprint.md`
- `docs/features/go-build-system/plans/FEAT-500_golang_native_runtime_plan.md`

### 📋 Pillar 2: Mandatory 10-Section Blueprint Schema (Zero Omissions)
The Blueprint MUST contain all 10 numbered sections in strict sequence:
1. **Section 1: Document Control & Upstream Traceability** (Strict Relative Paths only)
2. **Section 2: Executive Architecture & 4-Layer DDD Topology** (Mermaid Component Diagram)
3. **Section 3: Component Boundaries & Interface Contracts** (Exact Pydantic v2 / Go Structs / C# DTOs, Ports, Adapters)
4. **Section 4: Data Flow & Sequence Diagram** (Mermaid Request/Response Lifecycle)
5. **Section 5: Concurrency, Locking & Safe-Write Strategy** (Mode B Single-Writer Isolation)
6. **Section 6: Security Safeguards, Password Hashing & Auth Controls** (NIST SP 800-132, PBKDF2/JWT, OWASP)
7. **Section 7: File-by-File Change Matrix** (Path, DDD Layer, `[NEW]`/`[MODIFY]`, Family Folder, Facade/Aggregate Entry, Imports, Exports, Exact Signatures, Line Budget < 500)
8. **Section 8: Specialist Implementation Sequence DAG** (Task breakdown and dependency graph)
9. **Section 9: QA Verification Matrix** (Unit + End-to-End Acceptance Criteria Mapping)
10. **Section 10: Blueprint Readiness Assessment & Code Block Gate** (Score: 100/100 -> PASS)

### 🚫 Pillar 3: Anti-Placeholder / Anti-Lazy Policy
- **BANNED**: `// TODO`, `...`, `tương tự như trên`, `xem tài liệu khác`, `generic helpers`.
- **BANNED**: Machine absolute paths (`file:///...`, `e:/...`, `C:\...`, `/home/...`). Strictly relative paths only (Policy 11).
- **REQUIRED**: 100% of fields, data types, HTTP status codes (200, 201, 400, 401, 403, 404, 422, 500), and function signatures must be explicitly typed and written out in full.

### 🗂️ Pillar 4: Exhaustive File-by-File Change Matrix
Every affected file must be defined with:
- **Canonical Relative Path** (e.g. `src/auth/domain/entities/user.py`)
- **DDD Layer** (`Domain`, `Application`, `Infrastructure`, `Presentation`)
- **Mutation Type** (`[NEW]`, `[MODIFY]`, `[DELETE]`)
- **Imports & Exports List**
- **Exact Method Signatures & Return Types**
- **Line Budget Limit** (< 500 lines per file; family-folder split strategy if projected > 500 lines)
- **Family-Folder Split Contract**: If a file is split for line budget, all extracted files must live under one shared family-name directory and one facade/barrel/aggregate entry file must be defined for outside imports. Flat scatter-splitting into the parent directory is forbidden.

### ⚖️ Pillar 5: Weighted Gate Scoring & Deterministic Unlock Rules
Readiness scoring is evaluated on a 100-point scale across 4 core dimensions (25 pts each):
1. **Clean Architecture & DDD 4 Layers Isolation** (25 pts)
2. **Interface Contracts & Typed DTO Schemas** (25 pts)
3. **Security Safeguards & Cryptographic Controls** (25 pts)
4. **Automated Verification Matrix Coverage** (25 pts)

**GATING RULE**:
- If Total Score $\ge 95/100$ and zero blocking violations and the canonical strict gate result is `PASS`: `CODE_BLOCK_GATE: PASS`.
- If Total Score $< 95/100$: `CODE_BLOCK_GATE: BLOCKED` (Coder cannot edit source code until revisions pass).

---

## 2. Input Contract & Prerequisites Validation

Accepts ONLY a plan-architecture-approved handoff containing:
- `plan_id`, `plan_version`, `plan_full_hash`
- `requirement_spec_id`, `brainstorming_id`, `roadmap_id` (and all upstream full SHA-256 hashes)
- Plan architecture review status: `ARCHITECTURE_APPROVED` or `ARCHITECTURE_APPROVED_WITH_CONDITIONS`
- Tasks, dependencies, owners, expected file impacts, collaboration mode, safe-write requirements, verification & rollback requirements.

Unapproved plan statuses ARE STRICTLY REJECTED.

---

## 3. Current-State vs Target-State Architecture

- **Current-State Analysis**: Grounded in empirical repository evidence (`baseline_commit`, existing components, boundaries, interfaces, known defects).
- **Target-State Architecture**: Defines target components, responsibilities, input/output contracts, and allowed vs forbidden dependency directions. Generic component names ("Manager", "Utils", "Common") ARE PROHIBITED.

---

## 4. Component Boundaries & Interface Contracts

- **Boundary Contracts**: Defines module, package, service, data ownership, write ownership, and security boundaries. Multiple components MUST NOT share a data write path without explicit protocols.
- **Interface Contracts**: Specifies provider, consumers, purpose, input schema, output schema, error models, timeout/retry policies, idempotency, and versioning.

---

## 5. Data Models, Data Flow & Persistence Design

- **Data Models**: Classifies entities (`DOMAIN_ENTITY`, `VALUE_OBJECT`, `DTO`, `EVENT`, `COMMAND`, `QUERY`, `PERSISTENCE_MODEL`).
- **Data Flow**: Maps happy path, failure path, cancel, resume, and recovery flows with Mermaid visualization.
- **Persistence**: Defines stores, schemas, transaction boundaries, consistency models, and migrations. Guarantees a Single Source of Truth.

---

## 6. Concurrency, Safe-Write & Error Handling

- **Concurrency Design**: Specifies concurrency model (`SINGLE_THREADED`, `ASYNC_SERIAL`, `BOUNDED_PARALLEL`, `MULTI_PROCESS`).
- **Safe-Write Strategy**: Enforces `single_writer: true` under Mode B. Mode C is blocked (`MODE_C_NOT_ELIGIBLE`) unless explicit OCC runtime prerequisites exist.
- **Error Taxonomy**: Categorizes errors (`VALIDATION_ERROR`, `AUTH_ERROR`, `NOT_FOUND`, `CONFLICT`, `TIMEOUT`, `DEPENDENCY_UNAVAILABLE`, `RATE_LIMIT`, `CONCURRENCY_CONFLICT`, etc.) with explicit retry and rollback policies.

---

## 7. Security, Observability, Configuration & Migration

- **Security & Privacy**: Enforces least privilege, input validation, output encoding, path traversal prevention, secret protection, and data minimization.
- **Observability**: Specifies logging, metrics, tracing, health checks, and correlation IDs without logging sensitive data/secrets.
- **Migration & Compatibility**: Mandatory migration design for schema changes, API breaking changes, or layout updates. Preserves backward compatibility.

---

## 8. File Impact Map, Implementation Sequence, Verification Matrix & Blueprint Quality Gates

- **File Impact Map**: Classifies files (`allowed_files`, `protected_files`, `generated_files`, `mirror_files`). `skills/**` is authoritative; `.agents/skills/**` is mirror (direct edit forbidden).
- **Implementation Sequence**: Non-ambiguous, step-by-step technical instructions without code snippets.
- **Verification Matrix**: Maps Requirement → AC → Component → Interface → Verification Method → Owner (`TESTER` Agent owns test execution; tests default to `NOT_RUN`).
- **Rollback Design**: Explicit rollback steps for high-risk operations.

> [!CAUTION]
> **CODE_BLOCK_GATE — MANDATORY for every implementation-ready code block written into this Blueprint**
> Every non-trivial code block (function signature, struct definition, SQL schema, migration snippet, config schema, rule, or script) MUST be routed through `skills/strict-code-block-gate/SKILL.md`.
> 1. Add structured metadata immediately before each implementation-ready fenced block: `id`, `language`, `file`, `operation`, and `implementation_ready: true`.
> 2. Resolve the language through the strict profile registry. Missing, ambiguous, or non-strict profiles are `BLOCKED`.
> 3. Materialize validation-only snippets under `.agents/tmp/code-block-gate/<workflow-id>/`; never write product source as part of this gate.
> 4. Persist `code-block-gate.json` with `decision`, `blueprint_full_sha256`, `per_code_block`, `profile_results`, `materialized_scope`, and `test_status: NOT_RUN`.
> 5. A code block is **BANNED** from this Blueprint if it lacks metadata, uses placeholders, depends on guessed source identifiers, has no strict language profile, or cannot be mapped to the architecture boundary.
> `NOTE`, `PENDING`, local-only checks, or legacy `UNLOCKED` wording in the Internal Review Evidence CODE_BLOCK_GATE row = automatic FAIL.

**Internal Review Evidence** — every generated Blueprint MUST include this table before submission for Architecture Approval:

```markdown
| Field | Evidence |
|---|---|
| Reviewer Roles | Architect / Reviewer / QA / relevant Specialist roles |
| Source Artifacts Reviewed | Plan, Brainstorming, Requirement Spec, active Skill, `AI_RULES.md` |
| Checklist — No Placeholders (TBD/TODO/etc.) | `PASS` / `FAIL` |
| Checklist — File-by-File Change Matrix | `PASS` / `FAIL` — every file listed with operation + responsibility |
| Checklist — Line Budget <500 | `PASS` / `FAIL` — every touched source file lists projected physical line count; files projected over 500 define split tasks before approval |
| Checklist — Family-Folder Split Contract | `PASS` / `FAIL` / `NOT_APPLICABLE` — every split groups extracted files under one family-name directory and defines one facade/barrel/aggregate entry file for outside imports |
| Checklist — Language Profiles & Lint Plan | `PASS` / `FAIL` — every affected language maps to an active strict profile and lists exact build/lint/typecheck/test commands |
| Checklist — API & Interface Signatures | `PASS` / `FAIL` — all signatures have input types, return types, error behavior |
| Checklist — Data Schemas & Models | `PASS` / `FAIL` — SQL, struct, interface, JSON schema complete |
| Checklist — Test Strategy | `PASS` / `FAIL` — AC assertions are binary testable |
| Checklist — Risk & Mitigation | `PASS` / `FAIL` |
| **CODE_BLOCK_GATE** | **`PASS` / `FAIL` / `BLOCKED` / `NOT_APPLICABLE`** — canonical `strict-code-block-gate` result. Include `code-block-gate.json`, `blueprint_full_sha256`, profile coverage, and blocking findings. `NOTE`, `PENDING`, or legacy `UNLOCKED` = FAIL. |
| Failed Points | `None` or exact failed-point list |
| Revision Scope | `None` or exact sections revised |
| Re-review Count | `0` for first-pass PASS, otherwise count |
| Document Compliance Score | `NN/100` |
| Relative Path Scan | PASS only when no `file:///`, `/Users/`, `/Volumes/`, drive-letter paths |
| Final Result | `PASS` or `FAIL` |
```

---

## 9. Blueprint State Machine Lifecycle

```text
DRAFT → CURRENT_STATE_ANALYZING → TARGET_STATE_DESIGNING → CONTRACTS_DEFINING → RISKS_VALIDATING → READY_FOR_REVIEW → REVIEWED → AWAITING_ARCHITECTURE_APPROVAL → ARCHITECTURE_APPROVED → FROZEN → Implementation Entry Gate
```
*Secondary States*: `ARCHITECTURE_APPROVED_WITH_CONDITIONS`, `NEEDS_CHANGES`, `BLOCKED`, `INVALIDATED`, `SUPERSEDED`, `CANCELLED`.

---

## 10. Gate Hooks, Architecture Approval, Blueprint Freeze & User Approval Anti-Bypass

1. **Readiness Evaluation**: Calls `skills/readiness-and-approval-gates/SKILL.md` for gate `BLUEPRINT_READINESS`.
   - Requires score >= **95/100**.
   - Enforces **Strict Blocking Rule**: Unresolved blocking placeholders, missing interface contracts, missing migration for breaking changes, missing rollback, missing line-budget evidence, missing family-folder split evidence when a split is required, missing language lint/typecheck/build command matrix, missing strict profile, stale Blueprint hash, or **canonical CODE_BLOCK_GATE not explicitly marked `PASS`** MUST set decision to `BLOCKED`.
2. **Architecture Blueprint Approval Gate**:
   - The Agent MUST present the Design Blueprint summary to the user and ask for implementation approval.
   - **PRIMARY (NATIVE UI)**: Use the native Agent/IDE `ask_question` tool first with options `Continue` and `Cancel`.
   - **FALLBACK BRIDGE (CLI)**: Only if native `ask_question` is unavailable, attempt the CLI prompt bridge:
     `aiwf prompt select --question "Approve this Technical Design Blueprint for implementation?" --options "Continue|Cancel" --default "Cancel"`
   - If the fallback bridge returns `PROMPT_UNAVAILABLE`, no prompt was shown and no user selection occurred.
   - After invoking the prompt (via native tool or CLI), **immediately stop calling ALL tools and end the turn unconditionally**.
   - **CHAT APPROVAL IS NEVER VALID AS A FALLBACK.** An Agent MUST NOT self-declare bridge unavailability to unlock implementation.
   - The ONLY valid approval evidence is: native `ask_question` returning `Continue`, the fallback UI/CLI bridge returning `Continue`, OR the user explicitly writing the exact phrase **`APPROVE BLUEPRINT`** (case-insensitive) in a **new user turn** after structured prompting was unavailable.
   - Any other chat text (`ok`, `proceed`, `yes`, `go ahead`) is **NOT** a valid approval.
   - Claiming bridge unavailability in the same turn as the Blueprint presentation and then continuing to implement is a **CRITICAL VIOLATION**.
3. **Blueprint Freeze**: Once approved, issues `blueprint-freeze.schema.json` recording full SHA-256 hash, baseline commit, allowed/protected files, and freeze timestamp.
4. **Implementation Entry Gate**: Passes handoff (`schemas/implementation-entry-handoff.schema.json`) to `IMPLEMENTATION_ENTRY` gate.
5. **Live Checklist Ticking during Implementation** (applies when agent proceeds to implementation after approval):

   > [!IMPORTANT]
   > **Each checklist item in the Blueprint's Implementation Checklist MUST be ticked `[x]` immediately after its code write completes.**
   > Loop: Read item → Implement code → Update Blueprint `- [ ]` → `- [x]` → Next item.
   > Batching all code then ticking at the end is **FORBIDDEN**.
   > Blocked items use `- [!]` marker with inline blocker note. Do NOT skip silently.

---

## 11. Quick Flow & Specialized Paths

- **Quick Feature**: Uses `lightweight-blueprint-template.md` (lightweight component & interface contract; requires readiness and architecture approval if architectural impact exists).
- **Quick Fix**: Uses `patch-blueprint-template.md` (root-cause evidence, patch boundary, regression boundary, target vs protected files).
- **Documentation-Only & Analysis-Only**: Uses `BLUEPRINT_NOT_REQUIRED` or `NO_IMPLEMENTATION_ROUTE` with zero code execution (`NO_SOURCE_WRITE`).

---

## 12. Change Control & Invalidation

If any upstream artifact (Requirement, Brainstorming, Roadmap, or Plan) changes (full SHA-256 hash drift):
- The Technical Blueprint is IMMEDIATELY marked **`INVALIDATED`**.
- Blueprint Freeze is **`REVOKED`**.
- Implementation Entry authorization is **`BLOCKED`**.
- Re-evaluation and new Blueprint Architecture Approval ARE REQUIRED.

---

## 13. Forbidden Routing Guards (STRICTLY BLOCKED)

- `DRAFT / DESIGNING / CONTRACTS_DEFINING → IMPLEMENTATION` (BLOCKED)
- `UNAPPROVED PLAN → BLUEPRINT` (BLOCKED)
- `UNAPPROVED BLUEPRINT → IMPLEMENTATION` (BLOCKED)
- `FROZEN BLUEPRINT WITHOUT IMPLEMENTATION ENTRY PASS → IMPLEMENTATION` (BLOCKED)
- `BLUEPRINT → SOURCE_CODE_EXECUTION / TEST / GIT / RELEASE` (BLOCKED)
