---
name: plan-to-blueprint
command: blueprint
aliases:
  - design
  - architecture
category: workflow
tags:
  - blueprint
  - design
  - architecture
version: 3.2.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-09
description: Generate a production-grade Technical Blueprint (Markdown & JSON) from an approved Implementation Plan using a Memory-First strategy and the FEAT-XXX Feature ID format.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: none
  version: cached
  provider: optional
  usage: cached
---

# Skill: Plan to Blueprint (FEAT-XXX format)

## Purpose

Generate a production-grade Technical Blueprint (Markdown & JSON) from an approved Implementation Plan using a Memory-First strategy and the FEAT-XXX Feature ID format.

## Role

You are acting as a **Chief Software Architect**, **Senior Solution Architect**, and **Technical Reviewer**.

Your responsibility is to transform an approved implementation plan into a **production-grade Technical Blueprint** suitable for direct implementation by another AI or Senior Engineer.

---

# Objective

Upgrade the implementation plan into a production-grade Technical Blueprint. Do NOT merely transform the plan — act as an architect and reviewer to reduce uncertainty, analyze alternatives, evaluate risks, and enforce high architectural standards.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 3"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "plan-to-blueprint" --command "blueprint" --checkpoint 4 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 4 --step "Step Complete" --next-skill "blueprint-to-implementation" --next-command "implement"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.

## Multi-Agent Contract

Runs under the Multi-Agent Workflow. Respect agent ownership and handoff rules defined in [agents/](../../agents/) and [runtime/](../../runtime/).

---

# Input

```yaml
# Structure-mirroring rule (applies in ANY project, not just this repo):
# a feature's brainstorming and plan input may exist as either:
#   (a) semantic feature files: docs/features/<feature-family>/<stage>/FEAT-XXX_feature_slug_<stage>.md
#   (b) a multi-phase folder:   docs/features/<feature-family>/<stage>/master/FEAT-XXX_..._master_<stage>.md
#                              + docs/features/<feature-family>/<stage>/phase-NN-<phase-slug>/phase-<stage>.md
# Detect which shape the actual source_plan/source_brainstorming uses for THIS feature and mirror
# that same shape for the blueprint output — do not force multi-phase splitting onto a simple,
# single-phase feature, and do not flatten a genuinely multi-phase plan into one file.
source_brainstorming: docs/features/<feature-family>/brainstorming/FEAT-XXX_feature_slug.md   # or the (b) folder form above
source_plan: docs/features/<feature-family>/plans/FEAT-XXX_feature_slug_plan.md               # or the (b) folder form above
source_roadmap: docs/features/<feature-family>/roadmaps/FEAT-XXX_feature_slug_roadmap.md      # required for large or multi-phase features

workspace: auto

language: auto

tech_stack: auto

architecture: DDD + Clean Architecture (mandatory — see Step 5a)

output_path: docs/blueprints/                          # mirrors source_plan's shape — see Step 1
```

---

# Workflow

## Step 1 — Read Inputs
First detect the shape of this feature's plan: does `docs/features/<feature-family>/plans/` hold a canonical semantic feature file `FEAT-XXX_feature_slug_plan.md`, a legacy flat `docs/plans/FEAT-XXX_feature_slug_plan.md`, a former work-item folder, or a `master/` + `phase-NN-<phase-slug>/` folder tree? Use whichever exists as input, but all new Blueprint output must use the canonical semantic feature documentation contract.

- **Single-file shape**: read `docs/features/<feature-family>/plans/FEAT-XXX_feature_slug_plan.json` (fallback `.md`) and the matching `docs/features/<feature-family>/brainstorming/FEAT-XXX_feature_slug.md`. Legacy flat or former work-item input may be read if needed. Produce one blueprint for the whole feature (Step 5/Output Rules, single-file branch).
- **Multi-phase folder shape**: read `docs/features/<feature-family>/roadmaps/FEAT-XXX_feature_slug_roadmap.md` first and verify it has review result PASS, then read `docs/features/<feature-family>/brainstorming/master/FEAT-XXX_..._master_brainstorming.md`, every `phase-NN-<phase-slug>/phase-brainstorming.md` in Roadmap phase order, the mirrored `docs/features/<feature-family>/plans/master/...plan.json` (fallback `.md`), and each `phase-NN-<phase-slug>/phase-plan.json` (fallback `.md`) — a feature's requirements are split across these files, not contained in one document. Produce one Technical Blueprint **per phase** plus one master blueprint indexing all phases (Step 5/Output Rules, multi-phase branch). Never collapse a genuinely multi-phase plan into a single flat blueprint file, and never force a single-phase feature into an unnecessary master+phase split.

Either way, extract **Feature ID**, **Feature Name**, requirements, scope, constraints, and recommendations, as well as the **Roadmap Coverage Matrix** when present, **Traceability Matrix**, **Stakeholder Analysis**, **Data Flow**, **Open Decisions**, and **Risk Matrix** from the roadmap, brainstorming, and plan sources, reading the JSON form first when present for minimal token usage.

If a feature is large/multi-phase but the reviewed Roadmap is missing, STOP and return to `brainstorming`; do not generate the Blueprint.

---

## Step 2 — Read Project Memory
Consult the memory summaries, interfaces, and architecture layers.

---

## Step 3 — RAG Query
Query `project-rag-search` for existing patterns and dependencies.

---

## Step 4 — Targeted Source Inspection (if needed)
Inspect source files directly only if memory gaps remain.

---

## Step 5 — Generate Technical Blueprint
Produce the blueprint. It must include the YAML metadata header and the design specifications. Architect MUST directly inherit and reuse the architecture principles, dependency graph, data flow, migration strategy, traceability matrix, open decisions, and risk matrix from the brainstorming spec, focusing strictly on detailed code mutations and interface contracts without repeating high-level analysis.

### 5a. Mandatory: DDD + Clean Architecture layering
Every module the blueprint designs MUST be assigned to exactly one of these layers, and the blueprint must say which layer each class/module belongs to:
- **Domain**: pure entities, value objects, domain errors/exceptions. Zero framework or I/O dependencies (no HTTP, no DB driver, no SDK import).
- **Application**: use-cases/services that orchestrate domain logic. Depends only on Domain and on interfaces it declares (ports) — never on a concrete infrastructure type.
- **Infrastructure**: concrete implementations of the ports declared in Application (DB access, external SDK/IPC clients, file I/O, HTTP clients).
- **Interface/Presentation**: REST/WS/CLI handlers. Thin — parse input, call into Application, format output. No business logic here.

Dependencies point inward only: Interface/Infrastructure → Application → Domain, never the reverse. State this explicitly per module in Section 3, and reflect it in the Section 2 folder structure using whichever layering convention fits the target language/framework — e.g. `internal/domain|application|infrastructure|interfaces` (Go), `domain|application|infrastructure|api` (Python/FastAPI), `Domain/Application/Infrastructure/Api` (C#/.NET), `src/domain|application|infrastructure|presentation` (TS/Node), or Android/iOS package-per-layer conventions. If the target codebase already has an established layering convention, follow it instead of inventing a new one — check it first (Step 2/3).

### 5b. Mandatory: near-code depth, written as literal code — not prose describing code
"Do NOT implement business logic" (see Constraints) means the blueprint must stop short of final, compilable production code — it does NOT mean staying abstract, and it does NOT mean describing the code in prose bullet points instead of writing it. **The standard is literal, fenced, real-syntax code blocks in the target language — this is the single most load-bearing rule in this section, added after a real corrective pass where a blueprint written as prose bullets ("- **Fields**: `x: type`...") had to be entirely rewritten as actual code.** For every class/struct/component/module in Section 3 and every function in Section 4/11:

- Write a real fenced code block in the target language (` ```go `, ` ```python `, ` ```csharp `, ` ```svelte `, ` ```js `/`ts`, etc.) containing: the real package/import/namespace declaration; the real type/struct/class/component declaration with **every field given its own one-line doc comment directly above or beside it** (`// field is ... ` / `# field is ...` / JSDoc `/** ... */`, whichever the language's own convention is); and the real method/function signature — every parameter typed, the exact return/error type(s) — followed by a body. The body is either a stub that compiles (e.g. Go's `{ return nil, nil }`, Python's `pass`, a Svelte handler's `{}`) or, when the method is non-trivial, the body **is itself the numbered algorithm, given as line comments inside or immediately above the function** (`// 1. validate X`, `// 2. if Y, return err`, `// 3. call service.Z(...)`) — never as a separate prose bullet list living below/outside the code block.
- **Anti-pattern — do NOT do this**:
  ```markdown
  - **Fields**: `name: Name`, `payload: interface{}`, `requestedAt: time.Time`
  - **Public Methods**: `NewCommand(name, payload) (*Command, error)` — validates name is non-empty, returns ErrEmptyCommandName if not.
  ```
- **Correct pattern — do this instead** (real Go shown; apply the equivalent real syntax for whatever language this blueprint targets):
  ```go
  package command

  // Name is a dot-namespaced IPC command identifier, e.g. "app.ping".
  type Name string

  // Command is the domain value object for one command invocation request.
  type Command struct {
      name        Name          // dot-namespaced command identifier
      payload     interface{}   // arbitrary JSON-serializable request body; nil if none
      requestedAt time.Time     // construction time, for latency measurement
  }

  // NewCommand constructs a Command, validating name is non-empty.
  // 1. Trim whitespace from name; if empty, return ErrEmptyCommandName.
  // 2. Construct and return &Command{name, payload, time.Now()}.
  func NewCommand(name Name, payload interface{}) (*Command, error) { return nil, nil }
  ```
- This applies identically to every language — a Svelte component's `<script>` block with real `export let propName = default; // doc comment` prop declarations and real `function handlerName(args) { // 1. ...\n // 2. ... }` handlers is the exact same standard as the Go example above, just in Svelte/JS syntax. A Python class needs a real `class Foo:` with typed `__init__` params and real (if stubbed) method bodies with docstrings/comments carrying the numbered steps. There is no language this rule doesn't apply to.
- File-by-file and line-level detail is the bar: if a reader could not tell, from the blueprint's own code blocks alone, which file to open and roughly which lines to write, the blueprint is not detailed enough yet — and if the detail exists only as prose describing what the code should contain rather than as the code itself, it does not meet this bar regardless of how thorough the prose is.

### 5c. File splitting is allowed and expected at this depth
Given the depth required by 5b, a single `phase-blueprint.md` will often become too large. This is expected — split it into multiple companion files within the **same phase folder**, for example:
- `phase-blueprint.md` — index/overview: phase scope, requirement traceability, links to every companion file below, one-paragraph summary of each.
- `phase-blueprint-domain-layer.md`, `phase-blueprint-application-layer.md`, `phase-blueprint-infrastructure-layer.md` — one per architecture layer, OR
- `phase-blueprint-<module-name>.md` — one per major module, whichever split reads more naturally for that phase.

Only split when the single-file version would genuinely be unwieldy — don't split arbitrarily for a small phase. Every companion file must be linked from the index file so nothing is orphaned. The master blueprint may similarly gain companion files (e.g. a shared domain model doc) if truly needed for size, indexed the same way.

```markdown
<!-- File path (single-file shape):   docs/features/<feature-family>/blueprints/FEAT-XXX_feature_slug_blueprint.md -->
<!-- File path (multi-phase shape):   docs/features/<feature-family>/blueprints/phase-NN-<phase-slug>/phase-blueprint.md -->
<!-- File path (multi-phase master): docs/features/<feature-family>/blueprints/master/FEAT-XXX_..._master_blueprint.md -->

---
feature_id: FEAT-XXX
feature_name: Human Readable Name
status: reviewed
stage: blueprint
created_at: [YYYY-MM-DD]
updated_at: [YYYY-MM-DD]
previous_artifact: [relative path to the matching plan file/folder — mirror the shape from Step 1]
next_artifact: [Implementation (Source Code)](../) # or the relevant implementation root for this stack
---

# Technical Design Blueprint & Implementation Contract – [Human Readable Name]

## 0. Baseline Context & References
- **Memory Baseline**: [State and confidence levels retrieved from project memory summary]
- **RAG Query Summaries**: [List of vector search query results, matched files, and key findings]
- **Inspected Source Files**: [Target files inspected directly, including line references]

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation (Create/Modify/Delete/Rename) | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `relative/path/to/file` | `[NEW | MODIFY | DELETE]` | [...] | [...] | [...] |

## 1A. Roadmap Preservation Matrix (Required for large/multi-phase features)
| Roadmap Capability | Roadmap Phase | Plan Task | Blueprint Contract | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| [Capability] | Phase N | Task N.N | Section/File contract | [x] |

## 2. Target Folder Structure
Must show the DDD/Clean Architecture layer each new directory belongs to (Domain / Application / Infrastructure / Interface), using the target language/framework's own layering convention (see §5a) — check the existing codebase first, only propose a new one if none exists.
```text
.
└── <layering root per target stack — e.g. internal/, src/, App/>
    ├── <domain layer dir>          # entities, value objects, domain errors — no framework/IO imports
    ├── <application layer dir>    # use-cases/services + the ports (interfaces) infrastructure implements
    ├── <infrastructure layer dir> # concrete adapters implementing application's ports
    └── <interface layer dir>      # REST/WS/CLI handlers — thin, delegate to application
    (exact directory structure, real file names, per the plan's File Change Plan)
```

## 3. Complete Class & Module Design
For each class/module, state its **Layer** (Domain/Application/Infrastructure/Interface) in one line, then give the class/struct/component itself as a **real fenced code block** per §5b — not the bullet-list shape below (that shape is shown here only to enumerate what the code block must contain; do not render it as prose):

- **Class / Module Name**: `...` — **Layer**: `[Domain | Application | Infrastructure | Interface]`
  - The fenced code block (§5b) must contain: the real package/import/namespace line; the struct/class/component declaration with every field typed and doc-commented inline; the constructor/factory signature; every public method's full real signature (every parameter typed, exact return/error type) with its body either a compiling stub or the numbered algorithm as line comments inside the body; every internal/private method at the same depth.
  - **Dependencies** (prose, outside the code block): [other modules/ports this depends on, and which layer they're in]
  - **Extension Points** (prose, outside the code block): [How subclasses/implementations can extend this]

Narrative fields (Responsibilities, Dependencies, Extension Points) stay as prose around the code block — only the class/struct/component/method definitions themselves must be literal code, per §5b's anti-pattern/correct-pattern example.

## 4. Detailed Interface Contracts
Same rule as §3: give the interface/API itself as a real fenced code block (the real signature, typed params, exact return/exception types — per §5b), then prose notes around it:
- The code block: full real signature in the target language, e.g. `def api_name(param1: Type1, param2: Type2 = default) -> ReturnType:` (Python) or the equivalent real syntax for whatever language this blueprint targets.
- **Validation Rules** (prose, outside the code block): [...]
- **Exceptions** (prose or inline in the code block's own doc-comment, per §5b): `ExceptionName` thrown under Z conditions
- **Compatibility Notes** (prose): [...]

## 5. Configuration Schema
- **Current Schema**: [...]
- **Target Schema**: [...]
- **Migration Rules**: [...]
- **Defaults & Validation**: [...]

## 6. Database & Storage Design
- **Tables**:
  - `table_name`: Columns, keys, nullability, constraints
- **Indexes**: Column mappings
- **Relationships / Constraints**: Foreign keys
- **Migration & Rollback Strategy**: SQL statements or scripts

## 7. Cache Architecture
- **Cache Keys**: Format and parameters
- **Invalidation Rules**: When cache is invalidated
- **TTL**: Time to live in seconds
- **Hash Strategy**: How keys are hashed
- **Provider versioning & stale detection**: [...]
- **Warmup & Cleanup**: [...]

## 8. Error Model
- **Exception Class**: `ExceptionName`
  - **Trigger Condition**: [...]
  - **Recovery Strategy**: [...]
  - **Retry Policy / Fallback**: Retry count, backoff, fallback behavior
  - **Logging Requirements**: Log level, context keys

## 9. Skill Integration Contracts
- **Skill Name**: `...`
  - **Before Hooks**: [...]
  - **After Hooks**: [...]
  - **Runtime Calls**: [...]
  - **Data Exchanged / Outputs**: [...]

## 10. CLI & Runtime Contracts
- **Command Syntax**: `python workflow_runtime.py subcommand --arg`
  - **Parameters**: Option names, types, constraints
  - **Output**: JSON or text output schema
  - **Exit Codes**: 0 (success), 1 (general error)
  - **Failure behavior**: [...]

## 11. Sequence Flows
- **Normal Execution Flow**:
  1. Client calls API...
  2. ...
- **Cache Miss Flow**:
  1. Check cache (miss)...
  2. Query Provider...
- **Provider Unavailable Flow**:
  1. Provider throws exception...
  2. Fallback to default...

## 12. Security & Safety
- **Workspace Boundary**: Only write to relative workspace paths.
- **Path Validation**: Do not allow escape sequences like `../` to write outside sandbox.
- **Write Restrictions**: Specify forbidden directories.
- **Rollback safety**: [...]

## 13. Complete Test Matrix
| Requirement ID | Test Type (Unit/Integration/Compatibility/Regression/Performance/Stress/E2E) | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Unit Test | `relative/path/to/test_file.py` | `api.py` | `self.assertEqual(...)` |

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `API` -> `api.py` -> `test_api.py` -> Verified -> Released.

## 15. File-Level Implementation Contracts
- **File**: `relative/path/to/file`
  - **Purpose**: [...]
  - **Owner**: [Architect / Coder / Reviewer / Verifier / Documentation / Runtime]
  - **Inputs / Outputs / Dependencies**: [...]
  - **Implementation Notes & Risks**: [...]

## 16. Internal Review Evidence
| Field | Evidence |
|---|---|
| Reviewer Roles | Architect / Reviewer / QA / QC / relevant Specialist roles |
| Source Artifacts Reviewed | Plan, Brainstorming, active Skill, `AI_RULES.md`, `document-compliance-assessment`, memory/RAG/source references |
| Checklist Result | PASS/FAIL rows with concrete section evidence |
| Failed Points | `None` or exact failed-point list |
| Revision Scope | `None` or exact sections revised |
| Re-review Count | `0` for first-pass PASS, otherwise number of repeated reviews |
| Document Compliance Score | `NN/100` |
| Relative Path Scan | PASS only when no `file:///`, `/Users/`, `/Volumes/`, drive-letter paths, or local absolute links exist |
| Final Result | `PASS` or `FAIL` |
```

---

# Output Rules

## Step 6 — Internal Blueprint Review Gate

Self-review the generated Technical Blueprint before requesting user approval.

Review checklist:
- The Blueprint covers every internally reviewed Plan task and every in-scope requirement without adding unrelated scope.
- For large/multi-phase features, the Blueprint covers every Roadmap capability, phase, dependency, and release slice without adding, dropping, or reordering phases.
- File-by-file analysis, implementation contracts, interfaces, data contracts, algorithms, validation rules, rollback, and test matrix are concrete and verifiable.
- The Blueprint includes real near-code signatures/structures where required by this Skill and contains no placeholders, vague tasks, or generic instructions.
- DDD/Clean Architecture layer ownership and dependency direction are explicit for every designed module.
- Traceability maps requirement -> plan task -> blueprint contract -> expected test.
- All paths are project-relative and artifact placement follows `AI_RULES.md`.
- `document-compliance-assessment` no-go conditions are not present.
- The Blueprint contains `Internal Review Evidence` with reviewer roles, source artifacts, checklist evidence, failed-point repair history, document-compliance score, and relative-path scan result.
- If the Blueprint touches UI/UX, frontend components, layout, spacing, typography, color, animation, icons, visual hierarchy, aesthetic styling, or design-system decisions, `frontend-design` has been used and the Blueprint includes its relevant constraints.

Rules:
- Do not request user approval until this review passes.
- Missing `Internal Review Evidence`, score below `95/100`, unresolved failed points, or relative-path scan FAIL means review FAIL.
- For large/multi-phase features, missing Roadmap Preservation Matrix or mismatch with `docs/features/<feature-family>/roadmaps/FEAT-XXX_feature_slug_roadmap.md` means review FAIL.
- If review FAILS, state the exact failed points and revise only those points.
- Repeat review/revision until PASS.
- Continue to the final user approval stop only after review passes.

## Step 7 — Final User Approval Stop

After the Blueprint review passes, present the Blueprint path(s), review result, remaining risks, and request approval through the runtime prompt bridge:

`aiwf prompt select --question "Approve this Technical Design Blueprint for implementation?" --options "Continue|Cancel" --default "Cancel"`

Then stop absolutely. A plain chat approval question is not valid unless the runtime prompt bridge is unavailable and the Agent explicitly reports that unavailability.

The Agent MUST end the turn and MUST NOT mark the Blueprint approved, inspect more files, run git, run tests, or implement code until the user explicitly approves through the runtime prompt bridge, or through fallback chat evidence only after prompt bridge unavailability is explicitly reported.

Mirror whichever shape Step 1 detected for this feature:

**Single-file shape** — create exactly two files (plus companions from §5c only if this one feature is unusually large):
1. `docs/features/<feature-family>/blueprints/FEAT-XXX_feature_slug_blueprint.md`
2. `docs/features/<feature-family>/blueprints/FEAT-XXX_feature_slug_blueprint.json`

**Multi-phase folder shape** — for each phase, create at minimum two files (see §5c for when to add companions):
1. `docs/features/<feature-family>/blueprints/phase-NN-<phase-slug>/phase-blueprint.md`
2. `docs/features/<feature-family>/blueprints/phase-NN-<phase-slug>/phase-blueprint.json`
3. Any companion `.md` files from §5c, each linked from `phase-blueprint.md`.

Plus one master blueprint indexing every phase:
1. `docs/features/<feature-family>/blueprints/master/FEAT-XXX_..._master_blueprint.md`
2. `docs/features/<feature-family>/blueprints/master/FEAT-XXX_..._master_blueprint.json`

First line of every Markdown file must be its own real path, e.g.:
```html
<!-- File path: docs/features/<feature-family>/blueprints/FEAT-XXX_feature_slug_blueprint.md -->
<!-- or: docs/features/<feature-family>/blueprints/phase-NN-<phase-slug>/phase-blueprint.md -->
```

The JSON file must conform to this schema:
```json
{
  "modules": [
    {
      "name": "...",
      "classes": [
        {
          "class_name": "...",
          "layer": "domain|application|infrastructure|interface",
          "fields": [{"name": "...", "type": "...", "purpose": "..."}],
          "responsibilities": ["..."],
          "methods": [
            {
              "name": "...",
              "parameters": [{"name": "...", "type": "...", "validation": "..."}],
              "return_type": "...",
              "error_type": "...",
              "body_steps": ["1. ...", "2. ...", "3. error path: ..."]
            }
          ],
          "lifecycle": "...",
          "state_ownership": "..."
        }
      ]
    }
  ],
  "configuration": {
    "schema": {},
    "defaults": {}
  },
  "database": {
    "tables": [],
    "growth_estimation": "...",
    "maintenance_strategy": "..."
  },
  "cache": {
    "keys": [],
    "ttl_seconds": 600,
    "invalidation_rules": []
  },
  "errors": [
    {
      "exception_class": "...",
      "trigger": "...",
      "recovery": "..."
    }
  ],
  "sequence_flows": [
    {
      "flow_name": "...",
      "steps": []
    }
  ],
  "integration_contracts": [],
  "cli_contracts": [],
  "implementation_contracts": [
    {
      "file_path": "relative/path/to/file",
      "owner": "Coder",
      "notes": "..."
    }
  ],
  "implementation_packages": [
    {
      "task_id": "Task 1.1",
      "module": "...",
      "read_set": [],
      "write_set": [],
      "dependencies": [],
      "implementation_notes": "...",
      "verification": "...",
      "rollback": "...",
      "expected_outputs": []
    }
  ],
  "tests": [
    {
      "requirement_id": "REQ-001",
      "test_type": "Unit Test",
      "target_file": "relative/path/to/test_file.py"
    }
  ],
  "traceability": [],
  "artifacts": []
}
```

---

# Constraints

- Do NOT write final, compilable production code (that is `blueprint-to-implementation`'s job). Per §5b, DO write complete signatures/struct fields and numbered pseudocode-level method bodies — the line between the two is "an implementer transcribes it" vs. "an implementer designs it."
- Do NOT skip sections.
- Do NOT collapse a genuinely multi-phase feature into one flat blueprint file, and do NOT force a single-phase feature into an unneeded master+phase split (see Step 1 / §5c) — mirror the shape the plan actually used.
- Every module/class MUST declare its DDD/Clean-Architecture layer (§5a) — a class with no stated layer is an incomplete blueprint.
- Keep naming consistent with project (from memory).
- **Do NOT create ADR files**. Only assess and recommend if they are required.
- **Mandatory Skill Skeleton**: If the blueprint introduces or creates a new skill directory under `skills/<skill-name>/`, it MUST also declare and generate a complete Skill skeleton in its proposed modifications. The skeleton MUST include: `skills/<skill-name>/SKILL.md` (containing Purpose, Public APIs, Workflow Integration, Configuration, Runtime Commands, Provider Strategy, Backward Compatibility, Usage Examples, Extension Points, Limitations), `skills/<skill-name>/scripts/`, and `skills/<skill-name>/tests/` (if executable). If the blueprint creates a new skill path but does not define the SKILL.md file, validation must fail and the blueprint must not be marked complete.
- **Run a self-review of the generated blueprint against the "Disallowed Outputs Validation" checklist and fix all violations before saving.**

---

# IDE Skill Hardening & Boundary Rules

## 1. Single Responsibility
Convert an approved Implementation Plan into a detailed Technical Blueprint, internally review it until PASS, then stop for final user approval. Once the blueprint output (single file, or every phase's `phase-blueprint.md` + companions + master index for the multi-phase shape) is generated under `docs/blueprints/`, do not move into implementation until the user approves.

## 2. Never Execute Next Phase
Do NOT invoke `blueprint-to-implementation` or `create-adr`. Only recommend.

## 3. Workspace Modification Policy
Only create or update the target Technical Blueprint file.

---

## Completion Contract

```text
Current Phase:
Phase 3 — Plan to Blueprint

Status:
Completed

Memory Confidence:
[High | Medium | Low]

Memory Documents Read:
[list]

RAG Queries:
[list of queries and key findings]

Source Files Inspected:
[list or "None — all context from memory"]

Generated Output:
[Single-file shape: docs/features/<feature-family>/blueprints/FEAT-XXX_feature_slug_blueprint.md (+ .json)]
[Multi-phase shape: docs/features/<feature-family>/blueprints/master/FEAT-XXX_..._master_blueprint.md (+ .json)
 + docs/features/<feature-family>/blueprints/phase-NN-<phase-slug>/phase-blueprint.md (+ .json, + companions if split per §5c)]

Recommended Next Skill:
[create-adr (if ADR Required = Yes) | blueprint-to-implementation (if ADR Required = No)]

Workflow Paused at Final Blueprint Approval.
Approval Method:
workflow_runtime.py prompt select
```

## Evaluation Criteria & Readiness Score (Scale 100)
Giai đoạn chỉ được qua cổng kiểm duyệt khi tổng điểm từ 95 trở lên và không vi phạm tiêu chí đường dẫn (đánh fail lập tức nếu vi phạm chính sách đường dẫn tuyệt đối).

| # | Tiêu chí đánh giá | Điểm tối đa | Điểm đạt | Điều kiện đạt đủ điểm & Ghi chú |
|---|---|---:|:---:|---|
| 1 | Tương thích đường dẫn | 30 | /30 | 100% đường dẫn trong mã nguồn, script, kết quả và tài liệu là đường dẫn tương đối hoặc đã được làm sạch. Không có URL tệp tuyệt đối, đường dẫn ổ đĩa, đường dẫn tuyệt đối của macOS hoặc Linux, mã xác thực hoặc log chứa đường dẫn tuyệt đối. |
| 2 | Build và chạy runtime thật | 20 | /20 | App, service, UI, CLI hoặc worker build lại thành công, runtime thật mở được, surface tích hợp thật sẵn sàng, và không còn tiến trình treo sau kiểm thử. |
| 3 | Kiểm thử runtime thật | 20 | /20 | Kiểm thử gọi vào runtime đang chạy qua surface thật phù hợp như IPC, API, UI, CLI, SDK, job queue hoặc service, không chỉ kiểm thử đơn vị hoặc phản chiếu. Luồng thành công chính, luồng lỗi hợp lệ, luồng hồi quy và dọn dẹp đều đạt. |
| 4 | Đầy đủ chức năng | 15 | /15 | Giai đoạn triển khai đủ lệnh hoặc API bắt buộc, không có phần giữ chỗ chưa hoàn thiện, không bỏ sót hành vi cũ quan trọng. |
| 5 | Dễ đọc và dễ bảo trì | 5 | /5 | Mã nguồn, script và kết quả rõ ràng, có cấu trúc, đặt tên dễ hiểu, ít trùng lặp và không lan phạm vi ngoài giai đoạn. |
| 6 | Tuân thủ rule, Memory/RAG và skill trong project | 5 | /5 | Người điều phối và tác nhân đã đọc rule trong project, ưu tiên Memory First/RAG First bằng `./.agents/skills/project-rag-search` khi cần ngữ cảnh, chọn skill phù hợp từ `./.agents/skills`, đọc hướng dẫn skill trước khi làm, ghi rule/skill trong prompt/báo cáo và không tạo bản rule hoặc skill trùng lặp ở nơi khác. |
| 7 | An toàn dữ liệu và dọn dẹp | 5 | /5 | Kiểm thử chụp nhanh và khôi phục cấu hình, không tạo rác ở Màn hình nền hoặc thư mục tạm, không lộ mã xác thực hoặc bí mật, không để lại tiến trình app hoặc kiểm thử. |
| | **Tổng điểm** | **100** | **/100** | **Điểm đạt tối thiểu để Release: 95/100** |

## Điều kiện bắt buộc đánh FAIL (NO-GO)
Giai đoạn phải bị đánh FAIL (NO-GO) nếu gặp bất kỳ lỗi nào dưới đây (điểm đánh giá bị vô hiệu):
1. Có đường dẫn tuyệt đối thật trong mã nguồn, script, kết quả hoặc tài liệu thuộc phạm vi giai đoạn.
2. Build thất bại.
3. Ứng dụng không mở được.
4. Surface tích hợp thật của runtime không sẵn sàng (ví dụ: IPC token/pipe, API endpoint, UI route, CLI command, SDK entrypoint hoặc service health).
5. Ca kiểm thử runtime chính thất bại.
6. Kiểm thử chỉ là kiểm thử đơn vị hoặc phản chiếu (reflection) mà chưa gọi vào runtime thật.
7. Có tiến trình app hoặc kiểm thử còn treo sau khi kiểm thử kết thúc.
8. Kết quả chứa mã xác thực, bí mật hoặc dữ liệu chưa được làm sạch.
9. Có luồng tự ý tắt app, service hoặc runtime trong khi luồng điều phối chính chưa cho phép.
10. Chưa đủ bằng chứng thực tế nhưng báo cáo đạt.
11. Bỏ qua các skill phù hợp sẵn có trong `./.agents/skills` mà không có lý do được chấp nhận.
12. Tự ý copy hoặc tạo bản sao skill, prompt hoặc workflow mới ở thư mục khác khi project đã có skill tương ứng.
13. Bỏ qua rule của project hoặc không chứng minh đã đọc rule bắt buộc.
14. Tạo rule song song làm lệch hướng `PROJECT_RULES.md`, `./.agents/AGENTS.md` hoặc `./.agents/AI_RULES.md`.
15. Quét mã nguồn hoặc hỏi thiết kế trước khi tra cứu Project Memory và dùng `./.agents/skills/project-rag-search` khi cần ngữ cảnh.
