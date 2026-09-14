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

> 6. **APPROVAL ORDER IS HARD-GATED**: Do not invoke native `ask_question`,
> present a Blueprint approval prompt, or claim that a draft is ready while
> generating or repairing the artifact set. First write the complete
> `Master -> Family -> Small Feature -> Phase` files, then run the runtime
> Blueprint validator and recursive `strict-code-block-gate` against the same
> hash. Only the exact pair `status=APPROVAL_READY`, `score=100`, empty
> findings, and `decision=PASS` with zero blocking per-block findings permits
> an owner approval question. Any missing/failed/unread evidence is
> `BLOCKED`; continue repair and never ask the owner to approve a draft.

### Authoring Ledger Before Markdown

The ledger and all reasoning-heavy documents MUST be written with native Agent
file tools. Do not use Python, PowerShell, Node, shell heredocs, `echo >`,
`Set-Content`, `Out-File`, or ad-hoc scripts to generate or rewrite document
content. Scripts are limited to deterministic reads, directory creation,
hashing, parsing, validation, gate execution, and evidence collection. A
script-generated Blueprint or evidence file is not accepted as Agent
authorship and MUST remain `BLOCKED`.

Before approval, the runtime authoring-policy audit MUST pass. It inspects
active Agent scratch provenance for any script that targets the workspace and
writes, rewrites, renames, or deletes any workspace content during the
documentation transaction. This is intentionally broader than a filename or
Markdown check: a helper that writes one line, a generated JSON report, or a
source scaffold is still script-authored work. A finding named
`script_authored_document_detected:*` is a hard BLOCKED result and cannot be
offset by a structural CODE_BLOCK_GATE PASS. Re-author the affected files with
native Agent file tools and preserve the audit finding in the repair record.
The audit also reads recent AGY transcript command receipts, so an inline
`python -c`, PowerShell, Node, shell-redirection, copy, move, or delete
command that writes workflow artifacts is treated as script-authored work.
Read-only parsing, validation, hashing, gate execution, and evidence collection
commands remain permitted.

The Agent MUST not create a scratch repair script, even temporarily. Use the
native file editor against the actual artifact. Run the audit after every
authoring turn and before each gate; if it fails, stop the repair loop and
remain `BLOCKED` until the affected artifact is natively re-authored.

Before opening the Master or any phase file for writing, create a reasoning
ledger from the complete upstream artifacts. For a new multi-boundary project,
the ledger must explicitly cover all bootstrap surfaces, not only the first
implementation slice:

- Backend: module and dependency lock, executable entrypoint, configuration,
  domain types, database driver/connection, schema migrations, repositories,
  application services/use cases, workers/schedulers/probers, DTOs, Fiber
  routes/handlers/middleware, error responses, shutdown, and unit/integration
  tests.
- Frontend: package lock, `index.html`, compiler and bundler config, Tailwind
  and PostCSS config, local font assets/manifest, app entrypoint, hash router,
  API client, shell/navigation, every screen and route from the requirements,
  custom input/textarea/select/checkbox/radio controls, custom alert/confirm/
  prompt dialog host, loading/empty/error states, and UI/E2E tests.
- Desktop/Wails: Wails manifest, build/embed entrypoint, lifecycle and context
  cancellation, bindings, web/server bridge, system tray/menu/notifications,
  graceful shutdown/restart, and desktop tests.

This is a conditional surface checklist, not a fixed product architecture.
The Agent must add or remove rows only by reasoning from the actual request and
approved decisions. Every row gets an exact target path, owner, family,
small-feature, phase, block ID, test ID, and evidence path before prose is
written. The hierarchy and phase count are derived from dependency cohesion
and ownership, never chosen to minimize document length.

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
> Blueprint MUST compute affected language matrices, preserve the complete implementation surface, and bind policy SHA-256 hashes in the Blueprint frontmatter. Blueprint document length is never a completeness gate. Every physical product source file MUST be planned and implemented at no more than 500 lines. This source-file limit MUST cause a split by responsibility when exceeded; it MUST NOT be used to truncate or omit Blueprint code blocks.
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

## 1.0 Repository-First Blueprint Output

The Blueprint engine MUST write the complete artifact set into the active
workspace before requesting any approval or reporting readiness. The canonical
output is repository-relative and follows this shape:

```text
docs/features/<family>/
  README.md
  specifications/<slug>_requirement_specification.md
  brainstorming/<slug>_brainstorming.md
  roadmaps/<slug>_roadmap.md
  plans/<slug>_plan.md
  blueprints/<slug>_master_blueprint.md
  blueprints/<small-feature-or-phase>_blueprint.md
  questions/Q<nn>_<slug>.md
```

The actual family, small-feature, and phase set is derived from scope and may
contain any number of units. The master and every phase file MUST be physical
files under this tree, listed in the run artifact index, and verified by
read-back before approval is requested. An IDE brain file, external
`implementation_plan.md`, chat code block, screenshot, or self-reported PASS
is supplemental only and never satisfies the Blueprint contract.

For a greenfield request, Blueprint generation MUST also persist the complete
empty-repository bootstrap contract, directory tree, dependency manifests,
configuration boundaries, route/screen inventory, backend capability matrix,
data model and migrations, Wails/systray lifecycle, local font and asset
manifest, custom control/dialog/loading behavior, failure/recovery paths, and
real E2E acceptance evidence requirements. A short scaffold summary or a few
representative snippets is `CODE_BLOCK_GATE: BLOCKED`.

If any required artifact cannot be written or read back, the engine MUST stop
with `BLOCKED: ARTIFACT_PERSISTENCE_REQUIRED`; it MUST NOT advance based on an
external plan or claim that the documentation is complete.

### Non-Negotiable Agent Execution Checklist

The following is the minimum authoring transaction for every large feature or
greenfield request. Treat it as an executable checklist, not as review advice:

1. Read the complete Requirement, Roadmap, and Plan artifacts and copy their
   phase inventory and file-impact map into an in-memory delivery inventory.
2. Derive the real delivery tree from independent ownership boundaries. A
   greenfield request spanning backend, frontend, database, and desktop/Wails
   MUST materialize a Master plus separate `backend`, `frontend`, and `wails`
   family artifacts, with further small-feature directories whenever a family
   has more than one cohesive delivery unit. The exact count remains an Agent
   decision; a Master-only result is never valid for this scope.
3. Use `templates/blueprint-template.md` and
   `templates/phase-blueprint-template.md` as schemas. Copy their required
   headings literally, including `And` and `Section 10: Blueprint Readiness
   Assessment And CODE_BLOCK_GATE`; do not replace them with translated,
   abbreviated, or `&` headings. Use a literal `File` column and literal
   `Code Block IDs` column in every file matrix so machine validation can read
   the table.
4. Materialize every planned concrete file exactly once. For every row, emit
   one adjacent metadata-bearing `full-file` block containing the complete
   copy-ready file. Wildcards, grouped paths, excerpts, signatures, stubs,
   pseudocode, and representative samples are forbidden. Maintain a
   bidirectional row/block ledger while authoring; do not invent a PASS count.
   For a greenfield cross-layer application, derive and enumerate the bootstrap
   surfaces before writing any phase: language/dependency manifests and locks,
   entrypoints, runtime configuration, database connection plus migration,
   domain/application/delivery boundaries, API routes and DTOs, frontend entry
   point and router, every requested screen/state, design-system controls,
   loading/dialog/error surfaces, desktop lifecycle/tray integration, and local
   asset/font manifests. A stack name in prose is not coverage. Each discovered
   surface becomes a concrete inventory row, an owning family/small-feature/
   phase, a full-file block, a test, and retained evidence.
5. Before any approval question, run the canonical validation command against
   the Master and recursive phases, read its JSON result, repair every finding,
   and run it again. A strict gate-only result is insufficient. Approval is
   forbidden until the runtime result is exactly `status=APPROVAL_READY`,
   `score=100`, with an empty findings list and a strict recursive gate PASS.
6. Write `Internal Review Evidence` last, copying the actual result paths,
   hashes, decision, and findings. If the result is missing, stale, BLOCKED, or
   NOT_RUN, leave the artifact in draft/needs-changes state and continue the
   repair loop; never ask the owner to approve it.
7. Before asking for approval, materialize the complete implementation blocks
   into an isolated validation workspace and have the Agent run the applicable
   language checks there. This is an Agent verification step, not a script
   deciding architecture: Go module/test compilation, frontend typecheck and
   production build, schema validation, and any required desktop build must
   use the exact materialized files. Repair the Blueprint natively when a
   check fails. Do not approve a block set that only becomes buildable after
   the implementation writer edits its files.
8. For a cross-layer greenfield request, phase files MUST be written under the
   physical tree `blueprints/<family>/<small-feature>/<phase>.md` (or
   `blueprints/<family>/<phase>.md` only when that family is demonstrably small).
   The master remains at `blueprints/<master>.md`. Do not place all phases beside
   the master, and do not use a flat phase list as a substitute for family
   ownership. Before validation, read back the directory tree and confirm every
   phase frontmatter contains matching `family_id`, `small_feature_id`, and a
   local `phase_id: P01`, `P02`, ... sequence.

Do not modify a project-local quality-gate configuration to manufacture a
passing result. Configuration changes are not a substitute for missing phase
artifacts, coverage rows, or complete file blocks.

The declared phase count in a master file is only an assertion to validate; it
does not materialize phase artifacts. Before requesting Blueprint approval, the
Agent MUST discover the actual family/small-feature/phase files on disk and
prove that every declared delivery unit exists with its own complete contract.
If a blocking owner decision is unresolved, the Blueprint remains a draft or
`CLARIFYING` artifact and approval cannot be requested, regardless of the
Agent's readiness score.

Before writing any review summary, the Agent MUST complete this materialization
transaction in order:

1. Build the concrete delivery inventory from the Requirement, Roadmap, and
   Plan, including every source, configuration, schema, migration, UI, test,
   asset manifest, command, route, capability, and runtime boundary.
2. Derive the recursive `family/small-feature/phase` tree from that inventory.
   For a cross-layer greenfield request, backend, frontend, desktop/Wails, and
   any other independent architecture boundary MUST have their own nested
   phase artifacts. A master-only document is invalid.
3. Write and read back the Master and every phase file. For every concrete file
   row, write exactly one metadata-bearing complete full-file block in the
   Master or its owning phase. A block ID, signature, excerpt, pseudocode, or
   representative sample without the full file is not materialization.
4. Run the recursive Blueprint validator and strict code-block gate against the
   files on disk. If any phase, row, block, interface, coverage mapping, or
   preserved diagram is missing, repair the artifact set and repeat from step
   3.
5. Run the full approval-readiness validation loop after the strict code-block
   gate. A strict gate result by itself is insufficient. The Agent MUST invoke
   `BlueprintAutoValidationService.validate_for_approval` (or the canonical
   document-validation command that invokes it) against the Master and the
   recursively discovered phase artifacts. The returned `APPROVAL_READY` is
   the only valid pre-approval result. `CODE_BLOCK_GATE: PASS` with runtime
   validation `BLOCKED`, `NOT_RUN`, or an unavailable result MUST remain
   `BLOCKED` and MUST NOT open an owner approval prompt.
6. Only after machine validation returns its decision may the Agent populate
   Internal Review Evidence and ask for Blueprint approval. The Agent MUST NOT
   author PASS, READY, or REVIEW_PASSED from its own narrative.

## 1.1 The 5 Pillars of Technical Blueprint Excellence (MANDATORY STANDARDS)

## 1.2 Mandatory Blueprint Generation Contract

This contract is autonomous. The Agent MUST execute it after reading the
upstream artifacts; completeness MUST NOT depend on the user repeating these
rules in the request. Prompt text supplies product intent and constraints only.
The Agent is responsible for detecting greenfield scope, preserving every
constraint, deriving the recursive hierarchy, materializing every phase, and
running the repair loop until the deterministic validators pass or return an
exact blocker.

The Blueprint is a delivery contract for the whole requested change. It is not
a summary of the architecture and it is not a list of suggested files. Before
writing the Blueprint, the Agent MUST build a normalized inventory containing
every user capability, acceptance criterion, non-functional constraint,
runtime boundary, data store, UI state, external dependency, test scenario,
and rollback action found in the upstream artifacts and the user request.

The Agent MUST derive complexity from that inventory and MUST NOT default to a
single Blueprint or a fixed number of phases:

| Derived signal | Split trigger |
|---|---|
| Capabilities | More than 3 requires a split; more than 7 requires at least 3 phases |
| File families | More than 2 requires a split; more than 4 requires at least 3 phases |
| Implementation tasks | More than 5 requires a split; more than 10 requires at least 3 phases |
| Architecture boundaries | Any cross-layer change requires a split |
| Explicit specialist lanes | One phase per explicitly independent lane, subject to dependency ordering |
| Blueprint file size | Optional context/readability signal only; never a pass/fail rule and never a reason to omit implementation detail |

The final phase count is the maximum applicable trigger, never a hard-coded
`4`. The output contract is:

Blueprint files may be any length required to preserve a coherent, executable
contract. The Agent MAY split a document only for a meaningful ownership,
dependency, review, or context boundary. It MUST NOT split mechanically to
satisfy an arbitrary line count, and MUST NOT remove or summarize code blocks to
make a document shorter. The Master remains a complete index and coverage
contract, while detailed implementation blocks belong in their owning phase
when that is the coherent boundary. A size note is optional and informative;
its absence MUST never block approval.

1. Always write one master Blueprint containing the complete scope, all
   requirements, all cross-phase dependencies, the complete data-flow and
   sequence diagrams, and the Feature Coverage Matrix.
2. When the derived count is greater than one, write exactly the required
   phase sequence inside each affected delivery unit. The artifact layout is
   hierarchical: `Master -> Family -> Small Feature -> Phase`. Family names
   are derived from real architecture boundaries (for example `backend`,
   `frontend`, `wails`); a family may contain direct phases only when it is
   small enough, otherwise it MUST be divided into named small-feature
   directories before phases are created. Phase IDs are local to each
   `family/small-feature` (`P01`, `P02`, ...); the path and frontmatter family
   IDs disambiguate repeated local phase numbers. Block IDs remain globally
   unique across the complete artifact set. Each phase MUST have its own scope,
   file matrix, implementation-ready code-block inventory, test matrix,
   evidence paths, rollback, and explicit `NO-GO` conditions. Never invent a
   fixed number of families, small features, or phases.
   The first phase in every `family/small-feature` directory MUST be `P01`;
   numbering from another directory is not a valid substitute. A global phase
   number may be shown as an informational field, but it MUST NOT replace the
   local sequence used by the validator.
3. The master Feature Coverage Matrix MUST map every requirement and
   acceptance criterion to a phase, concrete file, code-block ID (or an
   explicit `NOT_APPLICABLE` reason), test ID, and retained evidence path.
   A requirement that appears only in prose is uncovered. The validator MUST
   cross-check every explicit `FR-*`, `NFR-*`, `AC-*`, `G-*`, and `US-*` token
   found in the artifact against a non-placeholder coverage row.
4. The File-by-File Change Matrix MUST contain one row per concrete file. A
   directory, wildcard, or vague group is not a file. Every source row MUST
   specify operation, layer, owner, imports, exports, exact signatures,
   projected physical lines, language profile, build/lint/typecheck/test
   commands, code-block IDs, and acceptance-test IDs.
   `Code Block IDs` is a mandatory column, not a prose hint. Every source,
   config, schema, migration, UI, test fixture, and asset-manifest row MUST
   reference at least one implementation-ready block in the master or its
   owning phase. A file listed without a real block is `CODE_BLOCK_GATE:
   BLOCKED`; the Blueprint MUST NOT be submitted for approval.
   For greenfield work, the Agent MUST enumerate every concrete file required
   to make the repository build and run, including entrypoints, manifests,
   configuration, migrations, adapters, handlers, routes, workers, DTOs,
   frontend components/views/stores, desktop bindings, assets, and tests.
   A directory tree, package summary, or representative sample does not count
   as file materialization. Before review, the Agent MUST perform a bidirectional
   audit: every matrix row maps to exactly one full-file block, and every block
   target maps back to exactly one matrix row and owning phase.
   Each physical source/config/test file MUST declare `projected_lines <= 500`
   and its implementation-ready block MUST contain no more than 500 lines.
   When a responsibility would exceed the limit, the Agent MUST split it by
   responsibility inside one family-name directory, define one facade,
   barrel, or aggregate entry for outside imports, and map every extracted
   file to its own full-file block, test IDs, and evidence. A single oversized
   `App`, `handlers`, `repository`, or `service` file is `BLOCKED`.
5. Section 4 MUST contain both a happy-path and failure/recovery Mermaid
   diagram. The sequence diagram is part of the master contract and MUST be
   preserved when code blocks are repaired or phase documents are split.
6. For a new-project or project-initialization request, add a Project
   Initialization Coverage Matrix. It MUST map each requested stack/runtime
   obligation (backend, frontend, database, desktop shell, assets, controls,
   dialogs, loading, and tooling) to scaffold files, code blocks, tests,
   commands, and retained evidence. Set `project_initialization: true` in the
   master frontmatter so the runtime validator can enforce this matrix even
   when a stack name is abbreviated. Installed Go/Node/Wails tools do not count
   as product implementation.
   Each obligation must have its own non-placeholder row; a single generic
   "scaffold" row is insufficient.
   The Master MUST also contain these additional machine-auditable matrices
   whenever their surfaces exist: `Greenfield Completeness Matrix`, `Test
   Scenario Coverage Matrix`, `Screen And Route Coverage Matrix`,
   `Mobile-First Visual Coverage Matrix`, and `Backend Capability Coverage
   Matrix`. Every row MUST name concrete files, code-block IDs, executable
   test IDs, and retained evidence paths. A stack summary, a route list, or a
   test label without a file, block, command, and binary assertion is not
   coverage.
   `Screen And Route Coverage Matrix` MUST give every feature route its own
   page/view file and full-file block when the route has distinct behavior;
   `App.svelte` or another shell file cannot represent multiple feature pages.
   `Backend Capability Coverage Matrix` MUST map each capability through its
   endpoint/command, DTO/schema, persistence operation, producer, consumer,
   error contract, and test. `Test Scenario Coverage Matrix` MUST include the
   real entrypoint, fixture/setup, executable command, binary assertion, and
   evidence path. `Mobile-First Visual Coverage Matrix` MUST record 375/390,
   768/820, and 1440/1920 behavior plus loading, empty, error, focus, and
   touch-target assertions when UI exists.
   The Master must also contain an exact **Greenfield Repository Bootstrap
   Contract** with an empty-repository baseline, complete target directory
   tree, ordered bootstrap commands, and initial dependency/lock manifests.
   Each phase must contain a Phase Entry And Exit Contract, an owned directory
   tree, and a Full-File Delivery Contract. A phase file that only summarizes
   work or contains a few representative snippets is `CODE_BLOCK_GATE:
   BLOCKED`, even when every listed row has an ID.
7. The Agent MUST run the deterministic Blueprint validation loop after every
   generation or repair. A checklist claiming `PASS` without validator output,
   hashes, and retained evidence is invalid.
   Internal Review Evidence MUST be written only after the validator has run.
   The Agent MUST copy the machine decision and blocking findings into the
   evidence section; it MUST never author `CODE_BLOCK_GATE: PASS` from prose,
   block count, document length, or its own confidence.
   An agent-authored `status: APPROVED` or `status: FROZEN` field is never
   owner approval; it remains rejected until the scoped runtime approval
   record exists. Blueprint generation must stop at approval request and must
   not invoke implementation or dependency installation.
 8. The strict gate MUST run against the complete recursive artifact set
   (master plus every family, small-feature, and phase Blueprint), not the
   master alone. It MUST reject missing phase
   blocks, unknown block IDs, duplicate block IDs, orphan block targets, and
    block/file mismatches. `PASS` with `test_status: NOT_RUN` means only that
    the declared blocks are structurally valid; it never means product runtime
    E2E passed.
 9. Every phase MUST contain an `Implementation Task Contract` modelled on a
    fresh-agent handoff. Each task is the smallest independently testable unit,
    and MUST declare exact files, responsibility, dependencies, consumed and
    produced interfaces, a failing test or executable verification first, the
    implementation block(s), the green verification command, expected binary
    output, and rollback. A task that says only "implement", "add validation",
    or "write tests" is incomplete. The Agent MUST split a task again when a
    worker would need to invent a file, signature, schema, error, state, or test
    to complete it.
    A phase is incomplete when any owned file is represented by a signature,
    excerpt, pseudocode, or prose instead of a complete copy-ready file block.
    Large backend surfaces MUST be decomposed by responsibility (for example
    domain, persistence, probing, scheduling, ingestion, delivery, runtime,
    observability, and verification) and the phase set MUST cover each
    responsibility. The Agent MUST not collapse an entire backend into one
    `core` phase merely because a short scaffold can be written.

The repair loop is surgical: identify exact failed fields, repair only those
fields, rerun the same validator, and assert that all previously valid
sections, especially Data Flow and Sequence Diagram, remain present. Deleting
or replacing valid sections to make a code-block gate pass is a `NO-GO`.

### Autonomous Surface Completeness Contract

The Agent MUST derive product surfaces from the upstream Requirement,
Roadmap, and Plan artifacts. These rules belong to this skill and MUST NOT be
outsourced to a user prompt, a magic phrase, or a requested phase count.

For a greenfield request with a web/UI surface, the Master MUST include a
`Screen And Route Coverage Matrix`. Every route or screen named upstream must
have its own row (or an explicit justified composition row) containing the
route, screen responsibility, concrete implementation files, code-block IDs,
API/data contract, validation and loading/error/empty states, test IDs, and
evidence paths. CRUD forms, detail/history/metrics views, incident views,
settings, shell/tray surfaces, not-found, and failure states are separate
surfaces unless the matrix explains their complete composition.
When the matrix has three or more routes, feature routes MUST have concrete
route/view files and matching implementation blocks. Do not hide multiple
feature screens inside one root shell file; use an explicit composition row
only when the shell genuinely owns the complete view behavior and the matrix
records that fact with its own tests and state contracts.

For a greenfield request with a backend or cross-layer runtime, the Master
MUST include a `Backend Capability Coverage Matrix`. It MUST contain separate
rows for domain/model validation, persistence/schema/migrations and
repositories, application services/use-cases, delivery/API/handlers, runtime
workers/schedulers/integrations when present, observability/history/events
when present, and verification fixtures/tests. Each row must name concrete
files and blocks, data/API contracts, tests, and retained evidence. A single
`routes.go`, `sqlite.go`, or `backend scaffold` row is not sufficient.

The Agent MUST make the phase split match the materialized delivery units:
large backend and frontend surfaces are recursively divided into family,
small-feature, and local phases. A phase may not hide unlisted files or
delegate missing screens/capabilities to implementation-time inference.

When a web/UI surface exists, the Agent MUST load and apply the repository's
`frontend-design` Skill before authoring frontend Blueprint blocks. It MUST
read that Skill's mandatory UX reference, use its Mobile -> Desktop -> Tablet
build order, and persist the resulting design decisions as a testable design
contract in the Blueprint. Merely naming `frontend-design` in source-artifact
provenance is not use. Missing page-level layout, responsive, interaction,
accessibility, loading, empty, and error acceptance rows is `BLOCKED`.

### Superpowers-Style Executability Contract

The objective of a Blueprint is that a fresh implementation Agent can execute
it without recovering missing design from chat history. Therefore the Agent
MUST write implementation tasks in this order:

1. Establish the exact target file tree and one responsibility per file.
2. Define typed interfaces between neighboring tasks, including imports,
   exports, request/response types, persistence schema, error codes, timeouts,
   retries, and ownership.
3. Define the real failing test or verification action and the command that
   must fail before implementation.
4. Provide the complete target-file code block, not a representative excerpt.
   Every source/config/schema/UI/test file row MUST use
   `implementation_ready: true`, `full_file: true`, and
   `block_scope: full-file`; binary assets use an explicit asset manifest and
   generated package-manager lockfiles use a generated-manifest contract.
   The metadata MUST be literal adjacent lines immediately before the fence,
   using this exact shape with a globally unique block ID:

   ```text
   id: CB-BE-001
   language: go
   file: internal/domain/entity/target.go
   operation: create
   symbol: Target
   implementation_ready: true
   block_scope: full-file
   full_file: true
   ```

   The fence language and `language` field MUST resolve to the same strict
   profile. The `file` value MUST be repository-relative and MUST match one
   matrix row after slash normalization.
5. Define the exact command that proves the task works after implementation,
   with a binary expected result and retained evidence path.
6. Run a spec-compliance review and a code-quality review for each task before
   advancing to the next task. Any missing or uncertain item reopens the task
   and blocks the phase.

The plan and Blueprint are a transitive contract: every capability maps to a
task, every task to concrete files, every file to a complete code block, every
block to a test, and every test to executable evidence. A block count, a
passing text parser, or a high readiness score cannot substitute for that
chain.

#### Non-text Assets And Generated Locks

Binary assets (`.woff2`, `.woff`, `.ttf`, `.otf`, images, and icons) MUST never
be emitted as text, a one-line fake file, or a `full-file` block. Use
`language: asset`, `block_scope: asset-manifest`, and `full_file: false`. The
manifest MUST contain the real source, destination, inclusion rule, immutable
SHA-256, and deterministic fetch or vendoring command. If the source bytes are
not available to verify, leave the asset `BLOCKED`; never invent a checksum.

Generated package-manager locks (`go.sum`, `package-lock.json`,
`pnpm-lock.yaml`, `yarn.lock`, `Cargo.lock`, and equivalent files) MUST never
be hand-authored from guessed checksums. Use `language: generated-manifest`,
`block_scope: generated-manifest`, `full_file: false`, `operation: generate`,
the exact generator command, and post-generation hash/consistency evidence.
The implementation Agent creates the lockfile by running that command. A
text/full-file substitute is a hard gate failure.

### Agent-Authored Reasoning And Script Boundary

The Agent owns all work that requires product or architecture reasoning. It
MUST write the decision ledger, coverage matrices, task contracts, interfaces,
file contents, diagrams, and verification design through its native document
editing tools. It MUST NOT generate those artifacts with Python, PowerShell,
JavaScript, templates, bulk string emitters, or ad-hoc scripts. Scripts are
allowed only for deterministic, non-interpretive work such as listing files,
hashing, parsing, linting, schema validation, gate execution, and collecting
retained evidence. A generator script that invents or emits Blueprint prose or
implementation code is a `NO-GO` process violation even if the resulting files
appear complete.

Before the approval question, the Agent MUST read back every phase and run the
canonical recursive gate. If the gate is not `PASS`, it MUST repair the
artifact with native editing and rerun the same gate. It MUST never copy a
self-authored `PASS` claim from a document into Internal Review Evidence.

The strict gate is only the first machine stage. Before any owner approval
question, the Agent MUST also run the canonical runtime approval-readiness
loop through `BlueprintAutoValidationService.validate_for_approval` (or the
repository command that invokes that service) against the Master and every
recursively discovered phase. The only acceptable pre-approval result is
`status=APPROVAL_READY`, `score=100`, and an empty findings list. A strict
`CODE_BLOCK_GATE: PASS` with runtime status `BLOCKED`, `NOT_RUN`, or missing is
still `NO-GO`; the Agent MUST continue the repair loop and MUST NOT ask the
owner to approve it.

The Master MUST use the literal headings `Feature Coverage Matrix`,
`Project Initialization Coverage Matrix`, `Screen And Route Coverage Matrix`
when UI exists, `Backend Capability Coverage Matrix` when backend exists, and
`Section 10: Blueprint Readiness Assessment And CODE_BLOCK_GATE`. Renaming a
matrix to a prose or upstream summary heading does not satisfy the contract.
Every phase MUST use the literal headings `Phase Scope`,
`File-By-File Change Matrix`, `Implementation-Ready Code-Block Inventory`,
`QA Verification Matrix`, and `NO-GO Conditions`, and must contain its full
file delivery and implementation task contracts. These checks are part of
artifact generation, not optional review advice.

The original Requirement Specification is the immutable scope floor for
repair. A repair may reorganize a Roadmap or Plan, but may not remove an
explicit route, screen, table, API capability, actor/use case, acceptance
criterion, or runtime constraint. The Agent MUST derive a requirement surface
inventory independently and reconcile it against the Master matrices. A
blueprint that passes only because its repaired Plan was made smaller is
`BLOCKED`.

For every linked Roadmap with a Phase Inventory, the Master MUST include an
**Upstream Delivery Unit Coverage Matrix**. Every upstream phase ID MUST map to
one distinct discovered phase Blueprint artifact, its family/small-feature
owner, concrete files, code blocks, tests, and evidence. A phase may not be
silently merged into another phase merely because the local Blueprint happens
to pass its own block checks. For every linked Implementation Plan, every
concrete source/config/schema/UI/test/asset path in its File Impact Map MUST be
materialized in the Master and an owning phase Blueprint with an implementation
ready block. Missing upstream phase or file materialization is a blocking
finding and requires another autonomous repair loop.

Pre-approval code-block checks are validation-only and MUST be labeled
`test_status: NOT_RUN`; they never prove that product code works. After
implementation, the Agent MUST run the real build, lint, integration, API,
browser, desktop, and visual E2E commands listed in the Blueprint against the
running product. Mock, dry-run, inferred, screenshot-only, or static-only
results MUST remain `NOT_RUN` or `BLOCKED` and cannot be promoted to `PASS`.
Before implementation, every QA row that represents runtime, API readiness,
browser, desktop, visual, or E2E behavior MUST be `NOT_RUN` or `BLOCKED`; a
`PASS` claim for those rows is rejected unless post-implementation evidence is
being validated by the separate verification workflow.

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
7. **Section 7: File-by-File Change Matrix** (Path, DDD Layer, `[NEW]`/`[MODIFY]`, Family Folder, Facade/Aggregate Entry, Imports, Exports, Exact Signatures, Projected Physical Size)
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
- **Projected Physical Lines** (informational estimate used for implementation planning and source-policy checks; it MUST NOT reject or truncate a Blueprint document)
- **Family-Folder Split Contract**: If the source architecture requires splitting a production file, all extracted files must live under one shared family-name directory and one facade/barrel/aggregate entry file must be defined for outside imports. This source-design rule is independent of Blueprint document length.

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

### CODE_BLOCK_GATE Branch And Depth Decision

Before authoring implementation material, record `blueprint_depth` as CONTRACT
or FULL and obtain the owner's choice. Use Branch A when the target source
exists: verify identifiers against the real file and add `verified from:
<path:line>`. Use Branch B when the source is absent: complete B1-B6 in the
canonical strict gate, including a runnable spike, real toolchain execution,
adversarial rejection tests, evidence table, and complete extraction. Keep the
Implementation Sequence prose-only; put all verified source in `Source -
verified` or a phase appendix. This separation prevents prose instructions
from hiding incomplete implementation material.

The Internal Review Evidence CODE_BLOCK_GATE row must state the chosen branch,
depth, executed commands and real results for Branch B, code-block count,
verified-marker count, public-unit count in the spike, public-unit count in the
Blueprint, and the exact statement `No section was written from memory`. The
two counts must match. Zero blocks, partial extraction, or a FULL spike without
a real entrypoint run is FAIL.

> [!CAUTION]
> **CODE_BLOCK_GATE — MANDATORY for every implementation-ready code block written into this Blueprint**
> Every non-trivial code block (function signature, struct definition, SQL schema, migration snippet, config schema, rule, or script) MUST be routed through `skills/strict-code-block-gate/SKILL.md`.
> 1. Add structured metadata immediately before each implementation-ready fenced block: `id`, `language`, `file`, `operation`, and `implementation_ready: true`.
> 2. Resolve the language through the strict profile registry. Missing, ambiguous, or non-strict profiles are `BLOCKED`.
> 3. Materialize validation-only snippets under `.agents/tmp/code-block-gate/<workflow-id>/`; never write product source as part of this gate.
> 4. Persist `code-block-gate.json` with `decision`, `blueprint_full_sha256`, `per_code_block`, `profile_results`, `materialized_scope`, and `test_status: NOT_RUN`.
> 5. A code block is **BANNED** from this Blueprint if it lacks metadata, uses placeholders, depends on guessed source identifiers, has no strict language profile, or cannot be mapped to the architecture boundary.
> 6. For project initialization, implementation-ready blocks represent complete physical files: add `full_file: true` and `block_scope: full-file` for source/config/schema/UI files. The gate checks content size against projected file lines. Binary assets use `language: asset`, `block_scope: asset-manifest`, `full_file: false`, and explicit source/destination/inclusion/checksum metadata. Generated lockfiles use `language: generated-manifest`, `block_scope: generated-manifest`, `full_file: false`, `operation: generate`, the exact package-manager command, and post-generation hash/consistency evidence.
> `NOTE`, `PENDING`, local-only checks, or legacy `UNLOCKED` wording in the Internal Review Evidence CODE_BLOCK_GATE row = automatic FAIL.

**Internal Review Evidence** — every generated Blueprint MUST include this table before submission for Architecture Approval:

```markdown
| Field | Evidence |
|---|---|
| Reviewer Roles | Architect / Reviewer / QA / relevant Specialist roles |
| Source Artifacts Reviewed | Plan, Brainstorming, Requirement Spec, active Skill, `AI_RULES.md` |
| Checklist — No Placeholders (TBD/TODO/etc.) | `PASS` / `FAIL` |
| Checklist — File-by-File Change Matrix | `PASS` / `FAIL` — every file listed with operation + responsibility |
| Checklist — Source Size Planning | `PASS` / `FAIL` — every touched source file lists honest projected physical size and any required source-level split; Blueprint document length is not scored |
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
   - **CHAT APPROVAL IS A BOUND FALLBACK ONLY.** An Agent MUST NOT self-declare bridge unavailability. When the runtime has returned `PROMPT_UNAVAILABLE` (or the host explicitly reports both structured prompt paths unavailable), a clear approval in the next user turn (`approve`, `approved`, `yes`, `continue`, or `ok`) is valid only if the exact pending request, gate, active work item, and Blueprint all match.
   - Valid evidence is native `ask_question` returning `Continue`, the fallback UI/CLI bridge returning `Continue`, or a bound chat fallback that is immediately persisted through `aiwf blueprint --path <path> --approve` and verified through its scoped approval artifact and command receipt.
   - Any chat approval without that pending-request and artifact-binding evidence is **NOT** valid.
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

## 13. Automatic Completeness & Evidence Contract

Every Blueprint generation MUST run the deterministic Blueprint validation loop
before approval. The loop MUST derive the phase count from actual capability,
file-family, task, cross-layer, and boundary complexity; never assume a fixed
number of phases. When a split is required it MUST emit one master Blueprint
and exactly the discovered phase Blueprints, with a Feature Coverage Matrix
mapping every requirement and acceptance criterion to a phase, file, code
block, test, and evidence.

The loop MUST validate the File-by-File Change Matrix against the repository,
including operation, target existence, anchor symbol, language profile,
projected physical size as planning evidence, and source boundary. Code-block repair MUST preserve
the complete `Data Flow And Sequence Diagram`; deleting it is `BLOCKED`.
Behavior evaluation MUST run for each selected Skill. Missing manifests are
reported as compatibility evidence, never silently treated as a behavioral
pass. Dry-run, mock, fake, inferred, static-only, or screenshot-only reports
cannot satisfy real runtime or browser acceptance criteria.

The canonical route is `aiwf verify --blueprint <path>`. Approval is allowed
only when it returns `APPROVAL_READY`, the strict code-block gate is `PASS`, all
coverage rows are satisfied or explicitly `NOT_APPLICABLE`, and runtime/browser
evidence is honestly marked `PASS`, `NOT_RUN`, or `BLOCKED`.

---

## 13. Forbidden Routing Guards (STRICTLY BLOCKED)

- `DRAFT / DESIGNING / CONTRACTS_DEFINING → IMPLEMENTATION` (BLOCKED)
- `UNAPPROVED PLAN → BLUEPRINT` (BLOCKED)
- `UNAPPROVED BLUEPRINT → IMPLEMENTATION` (BLOCKED)
- `FROZEN BLUEPRINT WITHOUT IMPLEMENTATION ENTRY PASS → IMPLEMENTATION` (BLOCKED)
- `BLUEPRINT → SOURCE_CODE_EXECUTION / TEST / GIT / RELEASE` (BLOCKED)
