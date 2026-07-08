# AI Skills Master Index

This document is the master directory of all 20 skills available in the AI Skill Framework. It details the purpose, inputs/outputs, boundaries, and dependencies for each skill.

---

### 🗺️ Dynamic Project-Aware Workflow (FEAT-XXX format)

The framework utilizes a project-aware, dynamic workflow structure. At initialization, the **`project-discovery`** skill scans the workspace configurations and generates `.agents/project-profile.json`. 

The core milestones are dynamically built, skipping non-applicable gates (e.g. Frontend Visual Debug for backend Go apps, or Desktop UI debug for standard web apps).

### Workflow Sequence Overview

```
              Initialize Workflow (Core 1)
                           │
                           ▼
             Project Memory Update (Core 2)
                           │
                           ▼
                 Brainstorming (Core 3)
                           │
                           ▼
                    Planning (Core 4)
                           │
                           ▼
                    Blueprint (Core 5)
                           │
                           ▼
                 Implementation (Core 6)
                           │
                           ▼
                  Debugging (Core 7)
                           │
     ┌─────────────────────┴─────────────────────┐
     ▼                                           ▼
[UI Stack Detected]                    [Backend-Only Stack]
Frontend/Desktop Visual Debug           Skipped (Backend Only)
     │                                           │
     └─────────────────────┬─────────────────────┘
                           ▼
             Feature Verification (Core 8)
                           │
                           ▼
                    Release (Core 9)
                           │
                           ▼
             Project Memory Update (Core 2)
```

---

## 📂 Skill Catalog

### 1. software-development-workflow
* **Primary Command**: `/workflow`
* **Aliases**: `/flow`, `/status`
* **Category**: `workflow`
* **Tags**: `#workflow`, `#status`, `#orchestrator`
* **Purpose**: Act as the central project coordinator and manager. Tracks workflow by Feature ID.
* **Responsibilities**: Inspects the workspace, scans `docs/brainstorm/` to determine the active Feature ID, traces downstream files, verifies ADR dependencies, and recommends the single correct next skill.
* **Input**:
  ```yaml
  workspace: "auto"
  check_environment: true
  check_memory: true
  check_workflow: true
  task_description: "auto"
  ```
* **Output**: Detailed workflow status report tracking Feature ID and naming next steps.
* **Capability Boundary**: Read-only.
* **Recommended Next Skill**: Varied (depends on active Feature ID status).
* **Example Invocation**:
  ```bash
  /workflow
  ```
* **Current Status**: Stable.
* **Dependencies**: None.

---
### 2. environment-bootstrap
* **Primary Command**: `/bootstrap`
* **Aliases**: `/setup`, `/install-env`
* **Category**: `environment`
* **Tags**: `#setup`, `#bootstrap`, `#environment`
* **Purpose**: Prepare the local system for the AI coding workflow.
* **Responsibilities**: Installs/configures CLI tools, initializes project memory configuration, and validates database/LLM infrastructure.
* **Input**:
  ```yaml
  workspace: "auto"
  install_safe: true
  prompt_unsafe: true
  init_memory_config: "prompt"
  check_skills: true
  check_qdrant: true
  check_embedding: true
  network_timeout_seconds: 3
  ```
* **Output**: Installed dependencies and initialized configurations.
* **Capability Boundary**: Only modifies system tools/configurations. Never modifies application source code.
* **Recommended Next Skill**: `environment-health`
* **Example Invocation**:
  ```bash
  /bootstrap
  ```
* **Current Status**: Stable.
* **Dependencies**: Requires administrator privileges for certain packages.

---
### 3. environment-health
* **Primary Command**: `/doctor`
* **Aliases**: `/health`, `/environment`
* **Category**: `environment`
* **Tags**: `#diagnostics`, `#health`, `#system`
* **Purpose**: Perform read-only diagnostic check of the development environment.
* **Responsibilities**: Verifies version numbers of tools, git config, Python/Node setup, Qdrant/Ollama endpoints, and availability of required skills.
* **Input**:
  ```yaml
  workspace: "auto"
  check_optional: true
  check_git_state: true
  check_network: true
  network_timeout_seconds: 3
  report_format: "detailed"
  ```
* **Output**: Detailed HTML/Markdown health report.
* **Capability Boundary**: Read-only. Never installs packages or alters configurations.
* **Recommended Next Skill**: `project-memory-bootstrap` (if memory is missing) or `software-development-workflow`.
* **Example Invocation**:
  ```bash
  /doctor
  ```
* **Current Status**: Stable.
* **Dependencies**: None.

---
### 4. project-memory-bootstrap
* **Primary Command**: `/memory-init`
* **Aliases**: `/memory-bootstrap`
* **Category**: `memory`
* **Tags**: `#memory`, `#bootstrap`, `#initialization`
* **Purpose**: Perform initial comprehensive scan of a project and generate structural Project Memory.
* **Responsibilities**: Analyzes the architecture, services, repositories, schemas, and lessons, and builds the initial semantic memory database.
* **Input**:
  ```yaml
  mode: "full"
  workspace: "auto"
  config_file: ".agents/memory.config.json"
  output_path: "auto"
  git_aware: true
  layers: ["summary", "architecture", "modules", "services", "repositories", "apis", "entities", "lessons", "indexes", "rag", "embeddings", "sqlite"]
  ```
* **Output**: Complete project memory folders under `.agents/memory/`.
* **Capability Boundary**: Only writes to the configured memory storage directory. Never alters source code.
* **Recommended Next Skill**: `software-development-workflow`
* **Example Invocation**:
  ```bash
  /memory-init
  ```
* **Current Status**: Stable.
* **Dependencies**: Needs tree-sitter or parser utilities for full module parsing.

---
### 5. project-memory-update
* **Primary Command**: `/memory-sync`
* **Aliases**: `/sync`, `/index`
* **Category**: `memory`
* **Tags**: `#memory`, `#synchronization`, `#update`
* **Purpose**: Sync Project Memory after files have changed.
* **Responsibilities**: Reads Git diff, identifies modified areas, and updates affected memory files and database indexes.
* **Input**:
  ```yaml
  mode: "full"
  ```
* **Output**: Updated memory layer files and indexes.
* **Capability Boundary**: Only writes updates to the memory storage folder.
* **Recommended Next Skill**: `software-development-workflow`
* **Example Invocation**:
  ```bash
  /memory-sync
  ```
* **Current Status**: Stable.
* **Dependencies**: `project-memory-bootstrap` (must have been run once).

---
### 6. project-rag-search
* **Primary Command**: `/memory-search`
* **Aliases**: `/search`, `/rag`
* **Category**: `memory`
* **Tags**: `#search`, `#rag`, `#retrieval`
* **Purpose**: Provide fast semantic search over project context.
* **Responsibilities**: Queries project indexes and memory files for relevant context.
* **Input**:
  ```yaml
  query: "How are background tasks configured?"
  workspace: "auto"
  config_file: ".agents/memory.config.json"
  top_k: 5
  retrieval_depth: "auto"
  include_lessons: true
  include_dependencies: true
  staleness_threshold_days: 7
  ```
* **Output**: Filtered, ranked markdown excerpts answering the query.
* **Capability Boundary**: Read-only.
* **Recommended Next Skill**: None (utility skill).
* **Example Invocation**:
  ```bash
  /memory-search query="SQLite connection pool"
  ```
* **Current Status**: Stable.
* **Dependencies**: Relies on memory indexes.

---
### 7. brainstorming
* **Primary Command**: `/brainstorm`
* **Aliases**: `/idea`, `/discover`
* **Category**: `workflow`
* **Tags**: `#requirements`, `#discovery`, `#brainstorming`
* **Purpose**: Production-hardened Requirement Discovery and Feature Decomposition Skill. Treats all user input as raw requirements. Detects single or multiple independent features, performs systematic discovery with a Readiness Score gate (< 85 triggers clarification), generates 2-3 solution options, requires explicit Y/N user confirmation, and writes only `docs/brainstorm/FEAT-XXX_feature_name.md`. Strictly read-only on all other workspace files.
* **Responsibilities**: (1) Detect and decompose multiple independent features, (2) Perform Requirement Discovery, Analysis, Gap Analysis, Impact Analysis, Risk Analysis, (3) Consult Project Memory and RAG, (4) Calculate Requirement Readiness Score — stop if < 85, (5) Generate 2-3 significantly different solution options, (6) Recommend one option with detailed architectural reasoning, (7) Require explicit Y/N confirmation before any file write, (8) Generate brainstorming document, (9) STOP — never transition downstream.
* **Input**: Free text after the invocation command. No YAML parameters required.
  ```text
  /brainstorm Add local cache for playwright static files.
  /brainstorm Fix login bug. Optimize cache. Change database.
  ```
* **Output**: `docs/brainstorm/FEAT-XXX_feature_name.md` only.
* **Capability Boundary**: Strictly read-only. Only writes to `docs/brainstorm/`. Never modifies source code, tests, memory, changelog, or invokes other Skills.
* **Recommended Next Skill**: `brainstorming-to-plan` — must be invoked manually by the user.
* **Current Status**: Production Hardened (v1.5.2 — Requirement Discovery & Feature Decomposition).
* **Dependencies**: None.

---
### 8. brainstorming-to-plan
* **Primary Command**: `/plan`
* **Aliases**: `/planning`, `/planning-phase`
* **Category**: `workflow`
* **Tags**: `#planning`, `#workflow`, `#scoping`
* **Purpose**: Convert a master brainstorming requirements document into a formal, Feature-ID-aligned Implementation Plan under `docs/plans/` using the `FEAT-XXX` format.
* **Responsibilities**: Validates details and scope of work using a memory-first approach. Reuses the active Feature ID.
* **Input**:
  ```yaml
  prompt_file: "docs/brainstorm/FEAT-XXX_<feature_name>.md"
  workspace: "auto"
  language: "auto"
  framework: "auto"
  architecture: "auto"
  output_path: "docs/plans/auto"
  ```
* **Output**: An implementation plan file under `docs/plans/FEAT-XXX_<feature_name>_plan.md` containing relative links and Traceability Info.
* **Capability Boundary**: Only writes to `docs/plans/`.
* **Recommended Next Skill**: `plan-to-blueprint`
* **Example Invocation**:
  ```bash
  /brainstorm-to-plan prompt_file="docs/brainstorm/FEAT-001_local_cache.md"
  ```
* **Current Status**: Refactored (FEAT-XXX format).
* **Dependencies**: Requires a generated brainstorming prompt document.

---
### 9. plan-to-blueprint
* **Primary Command**: `/blueprint`
* **Aliases**: `/design`, `/architecture`
* **Category**: `workflow`
* **Tags**: `#blueprint`, `#design`, `#architecture`
* **Purpose**: Convert an approved Implementation Plan into a detailed Technical Blueprint.
* **Responsibilities**: Designs interfaces, database schemas, code contracts, sequence diagrams, and recommends optional ADRs. Reuses the active Feature ID.
* **Input**:
  ```yaml
  source_plan: "docs/plans/FEAT-XXX_<feature_name>_plan.md"
  workspace: "auto"
  language: "auto"
  tech_stack: "auto"
  architecture: "auto"
  output_path: "docs/designs/auto"
  ```
* **Output**: Technical design blueprint under `docs/designs/FEAT-XXX_<feature_name>_blueprint.md` containing an ADR assessment.
* **Capability Boundary**: Only writes technical blueprints. Does not modify application source code or write ADR files directly.
* **Recommended Next Skill**: `create-adr` (if ADR Required = Yes) or `blueprint-to-implementation` (if ADR Required = No).
* **Example Invocation**:
  ```bash
  /blueprint source_plan="docs/plans/FEAT-001_local_cache_plan.md"
  ```
* **Current Status**: Refactored (FEAT-XXX format & ADR Assessment).
* **Dependencies**: Requires an approved Implementation Plan.

---
### 10. create-adr
* **Primary Command**: `/adr`
* **Aliases**: `/architecture-decision`
* **Category**: `architecture`
* **Tags**: `#adr`, `#architecture`, `#decision`
* **Purpose**: Create Architecture Decision Records (ADRs) only when explicitly invoked.
* **Responsibilities**: Evaluates decisions, alternatives, trade-offs, and risks, and documents them.
* **Input**:
  ```yaml
  title: "Decide on cache strategy for Playwright assets"
  related_feature: "docs/brainstorm/FEAT-001_local_cache.md"
  design_file: "docs/designs/FEAT-001_local_cache_blueprint.md"
  ```
* **Output**: Writes the ADR file to `docs/adr/ADR-XXX_short_title.md` (where `XXX` is independent of Feature ID).
* **Capability Boundary**: Only writes to `docs/adr/`.
* **Recommended Next Skill**: `blueprint-to-implementation`
* **Example Invocation**:
  ```bash
  /adr title="Decide cache mechanism" related_feature="docs/brainstorm/FEAT-001_local_cache.md"
  ```
* **Current Status**: New Skill (ADR Support).
* **Dependencies**: None.

---
### 11. blueprint-to-implementation
* **Primary Command**: `/implement`
* **Aliases**: `/code`, `/build`
* **Category**: `workflow`
* **Tags**: `#implementation`, `#code`, `#generation`
* **Purpose**: Implement production-ready code based on an approved Technical Blueprint.
* **Responsibilities**: Generates code matching the blueprint, verifies compilation, and runs local tests. Verifies ADR presence if specified in design blueprint.
* **Input**:
  ```yaml
  phase: "auto"
  design_file: "docs/designs/FEAT-XXX_<feature_name>_blueprint.md"
  workspace: "auto"
  language: "auto"
  tech_stack: "auto"
  architecture: "auto"
  implementation_scope: "auto"
  build_command: "auto"
  test_command: "auto"
  ```
* **Output**: Source code edits matching the blueprint.
* **Capability Boundary**: Only modifies codebase files scoped in the blueprint. Enforces ADR validation blocking before code changes.
* **Recommended Next Skill**: `project-memory-update` (to sync code changes), followed by `implementation-to-release`.
* **Example Invocation**:
  ```bash
  /implement design_file="docs/designs/FEAT-001_local_cache_blueprint.md"
  ```
* **Current Status**: Refactored (FEAT-XXX format & ADR Validation).
* **Dependencies**: Requires an approved Technical Blueprint and matching accepted ADR if requested.

---
### 12. frontend-design
* **Primary Command**: `/ui`
* **Aliases**: `/frontend`, `/design`
* **Category**: `utility`
* **Tags**: `#ui`, `#design`, `#ux`
* **Purpose**: Provide frontend design principles and UX psychological guardrails for web application development.
* **Responsibilities**: Instructs the agent on accessibility compliance, color harmony, typography systems, smooth animations, and UX design checklists.
* **Input**: UI design request/context.
* **Output**: Aesthetic, premium visual design specifications.
* **Capability Boundary**: Guides design decisions.
* **Recommended Next Skill**: None (advisory design workflow).
* **Example Invocation**:
  ```bash
  /ui
  ```
* **Current Status**: Stable.
* **Dependencies**: Requires runtime Python for `scripts/ux_audit.py`.

---
### 13. implementation-to-release
* **Primary Command**: `/release`
* **Aliases**: `/publish`, `/ship`
* **Category**: `workflow`
* **Tags**: `#release`, `#versioning`, `#publish`
* **Purpose**: Finalize the current feature cycle and publish a release, supporting single and multi-module configurations.
* **Responsibilities**: Configuration loading, file change and affected module detection, per-module version bumps and CHANGELOG updates, root Release Summary generation, branch merge gate, git commits, tags, and pushes.
* **Input**:
  ```yaml
  phase: "auto"
  workspace: "auto"
  branch: "auto"
  version: "auto"
  version_strategy: "auto"
  commit_style: "conventional"
  update_changelog: true
  commit_changes: true
  push_after_commit: true
  create_git_tag: false
  create_release: false
  build_command: "auto"
  test_command: "auto"
  ```
* **Output**: Updates corresponding version files and CHANGELOGs per module, compiles root Release Summary, commits changes, creates tag(s) (simple or prefixed per module), and pushes.
* **Capability Boundary**: Read/write access for version configurations, changelogs, and git repository. No new feature logic is allowed.
* **Recommended Next Skill**: `project-memory-update` (post-push).
* **Example Invocation**:
  ```bash
  /release
  ```
* **Current Status**: Production Stable (v2.4.0 — Configuration-driven & Module-aware Release).
* **Dependencies**: Healthy environment, valid `.agents/release.config.json` configuration, correct Git credentials.

---
### 14. okr-report-generator
* **Primary Command**: `/okr`
* **Aliases**: `/report`
* **Category**: `utility`
* **Tags**: `#okr`, `#report`, `#ocr`
* **Purpose**: Parse task-tracking board images to compile OKR status reports.
* **Responsibilities**: OCRs input task boards and builds summarized/completed task markdown logs.
* **Input**: OKR board image path.
* **Output**: Generates `summary.md` and `completed_tasks.md` in the current folder.
* **Capability Boundary**: Only creates reporting files.
* **Recommended Next Skill**: None (utility skill).
* **Example Invocation**:
  ```bash
  /okr image_path="C:\Users\Kyle\Desktop\okr.jpg"
  ```
* **Current Status**: Stable.
* **Dependencies**: Requires OCR capabilities / multimodal models.

---
### 15. quick-fix
* **Primary Command**: `/fix`
* **Aliases**: `/bugfix`
* **Category**: `utility`
* **Tags**: `#utility`, `#bugfix`, `#patch`
* **Purpose**: Provide a lightweight, fast-track workflow for small, low-risk bug fixes (e.g. 404 Route, Cannot POST, Null Pointer, Wrong SQL, Typo, Validation Bug, Configuration Error, Wrong Permission, Small UI Bug).
* **Responsibilities**:
  1. Evaluate reported issue against Quick-Fix Eligibility Matrix (low risk, small scope).
  2. Perform eligibility check and stop/reject standard features.
  3. Inspect memory configuration, Project Memory, and RAG search.
  4. Perform targeted source inspection and generate Fix document (`docs/brainstorm/FIX-XXX_issue_name.md`).
  5. User Approval Gate: Prompt user `Continue? [Y/N]` and pause.
  6. Apply minimal code changes to source code after Y confirmation.
  7. Verify correctness via builds and tests.
  8. Generate Quick-Fix Implementation Summary.
* **Input**: Free text after invocation.
  ```text
  /fix Cannot POST /api/profiles/bulk/update-proxy-multi
  ```
* **Output**: Minimal code changes in the repository, and a Quick-Fix Summary report printed to console.
* **Capability Boundary**: Never generates plans, blueprints, or ADR files. Only writes `docs/brainstorm/FIX-XXX_issue_name.md` before user confirmation.
* **Recommended Next Skill**: `implementation-to-release` (must be executed manually).
* **Current Status**: Production Stable (v1.7.1 — Quick Fix Workflow).
* **Dependencies**: Clean working state, correct Git credentials.

---
### 16. quick-feature
* **Primary Command**: `/feature`
* **Aliases**: `/scaffold`
* **Category**: `utility`
* **Tags**: `#utility`, `#feature`, `#scaffolding`
* **Purpose**: Provide a lightweight, fast-track workflow for small, low-risk feature requests (e.g. Add one API endpoint, button, dialog, filter, validation, search field, export function, configuration option).
* **Responsibilities**:
  1. Evaluate request against Quick-Feature Eligibility Matrix (low risk, single module scope).
  2. Perform eligibility check and stop/reject standard features.
  3. Inspect memory configuration, Project Memory, and RAG search.
  4. Perform targeted source inspection and generate Mini Feature Specification (`docs/brainstorm/FEAT-XXX_feature_name.md`).
  5. User Approval Gate: Prompt user `Continue? [Y/N]` and pause.
  6. Apply minimal code changes to source code after Y confirmation.
  7. Verify correctness via builds and tests.
  8. Generate Quick Feature Summary report.
* **Input**: Free text after invocation.
  ```text
  /feature Add Export CSV button to bulk proxy modal.
  ```
* **Output**: Minimal code changes in the repository, a Mini Feature Specification under `docs/brainstorm/FEAT-XXX_feature_name.md`, and a summary report.
* **Capability Boundary**: Never generates planning, blueprints, or ADR files. Never commits, pushes, or executes releases.
* **Recommended Next Skill**: `implementation-to-release` (must be executed manually).
* **Current Status**: Production Stable (v1.7.0 — Quick Feature Workflow).
* **Dependencies**: Clean working state, correct Git credentials.

---
### 17. initialize-workflow
* **Primary Command**: `/init`
* **Aliases**: `/initialize`
* **Category**: `runtime`
* **Tags**: `#initialization`, `#bootstrap`, `#runtime`
* **Purpose**: Perform system initialization, verify the workspace and Git environment, resolve project rules and policies, load Project Memory, and build a unified runtime execution context.
* **Responsibilities**:
  1. Validate workspace and directory root.
  2. Parse `.agents/AGENTS.md` and load global runtime policies.
  3. Load Memory configurations and summary indexes.
  4. Collect Git metadata (active branch, dirty status, remote URL, default branch, tags).
  5. Scan standard documentation subfolders for the latest active feature/fix/quick ID.
  6. Identify the current project version from package/config files.
  7. Validate the presence of the 8 standard documentation folders under `docs/`.
  8. Inspect environment tool availability and output a clean plain text initialization report block.
* **Input**: None (purely read-only).
* **Output**: Standard execution context schema and a structured plain text initialization status log.
* **Capability Boundary**: Strictly read-only. Never modifies repository files, source code, configs, or Git state.
* **Recommended Next Skill**: `software-development-workflow` (or the skill requested by the user).
* **Example Invocation**:
  ```bash
  /init
  ```
* **Current Status**: Production Stable (v2.1.0 — Initialization Layer).
* **Dependencies**: None.

---
### 18. implementation-to-debug
* **Primary Command**: `/debug`
* **Aliases**: `/compile`, `/lint`
* **Category**: `workflow`
* **Tags**: `#debug`, `#testing`, `#verification`
* **Purpose**: Review the implementation, verify builds, resolve compilation and linting issues, and fix unit tests before code verification.
* **Responsibilities**:
  1. Build project and run compile commands to ensure clean code.
  2. Run linters and formatters.
  3. Execute unit test suites and verify a 100% pass rate.
  4. Fix compilation, linting, and runtime errors.
  5. Remove dead code and unused imports.
  6. Enhance logging and error handling.
  7. Generate Debug Report at `docs/debug/FEAT-XXX_debug.md`.
* **Input**: None (runs automatically on codebase).
* **Output**: A Debug Report under `docs/debug/FEAT-XXX_debug.md`.
* **Capability Boundary**: Only reads source files and runs build tools. Never merges, tags, or pushes.
* **Recommended Next Skill**: `debug-to-verify` (command: `/verify`).
* **Example Invocation**:
  ```bash
  /debug
  ```
* **Current Status**: Production Stable (v1.0.0 — Quality Layer).
* **Dependencies**: Implementation complete (Checkpoint 6).

---
### 19. debug-to-verify
* **Primary Command**: `/verify`
* **Aliases**: `/check`, `/audit`
* **Category**: `workflow`
* **Tags**: `#verification`, `#quality`, `#compliance`
* **Purpose**: Perform a final qualitative and quantitative audit on the active feature implementation to ensure it meets all standards before staging for release.
* **Responsibilities**:
  1. Verify Acceptance Criteria from the project plan.
  2. Check Technical Blueprint compliance and ADR alignment.
  3. Verify Coding Standards, security conventions, and input sanitization.
  4. Evaluate performance risks and database index configurations.
  5. Check documentation completeness and changelog readiness.
  6. Output formal Go / No-Go decision recommendation.
  7. Generate Verification Report at `docs/verification/FEAT-XXX_verify.md`.
* **Input**: None (analyzes generated documents and code changes).
* **Output**: A Verification Report under `docs/verification/FEAT-XXX_verify.md`.
* **Capability Boundary**: Read-only audit skill. Never makes code modifications.
* **Recommended Next Skill**: `implementation-to-release` (command: `/release`).
* **Example Invocation**:
  ```bash
  /verify
  ```
* **Current Status**: Production Stable (v1.0.0 — Quality Layer).
* **Dependencies**: Debug report complete with PASS status (Checkpoint 7).

---
### 20. workflow-runtime
* **Primary Command**: `/runtime`
* **Aliases**: `/engine`
* **Category**: `runtime`
* **Tags**: `#runtime`, `#controller`, `#session`
* **Purpose**: Manage the active execution session, validate runtime health, detect context drift, update checkpoints, and support recovery via resume-workflow.
* **Responsibilities**:
  1. Maintain execution state in `.agents/.session.json`.
  2. Verify that workspace, policies, memory, Git branch, and project version match the active session.
  3. Detect unexpected branch switches or context shifts (Drift Detection) and pause.
  4. Perform checkpoints (1 to 9) at major SDLC milestones.
  5. Print plain text heartbeats and end-of-skill status reports.
  6. Support `/resume` to recover and continue from the last valid checkpoint.
* **Input**: State changes or explicit commands (e.g. `/resume`).
* **Output**: Updated `.session.json` state, console heartbeats, and runtime reports.
* **Capability Boundary**: Read-only regarding source code. Only modifies the local session file `.agents/.session.json`.
* **Recommended Next Skill**: Varied (continues from the last active checkpoint).
* **Example Invocation**:
  ```bash
  /resume
  ```
* **Current Status**: Production Stable (v2.3.0 — Runtime Layer).
* **Dependencies**: Requires a completed `initialize-workflow` run to bootstrap the session state.

---
### 21. frontend-visual-debug
* **Primary Command**: `/visual-debug`
* **Aliases**: `/ui-debug`, `/visual-qa`, `/browser-debug`
* **Category**: `workflow`
* **Tags**: `#frontend`, `#ui`, `#browser`, `#visual`, `#debug`, `#qa`
* **Purpose**: Validate frontend implementation visually using browser automation.
* **Responsibilities**:
  1. Detect the active frontend framework and start/reuse the local dev server.
  2. Open the page under review using the browser subagent.
  3. Capture visual layouts across responsive breakpoints and inspect spacing, alignment, colors, and z-index issues.
  4. Collect console outputs and network tab records to detect errors, failed assets, or failed API calls.
  5. Interactively test buttons, links, forms, and modals.
  6. Apply precise styling/markup bug fixes and generate `docs/verification/FEAT-XXX_visual_debug.md`.
* **Input**:
  ```yaml
* **Current Status**: Production Stable (v2.4.0 — Configuration-driven & Module-aware Release).
* **Dependencies**: Healthy environment, valid `.agents/release.config.json` configuration, correct Git credentials.

---
### 14. okr-report-generator
* **Primary Command**: `/okr`
* **Aliases**: `/report`
* **Category**: `utility`
* **Tags**: `#okr`, `#report`, `#ocr`
* **Purpose**: Parse task-tracking board images to compile OKR status reports.
* **Responsibilities**: OCRs input task boards and builds summarized/completed task markdown logs.
* **Input**: OKR board image path.
* **Output**: Generates `summary.md` and `completed_tasks.md` in the current folder.
* **Capability Boundary**: Only creates reporting files.
* **Recommended Next Skill**: None (utility skill).
* **Example Invocation**:
  ```bash
  /okr image_path="C:\Users\Kyle\Desktop\okr.jpg"
  ```
* **Current Status**: Stable.
* **Dependencies**: Requires OCR capabilities / multimodal models.

---
### 15. quick-fix
* **Primary Command**: `/fix`
* **Aliases**: `/bugfix`
* **Category**: `utility`
* **Tags**: `#utility`, `#bugfix`, `#patch`
* **Purpose**: Provide a lightweight, fast-track workflow for small, low-risk bug fixes (e.g. 404 Route, Cannot POST, Null Pointer, Wrong SQL, Typo, Validation Bug, Configuration Error, Wrong Permission, Small UI Bug).
* **Responsibilities**:
  1. Evaluate reported issue against Quick-Fix Eligibility Matrix (low risk, small scope).
  2. Perform eligibility check and stop/reject standard features.
  3. Inspect memory configuration, Project Memory, and RAG search.
  4. Perform targeted source inspection and generate Fix document (`docs/brainstorm/FIX-XXX_issue_name.md`).
  5. User Approval Gate: Prompt user `Continue? [Y/N]` and pause.
  6. Apply minimal code changes to source code after Y confirmation.
  7. Verify correctness via builds and tests.
  8. Generate Quick-Fix Implementation Summary.
* **Input**: Free text after invocation.
  ```text
  /fix Cannot POST /api/profiles/bulk/update-proxy-multi
  ```
* **Output**: Minimal code changes in the repository, and a Quick-Fix Summary report printed to console.
* **Capability Boundary**: Never generates plans, blueprints, or ADR files. Only writes `docs/brainstorm/FIX-XXX_issue_name.md` before user confirmation.
* **Recommended Next Skill**: `implementation-to-release` (must be executed manually).
* **Current Status**: Production Stable (v1.7.1 — Quick Fix Workflow).
* **Dependencies**: Clean working state, correct Git credentials.

---
### 16. quick-feature
* **Primary Command**: `/feature`
* **Aliases**: `/scaffold`
* **Category**: `utility`
* **Tags**: `#utility`, `#feature`, `#scaffolding`
* **Purpose**: Provide a lightweight, fast-track workflow for small, low-risk feature requests (e.g. Add one API endpoint, button, dialog, filter, validation, search field, export function, configuration option).
* **Responsibilities**:
  1. Evaluate request against Quick-Feature Eligibility Matrix (low risk, single module scope).
  2. Perform eligibility check and stop/reject standard features.
  3. Inspect memory configuration, Project Memory, and RAG search.
  4. Perform targeted source inspection and generate Mini Feature Specification (`docs/brainstorm/FEAT-XXX_feature_name.md`).
  5. User Approval Gate: Prompt user `Continue? [Y/N]` and pause.
  6. Apply minimal code changes to source code after Y confirmation.
  7. Verify correctness via builds and tests.
  8. Generate Quick Feature Summary report.
* **Input**: Free text after invocation.
  ```text
  /feature Add Export CSV button to bulk proxy modal.
  ```
* **Output**: Minimal code changes in the repository, a Mini Feature Specification under `docs/brainstorm/FEAT-XXX_feature_name.md`, and a summary report.
* **Capability Boundary**: Never generates planning, blueprints, or ADR files. Never commits, pushes, or executes releases.
* **Recommended Next Skill**: `implementation-to-release` (must be executed manually).
* **Current Status**: Production Stable (v1.7.0 — Quick Feature Workflow).
* **Dependencies**: Clean working state, correct Git credentials.

---
### 17. initialize-workflow
* **Primary Command**: `/init`
* **Aliases**: `/initialize`
* **Category**: `runtime`
* **Tags**: `#initialization`, `#bootstrap`, `#runtime`
* **Purpose**: Perform system initialization, verify the workspace and Git environment, resolve project rules and policies, load Project Memory, and build a unified runtime execution context.
* **Responsibilities**:
  1. Validate workspace and directory root.
  2. Parse `.agents/AGENTS.md` and load global runtime policies.
  3. Load Memory configurations and summary indexes.
  4. Collect Git metadata (active branch, dirty status, remote URL, default branch, tags).
  5. Scan standard documentation subfolders for the latest active feature/fix/quick ID.
  6. Identify the current project version from package/config files.
  7. Validate the presence of the 8 standard documentation folders under `docs/`.
  8. Inspect environment tool availability and output a clean plain text initialization report block.
* **Input**: None (purely read-only).
* **Output**: Standard execution context schema and a structured plain text initialization status log.
* **Capability Boundary**: Strictly read-only. Never modifies repository files, source code, configs, or Git state.
* **Recommended Next Skill**: `software-development-workflow` (or the skill requested by the user).
* **Example Invocation**:
  ```bash
  /init
  ```
* **Current Status**: Production Stable (v2.1.0 — Initialization Layer).
* **Dependencies**: None.

---
### 18. implementation-to-debug
* **Primary Command**: `/debug`
* **Aliases**: `/compile`, `/lint`
* **Category**: `workflow`
* **Tags**: `#debug`, `#testing`, `#verification`
* **Purpose**: Review the implementation, verify builds, resolve compilation and linting issues, and fix unit tests before code verification.
* **Responsibilities**:
  1. Build project and run compile commands to ensure clean code.
  2. Run linters and formatters.
  3. Execute unit test suites and verify a 100% pass rate.
  4. Fix compilation, linting, and runtime errors.
  5. Remove dead code and unused imports.
  6. Enhance logging and error handling.
  7. Generate Debug Report at `docs/debug/FEAT-XXX_debug.md`.
* **Input**: None (runs automatically on codebase).
* **Output**: A Debug Report under `docs/debug/FEAT-XXX_debug.md`.
* **Capability Boundary**: Only reads source files and runs build tools. Never merges, tags, or pushes.
* **Recommended Next Skill**: `debug-to-verify` (command: `/verify`).
* **Example Invocation**:
  ```bash
  /debug
  ```
* **Current Status**: Production Stable (v1.0.0 — Quality Layer).
* **Dependencies**: Implementation complete (Checkpoint 6).

---
### 19. debug-to-verify
* **Primary Command**: `/verify`
* **Aliases**: `/check`, `/audit`
* **Category**: `workflow`
* **Tags**: `#verification`, `#quality`, `#compliance`
* **Purpose**: Perform a final qualitative and quantitative audit on the active feature implementation to ensure it meets all standards before staging for release.
* **Responsibilities**:
  1. Verify Acceptance Criteria from the project plan.
  2. Check Technical Blueprint compliance and ADR alignment.
  3. Verify Coding Standards, security conventions, and input sanitization.
  4. Evaluate performance risks and database index configurations.
  5. Check documentation completeness and changelog readiness.
  6. Output formal Go / No-Go decision recommendation.
  7. Generate Verification Report at `docs/verification/FEAT-XXX_verify.md`.
* **Input**: None (analyzes generated documents and code changes).
* **Output**: A Verification Report under `docs/verification/FEAT-XXX_verify.md`.
* **Capability Boundary**: Read-only audit skill. Never makes code modifications.
* **Recommended Next Skill**: `implementation-to-release` (command: `/release`).
* **Example Invocation**:
  ```bash
  /verify
  ```
* **Current Status**: Production Stable (v1.0.0 — Quality Layer).
* **Dependencies**: Debug report complete with PASS status (Checkpoint 7).

---
### 20. workflow-runtime
* **Primary Command**: `/runtime`
* **Aliases**: `/engine`
* **Category**: `runtime`
* **Tags**: `#runtime`, `#controller`, `#session`
* **Purpose**: Manage the active execution session, validate runtime health, detect context drift, update checkpoints, and support recovery via resume-workflow.
* **Responsibilities**:
  1. Maintain execution state in `.agents/.session.json`.
  2. Verify that workspace, policies, memory, Git branch, and project version match the active session.
  3. Detect unexpected branch switches or context shifts (Drift Detection) and pause.
  4. Perform checkpoints (1 to 9) at major SDLC milestones.
  5. Print plain text heartbeats and end-of-skill status reports.
  6. Support `/resume` to recover and continue from the last valid checkpoint.
* **Input**: State changes or explicit commands (e.g. `/resume`).
* **Output**: Updated `.session.json` state, console heartbeats, and runtime reports.
* **Capability Boundary**: Read-only regarding source code. Only modifies the local session file `.agents/.session.json`.
* **Recommended Next Skill**: Varied (continues from the last active checkpoint).
* **Example Invocation**:
  ```bash
  /resume
  ```
* **Current Status**: Production Stable (v2.3.0 — Runtime Layer).
* **Dependencies**: Requires a completed `initialize-workflow` run to bootstrap the session state.

---
### 21. frontend-visual-debug
* **Primary Command**: `/visual-debug`
* **Aliases**: `/ui-debug`, `/visual-qa`, `/browser-debug`
* **Category**: `workflow`
* **Tags**: `#frontend`, `#ui`, `#browser`, `#visual`, `#debug`, `#qa`
* **Purpose**: Validate frontend implementation visually using browser automation.
* **Responsibilities**:
  1. Detect the active frontend framework and start/reuse the local dev server.
  2. Open the page under review using the browser subagent.
  3. Capture visual layouts across responsive breakpoints and inspect spacing, alignment, colors, and z-index issues.
  4. Collect console outputs and network tab records to detect errors, failed assets, or failed API calls.
  5. Interactively test buttons, links, forms, and modals.
  6. Apply precise styling/markup bug fixes and generate `docs/verification/FEAT-XXX_visual_debug.md`.
* **Input**:
  ```yaml
  design_file: "docs/designs/FEAT-XXX_blueprint.md"
  debug_report: "docs/debug/FEAT-XXX_debug.md"
  ```
* **Output**: A Visual Debug Report under `docs/verification/FEAT-XXX_visual_debug.md`.
* **Capability Boundary**: Allowed to fix CSS, layout, component markup, and UI state. Forbidden from rewriting backend architectures or unrelated modules.
* **Recommended Next Skill**: `debug-to-verify` (command: `/verify`).
* **Example Invocation**:
  ```bash
  /visual-debug
  ```
* **Current Status**: Production Stable (v1.0.0 — Quality Layer).
* **Dependencies**: Debug report complete with PASS status (Checkpoint 7).

---
### 22. project-discovery
* **Primary Command**: `/discover`
* **Aliases**: `/tech-stack`, `/project-profile`
* **Category**: `environment`
* **Tags**: `#project`, `#tech-stack`, `#workflow`, `#profile`, `#discovery`
* **Purpose**: Discover target project's technologies and compile `.agents/project-profile.json` configuration.
* **Responsibilities**:
  1. Scan package.json, go.mod, Cargo.toml, pyproject.toml, and other stack signatures.
  2. Parse active languages, testing frameworks, linter tooling, databases, platforms, and runtime settings.
  3. Formulate custom dynamic checkpoints sequence (`recommended_workflow`) based on stack requirements.
  4. Write `.agents/project-profile.json` and update session state to Checkpoint 2.
* **Input**: None (scans root repository configurations).
* **Output**: `.agents/project-profile.json` profile file.
* **Capability Boundary**: Read-only regarding source code. Only writes the project profile configuration under `.agents/`.
* **Recommended Next Skill**: `brainstorming` (command: `/brainstorm`).
* **Example Invocation**:
  ```bash
  /discover
  ```
* **Current Status**: Production Stable (v1.0.0 — Environment Layer).
* **Dependencies**: Completed initialization (Checkpoint 1).

---

## 21. `skill-self-verification` (command: `/verify-skill`)

* **Responsibilities**:
  1. Thực hiện phân tích tĩnh các file hướng dẫn `SKILL.md` để đảm bảo định dạng YAML frontmatter chính xác.
  2. Phát hiện các vi phạm quy tắc an toàn (cấm tuyệt đối đường dẫn tuyệt đối, link `file:///`, hoặc enum không an toàn cho `permission_mode`).
  3. Mô phỏng động sự tương tác hội thoại của người dùng (happy path, sai checkpoint, approval gate, v.v.).
  4. Xuất báo cáo chất lượng chính thức dưới dạng tệp tin markdown trong `docs/verification/`.
* **Input**: `--skill <skill-name>` (Tên Skill cần kiểm tra).
* **Output**: `docs/verification/SKILL-VERIFY_<skill-name>.md` báo cáo xác thực.
* **Capability Boundary**: Chỉ đọc các file Skill và quy tắc, ghi file báo cáo dưới `docs/verification/`.
* **Recommended Next Skill**: `implementation-to-release` (command: `/release`).
* **Example Invocation**:
  ```bash
  /verify-skill brainstorming
  ```
* **Current Status**: Production Stable (v1.0.0 — Quality Layer).
* **Dependencies**: Hoạt động sau bất kỳ pha tạo mới hoặc sửa đổi Skill nào.

---

## 🛠️ Script-First Skill Architecture

Starting with version 5.0.0, the AI Skill Framework implements a **Script-First Skill Architecture**. Under this model, all deterministic, repeatable, file-based validation, and environment inspection tasks are executed by specialized Python scripts instead of being simulated or processed manually by the LLM in natural language prompt text.

### Classification Categories

1. **Group A — Must Become Script-First (100% Executed by Python Scripts)**
   * `initialize-workflow`, `resume-workflow`, `project-discovery`, `project-memory-bootstrap`, `project-memory-update`, `project-rag-search`, `environment-health`, `environment-bootstrap`, `implementation-to-debug`, `debug-to-verify`, `implementation-to-release`, `workflow-runtime`.
   * *CLI Commands*: `aiwf init`, `aiwf resume`, `aiwf discover`, `aiwf classify`, `aiwf memory bootstrap/update/search`, `aiwf env health`, `aiwf validate`, `aiwf debug run`, `aiwf verify run`, `aiwf release plan/execute`.
   * *JSON Output Contract*: Every script-first CLI action output format returns a structured JSON payload:
     ```json
     {
       "status": "success" | "failure",
       "command": "command_name",
       "summary": "human readable status summary",
       "warnings": [],
       "files_read": [],
       "files_written": []
     }
     ```

2. **Group B — Hybrid LLM + Script (Reasoning by LLM + Validation by Scripts)**
   * `brainstorming`, `quick-fix`, `quick-feature`, `brainstorming-to-plan`, `plan-to-blueprint`, `create-adr`, `blueprint-to-implementation`.
   * The LLM performs requirement decomposition, alternative designs analysis, and code logic reasoning, while Python scripts handle formatting validation, artifact checks, and checkpoint locking.

3. **Group C — Remain Mostly LLM-Driven**
   * Rationale writing, UX critique, and architectural trade-off evaluations. Scripts are used only to enforce confirmation gates and status checkpoints.

