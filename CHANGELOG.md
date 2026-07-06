# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.12.0] - 2026-07-06

### Added
- **Script-First Runtime Engine**:
  - Refactored the token and cost calculation into a fully deterministic Python pipeline.
  - Implemented SQLite database storage local to the project (`.agents/project_runtime.db`) and globally in OS AppData directory (`global_runtime.db`) to track three independent scopes: Workflow, Project, and Global usage.
  - Added new CLI subcommands: `usage sync`, `usage report`, `usage diagnose`, `usage export`.
  - Updated the Visualizer Sidebar webview to show three distinct scope cards, with Workflow context limit comparing current active window tokens instead of accumulated totals.

## [2.11.1] - 2026-07-06

### Added
- **Visualizer Extension Session Usage**:
  - Integrated a new visual "Session Usage" metadata card into the visualizer sidebar extension template (`webview.html`).
  - Added token and cost visualization including total tokens, input/output/cache/thinking counts, context limit, usage percentage, cost USD, provider name, active model, accuracy, and last updated time.
  - Implemented color-changing progress bar indicating token capacity warning states (Green < 60%, Yellow 60%-85%, Red > 85%).
  - Added a toggleable empty state fallback container to gracefully handle missing session metrics.

## [2.11.0] - 2026-07-06

### Added
- **Centralized CLI Runtime Engine**:
  - Implemented a modular, executable Python CLI Runtime Engine under `skills/workflow-runtime/scripts/`.
  - Exposed Runtime CLI API: `init`, `validate`, `start`, `step`, `complete`, `fail`, `heartbeat`.
  - Moved session schema validation, atomic file writing, token estimation, drift check, and heartbeat formatting into the Runtime Engine.
  - Refactored all 26 skills to call this CLI instead of natural language prompt edits, resulting in major token savings and robust execution.
  - Added comprehensive automated unit tests under `skills/workflow-runtime/tests/`.

## [2.10.1] - 2026-07-06

### Optimized
- **Token Usage Optimization**: Refactored all 26 workflow skills to centralize repeated policy descriptions (approval gates, git workflow, memory strategy, RAG retrieval) inside `AI_RULES.md`, reducing prompt sizes by ~3,000 tokens per agent context load while preserving 100% behavior.

## [2.10.0] - 2026-07-06

### Added
- **Dynamic Project-Aware Checkpoints**:
  - Introduced the `project-discovery` skill (`/discover`) to scan codebase structure (configuration files, package managers, frameworks, and databases) and generate `.agents/project-profile.json`.
  - Refactored the orchestrator (`software-development-workflow`) and other SDLC skills to dynamically skip checkpoints (e.g., skip `frontend-visual-debug` for backend-only/CLI projects) according to the project profile.
  - Upgraded the VS Code Visualizer extension to support dynamic project-aware checkpoint rendering.

### Fixed
- **Framework Installer Export Bug**:
  - Fixed a packaging bug in `tools/export.js` that missed copying the `templates`, `agents`, and `runtime` folders to the public export directory, resolving installer failures during `aiwf install`.

---

## [2.9.0] - 2026-07-04

### Added
- **Claude (Anthropic) Support Integration**: Added environment, prompt, and discovery support for Anthropic Claude.
  - Upgraded `skills/environment-bootstrap/SKILL.md` to prompt and configure `ANTHROPIC_API_KEY`.
  - Added key verification diagnostics for Gemini and Anthropic in `doctor.ps1` and `doctor.sh`.
  - Defined XML tagging guidelines in `AI_RULES.md` to wrap boundaries for optimal instruction-following on Claude.
  - Added step-by-step Claude Desktop and Claude Code integration guides in `INSTALL.md`.
  - Upgraded VS Code Extension (`extensions/visualizer`) to version `1.0.10` with custom installation instructions in its README, compiled and packaged to `.vsix` packages.

---

## [2.8.3] - 2026-07-04

### Added
- **Visualizer Extension Webview Separation & Branding**: Upgraded the VS Code Extension (`extensions/visualizer`) to version `1.0.5` to separate inline webview HTML/CSS/JS code into resources file, implement build-time code-gen, and attach the missing Marketplace branding Icon.
  - Linked official logo image to extension manifest.
  - Staged, compiled and packaged the extension to `extensions/visualizer/ai-workflow-visualizer-1.0.5.vsix`.

---

## [2.8.2] - 2026-07-03

### Added
- **Visualizer Extension Author Profile**: Upgraded the VS Code Extension (`extensions/visualizer`) to version `1.0.4` to display the Framework Author profile card containing name, email, and website at the bottom of the sidebar explorer webview.
  - Staged, compiled and packaged the extension to `extensions/visualizer/ai-workflow-visualizer-1.0.4.vsix`.

---

## [2.8.1] - 2026-07-03

### Added
- **Visualizer Extension Upgrade**: Upgraded the VS Code Extension (`extensions/visualizer`) to version `1.0.3` to render checkpoint execution status badges:
  - Rendered pulsing orange `"Running"` badge when checkpoint is `"in_progress"`.
  - Rendered red `"Failed"` badge when checkpoint is `"failed"`.
  - Rendered green `"Complete"` badge when checkpoint is `"completed"`.
  - Staged, compiled and packaged the extension to `extensions/visualizer/ai-workflow-visualizer-1.0.3.vsix`.

---

## [2.8.0] - 2026-07-03

### Added
- **Checkpoint Status Tracking**: Introduced checkpoint execution status (`status: "in_progress" | "completed" | "failed"`) to the session state `.session.json` to allow the Visualizer UI Extension to accurately reflect current running and completed steps.
  - Updated `skills/workflow-runtime/SKILL.md` schema to include the `"status"` field and define update rules.
  - Integrated status checks into `skills/resume-workflow/SKILL.md` and `skills/software-development-workflow/SKILL.md` to recommend retrying/running the exact interrupted skill when a checkpoint has status `"in_progress"` or `"failed"`.
  - Added status update instructions to all checkpoint-changing skills (`brainstorming`, `brainstorming-to-plan`, `plan-to-blueprint`, `blueprint-to-implementation`, `implementation-to-release`, `quick-fix`, `quick-feature`, `project-memory-bootstrap`, `project-memory-update`).

---

## [2.7.0] - 2026-07-03

### Added
- **Standardized Author Metadata**: Integrated professional author metadata across the framework.
  - Added structured author details (Kyle Dang, email, website), license (MIT), repository URL, creation date (`created_at: 2026-07-03`), and last update (`updated_at: 2026-07-03`) to the frontmatter of all 22 `SKILL.md` files.
  - Declared the `"author"` block at the root level of `MANIFEST.json` as the single source of truth, and bumped framework version to `2.7.0`.
  - Added an **Author** bio section to the end of `README.md`.
  - Enforced a strict no-signature constraint in Section 7 of `AI_RULES.md` to prevent agents from appending personal signatures to generated engineering plans, blueprints, or implementations.

---

## [2.6.0] - 2026-07-03

### Added
- **Command-Based Architecture**: Redesigned metadata system to support concise command interactions (`/command` style) instead of verbose skill folder name invocations, while preserving folder paths and skill names for 100% backward compatibility.
  - Added `command`, `aliases`, `category`, and `tags` to the frontmatter of all 22 `SKILL.md` files.
  - Re-structured `MANIFEST.json` list of skills from a string array to an array of objects detailing command properties, and added a `"categories"` configuration grouping the skills.
  - Updated all user-facing documentation (`USAGE.md`, `README.md`, `SKILLS.md`) to use short command invocation examples (e.g. `/workflow`, `/plan`, `/blueprint`, `/implement`).
  - Replaced legacy commands inside skill instruction files (e.g. `/plan-to-blueprint` -> `/blueprint`).

---

## [2.5.0] - 2026-07-03

### Changed
- **Workflow Phase Separation & Project Planning Refactor**: Refactored the Planning phase into Project Planning, separating project scope and technical details.
  - Slashed code implementation details, folder layout, databases, APIs, classes, SQL, and pseudo-code from the Planning phase (`planning-prompt-to-plan` and `brainstorming-to-plan`).
  - Strengthened `plan-to-blueprint` to read both brainstorming and plan files, consolidating all technical design specifications (database schemas, public APIs, sequence diagrams, migration/rollback strategy, folder structure) into a single technical design document.
  - Added "Workflow Phase Separation Policy" as Section 10 to `AI_RULES.md` and updated `AGENTS.md` to define these boundaries.
  - Updated `README.md`, `SKILLS.md`, and `INSTALL.md` to document the new boundaries.

---

## [2.4.6] - 2026-07-03

### Fixed
- **SDLC Checkpoint Alignment**: Fixed target checkpoint transitions in `brainstorming` and `brainstorming-to-plan` skills to write Checkpoint `3` (Architecture Analysis Complete) to `.session.json` upon successful execution (fixing legacy specs that erroneously set it to 1 or 2).

---

## [2.4.5] - 2026-07-03

### Changed
- **Active Runtime Context Tracking**: Mandated executing agents inside `initialize-workflow` and `workflow-runtime` skills to dynamically calculate and save active conversation token usage (calculated from local transcript JSONL logs) to the `"context_usage"` field in `.agents/.session.json` during state updates.

---

## [2.4.4] - 2026-07-03

### Added
- **Default Session Initialization**: Configured installation (`install.sh` / `install.ps1`) and update (`update.sh` / `update.ps1`) scripts to automatically create or upgrade `.agents/.session.json` to the new nested format with elegant initial values to prevent Webview loading issues on empty workspaces.

---

## [2.4.3] - 2026-07-03

### Changed
- **Unified Session State Schema**: Aligned the `.agents/.session.json` schema inside `workflow-runtime` skill with the rich, nested format expected by the VS Code UI Visualizer Extension (including `git`, `work_item`, `version`, `memory`, `rag`, and `context_usage` objects).

---

## [2.4.2] - 2026-07-03

### Changed
- **Strict Relative Path Guards**: Strengthened behavioral rules in `initialize-workflow` and `workflow-runtime` skills to explicitly force runtime agents to save workspace directory paths as `"."` under `.agents/.session.json` to eliminate absolute path outputs completely.

---

## [2.4.1] - 2026-07-03

### Changed
- **Relative Path Optimization**: Configured workspace session state and initialization scripts to report project paths using relative representations (e.g. `.`) rather than absolute paths to prevent local file path leakage.

---

## [2.4.0] - 2026-07-03

### Added
- **Configuration-Driven Releases (`release.config.json`)**: Refactored the release subsystem to read layout metadata from a centralized project configuration. Supports single projects, multi-module (backend/frontend), mobile, desktop, and monorepos.
- **Affected Module Detection**: Added Git diff scanning to identify modified modules and bump versions/changelogs only for affected components.
- **Shared Module Detection**: Added dependency propagation so that modifications to common folders (like `shared/`, `common/`, `libs/`) prompt the user to decide on dependent module updates.
- **Release Guide Document (`release-guide.md`)**: Created detailed documentation explaining release modes, schemas, and safety gates.
- **Auto-Detection Fallback**: Implemented automatic language/framework detection to suggest configuration structures to the user if `release.config.json` is missing.

---

## [2.3.0] - 2026-07-03

### Added
- **Multi-Agent Role Contracts (`agents/`)**: Added role specifications, artifact ownership rules, and execution constraints for `planner`, `architect`, `coder`, `reviewer`, and `release-manager` agents.
- **Handoff Runtime Schemas & State Files (`runtime/`)**: Created JSON schema specifications and tracking files for handoffs (`handoffs.json`), checkpoints (`checkpoints.json`), and system state (`state.schema.json`) to track role transitions and prevent illegal workspace alterations.
- **Script Support & Installers**: Updated `install.*`, `update.*`, and `uninstall.*` utility scripts to support deploying, upgrading, and removing the new multi-agent `agents/` and `runtime/` directories.

---

## [2.2.0] - 2026-07-03

### Added
- **Workflow Runtime Controller (`workflow-runtime`)**: Introduced a new core Skill that acts as the runtime controller for execution state management, session handling (`.agents/.session.json`), validation checkpoints, and resume-workflow recovery capabilities.
- **Unified Checkpoints and Heartbeats**: Added checkpoint transitions (1 to 7) and plain text heartbeat logging to all SDLC Feature and Fast-track/Quick skills to detect context drift (unexpected branch/work item/version changes) and ensure resumable, robust execution.

---

## [2.1.0] - 2026-07-03

### Added
- **Workflow Initialization Skill (`initialize-workflow`)**: Introduced a new core Skill acting as the mandatory entry point of the entire AI Engineering Workflow. It aggregates workspace validation, policy loading, project memory status, Git checking, active work item discovery, version detection, and tool inspection into a single runtime context.
- **Reference-Driven Initialization Check**: Updated all 12 core Skills to assume `initialize-workflow` has executed and to verify context before running, eliminating redundant environment and configuration parsing checks in individual Skills.

---

## [2.0.1] - 2026-07-03

### Changed
- **Plain Text Orchestrator Report**: Refactored the `software-development-workflow` output layout from Markdown tables to a clean, structured plain text block format to align with other Skill Completion Contracts and prevent UI line-wrap issues.

---

## [2.0.0] - 2026-07-03

### Added
- **Centralized Policy Architecture (`AI_RULES.md`)**: Created a centralized global policies file in the repository root as the single source of truth for all shared behaviors, constraints, and SDLC gates.
- **Reference-Driven Skills**: Refactored all core Skills (`software-development-workflow`, `brainstorming`, `brainstorming-to-plan`, `plan-to-blueprint`, `blueprint-to-implementation`, `quick-fix`, `quick-feature`, `implementation-to-release`, `project-memory-bootstrap`, `project-memory-update`, `project-rag-search`, `environment-bootstrap`, `environment-health`) to reference `AI_RULES.md` instead of duplicating rules, satisfying DRY principles and enabling policy-driven architecture.

---

## [1.9.1] - 2026-07-03

### Changed
- **Unicode Box Art Migration**: Replaced Unicode box art boundary boxes with native Markdown tables and plain text headers in all skill definitions (`brainstorming`, `quick-fix`, `quick-feature`, `software-development-workflow`, `environment-health`, `environment-bootstrap`) to guarantee stable font rendering across all IDEs and chat clients while preserving the behavioral anchor constraints.

---

## [1.9.0] - 2026-07-03

### Changed
- **Unified Global Approval Gate Policy**: Implemented strict approval gates before any state-changing action in the workspace (modifying source code, creating/deleting files, branch checkouts, merging, version bumps, commits, tags, pushing). Agents must display changes, list affected files, current branch, and stop to await `Y`/`Yes`/`Proceed`/`Continue`.
- **Pre-Implementation Git Gate**: Refactored `blueprint-to-implementation`, `quick-fix` (Phase 2), and `quick-feature` (Phase 2) to display the active branch and status, prompt the user with branch options (continue on branch, create new branch with suggested names `feature/FEAT-XXX-slug`, `fix/FIX-XXX-slug`, `quick/QUICK-XXX-slug`, or stop), and wait for approval before any coding.
- **Merge Gate & Release Workflow Order**: Refactored `implementation-to-release` to follow the strict sequential release workflow (Build/Test, Detect version, Update version, Update CHANGELOG, Approval, Commit, Create Tag `vX.Y.Z`, Push Branch, Push Tag). If not on main/master, the agent must explicitly ask for merge permission. Skipped Git steps automatically for Non-Git projects.
- **Workflow Orchestration Reminders**: Upgraded `software-development-workflow` to remind executing agents about branch and merge gates during Implementation and Release cases.

---

## [1.8.0] - 2026-07-03

### Changed
- **New Documentation Folders Alignment**: Refactored `quick-fix` and `quick-feature` Skills to conform to the new project directory architecture:
  - **`quick-fix`**: Generates Fix files under `docs/issues/FIX-XXX_issue_name.md` instead of `docs/brainstorming/`. Updates Phase 2 execution to read from `docs/issues/`.
  - **`quick-feature`**: Generates Spec files under `docs/quick/QUICK-XXX_feature_name.md` instead of `docs/brainstorming/`. Calculates IDs by scanning `docs/quick/`. Updates Phase 2 execution to read from `docs/quick/`.
- **Project Memory & RAG Upgrades**: Updated `project-memory-bootstrap`, `project-memory-update`, and `project-rag-search` Skills to index and search files inside `docs/issues/` and `docs/quick/` alongside standard SDLC folders.
- Preserved the existing standard workflow.

---

## [1.7.1] - 2026-07-03

### Changed
- **Rename fast-fix to quick-fix**: Renamed the `fast-fix` Skill directory to `skills/quick-fix/` and all internal/external CLI references to `/quick-fix`.
- **Mandatory Mode Active Blocks**: Added `🔒 QUICK-FEATURE MODE ACTIVE` and `🔒 QUICK-FIX MODE ACTIVE` behavioral anchor blocks to establish immediate approval gate boundaries.
- **Mandatory Specification Creation**: Enforced that `docs/brainstorming/FEAT-XXX_feature_name.md` (for `quick-feature`) and `docs/brainstorming/FIX-XXX_issue_name.md` (for `quick-fix`) must be generated during Phase 1. Source code modifications are strictly blocked until the user confirms with `Y` or `Yes`.

---

## [1.7.0] - 2026-07-03

### Added
- **New `quick-feature` Skill**: Introduced a lightweight parallel workflow designed specifically for low-risk, small feature requests (e.g. adding one API endpoint, button, dialog, filter, validation, search field, export function, configuration option). Eligible features bypass standard planning/blueprint overhead. Includes:
  - Scope/Eligibility Matrix (low impact, single module context).
  - Mini Feature Specification template generated at `docs/brainstorming/FEAT-XXX_feature_name.md`.
  - User Approval Gate blocking code modifications until explicit Y/N confirmation.
  - Automatic compilation/test verification and Quick Feature Summary output formatting.
  - Self-Validation checklist for compliance.

### Changed
- **Workflow Orchestration Integration**: Upgraded the `software-development-workflow` Skill to support the parallel **Option 3: Quick-Feature Workflow** track. The orchestrator now automatically classifies incoming tasks and recommends `quick-feature` based on scope, risk, and impact analysis of the `task_description`.
- Registered `quick-feature` in `MANIFEST.json` and cataloged it in `SKILLS.md`.

---

## [1.6.2] - 2026-07-03

### Changed
- **Two-Phase Quick-Fix Workflow**: Refactored the `quick-fix` Skill from an immediate implementation skill into a two-phase workflow with an explicit User Approval Gate:
  - **Phase 1 (Analysis)**: Generates a formal Fix document at `docs/brainstorming/FIX-XXX_issue_name.md` containing metadata, symptoms, root cause, proposed fix, acceptance criteria, and a test plan. Bypasses source code modifications.
  - **User Approval Gate**: Automatically stops after writing the Fix document and prompts the user `Continue? [Y/N]`.
  - **Phase 2 (Implementation)**: Executes minimal source code changes only after receiving explicit Y/yes confirmation from the user.
- Updated `skills/quick-fix/SKILL.md` to establish the `QUICK-FIX MODE ACTIVE` behavioral anchor and wrong behavior check patterns.

---

## [1.6.1] - 2026-07-03

### Fixed
- **CLI Updater macOS/BSD Compatibility**: Fixed a bug where `aiwf update` and `aiwf uninstall` failed to sync or remove skills on macOS because of the non-portable `\s` regex pattern in `sed`. Replaced it with a POSIX-compliant `[[:space:]]` pattern and added a grep filter to exclude target prefixes.
- Deployed identical fixes to both `update.sh` and `uninstall.sh`.

---

## [1.6.0] - 2026-07-03

### Added
- **New `quick-fix` Skill**: Introduced a lightweight parallel workflow designed specifically for low-risk, small bug fixes (e.g. routing errors, null pointers, typos, configuration changes, simple validations). Eligible fixes bypass the full SDLC (No Brainstorming, Planning, Blueprint, or ADR). Includes:
  - Scope/Eligibility Matrix (low impact, single module context).
  - Decision Matrix for auto-classification (Quick-Fix vs Standard Workflow).
  - Automatic compilation checks and test suite verification.
  - Comprehensive Quick-Fix Implementation Summary output formatting.
  - Verification checklist for compliance.

### Changed
- **Workflow Orchestration Integration**: Upgraded the `software-development-workflow` Skill to accept `task_description` input. The orchestrator now automatically classifies incoming tasks and recommends either the `quick-fix` track or the `brainstorming` standard workflow based on scope and risk analysis.
- Registered the `quick-fix` skill in `MANIFEST.json` and cataloged it in `SKILLS.md`.

---

## [1.5.5] - 2026-07-03

### Changed
- **Completion Report Layout Refactoring**: Refactored the `Self-Validation Checklist` and `Completion Report` text blocks in the `brainstorming` skill into beautiful, native Markdown tables and callout alert boxes to prevent ugly line wraps and layout breaks in chat interfaces.

---

## [1.5.4] - 2026-07-03

### Changed
- **Skill Renamed**: `idea-to-planning-prompt` → `brainstorming` — invocation is now `/brainstorming`. Directory renamed to `skills/brainstorming/`.
- **Skill Renamed**: `planning-prompt-to-plan` → `brainstorming-to-plan` — invocation is now `/brainstorming-to-plan`. Directory renamed to `skills/brainstorming-to-plan/`.
- Updated all cross-references in: `MANIFEST.json`, `SKILLS.md`, `README.md`, `INSTALL.md`, `USAGE.md`, `CHANGELOG.md`, and Skills: `software-development-workflow`, `environment-bootstrap`, `environment-health`, `project-rag-search`, `project-memory-update`.

---

## [1.5.3] - 2026-07-03

### Changed
- **Behavior Anchoring: brainstorming**: Root cause identified — previous guardrails were passive warnings that LLM helpfulness bias could override. Fixed with: (1) Mandatory First Output declaration block — AI must print "DISCOVERY MODE ACTIVE" verbatim before any other action, creating a behavioral commitment anchor; (2) Wrong Behavior Detection pattern — explicit checklist of prohibited tool calls with a right vs wrong examples table; (3) Restructured workflow with `[MANDATORY]` step before Step 1; (4) Identical SKILL.md deployed to both framework source and installed project `.agents/`.
- **Repository Metadata Sync**: Bumped framework version to `1.5.3` in `MANIFEST.json`.

---

## [1.5.2] - 2026-07-03

### Changed
- **Production Hardening: brainstorming**: Performed root cause analysis identifying 8 critical/high/medium defects. Refactored the Skill with: (1) Requirement Readiness Score gate (0–100, threshold 85), (2) explicit Y/N user confirmation before document generation, (3) free-text invocation replacing YAML input parsing, (4) corrected Feature labels during decomposition to prevent ID naming conflicts, (5) added Impact Analysis and Risk Analysis to discovery checklist, (6) top-level STOP RULE block preventing auto-transition to downstream phases, (7) expanded 14-section Brainstorming document template per production spec, (8) resolved Capability Boundary vs Completion Report conflict.
- **Repository Metadata Sync**: Bumped framework version to `1.5.2` in `MANIFEST.json`.

---

## [1.5.1] - 2026-07-03

### Changed
- **Strict Requirement Discovery & Feature Decomposition**: Refactored `brainstorming` skill to focus purely on read-only requirement discovery and solution discovery, preventing direct implementation or auto-execution of downstream tasks. Added multi-feature decomposition support.
- **Repository Metadata Sync**: Bumped framework version to `1.5.1` in `MANIFEST.json`.

---

## [1.5.0] - 2026-07-03

### Changed
- **Solution Architect Workshop Upgrade**: Refactored `brainstorming` (now Interactive Solution Discovery) to conduct in-depth architectural design reviews. It maps context, generates 2-3 significantly different solution options, provides trade-offs and complexity ratings, recommends the best choice, and requires user selection (`user_selection`) before writing `docs/brainstorming/` files.
- **Repository Metadata Sync**: Bumped framework version to `1.5.0` in `MANIFEST.json` and synchronized descriptions/inputs in `SKILLS.md`.

---

## [1.4.0] - 2026-07-03

### Added
- **Global Bootstrap Installers**: Added `bootstrap.sh` (macOS/Linux), `bootstrap.ps1` (Windows PowerShell), and `bootstrap.bat` (Windows CMD) to easily configure a global PATH environment variable one-time setup.
- **Global `aiwf` CLI Wrapper**: Added light-weight binary and script command-line wrappers redirecting project-level actions (`install`, `update`, `uninstall`, `doctor`, `version`) back to the framework repository location.
- **Diagnostics and Doctor Scripts**: Added `doctor.sh` and `doctor.ps1` to test the validity of PATH setups and project structure integrity.
- **Version Reporting CLI**: Added `version.sh` and `version.ps1` to display framework core metadata.
- **Windows CLI Complete parity**: Added `update.ps1` and `uninstall.ps1` to provide native CLI powershell support under Windows.

---

## [1.3.0] - 2026-07-03

### Added
- **Framework Installer**: Added `install.sh` (Linux/macOS) and `install.ps1` (Windows/PowerShell Core) to deploy framework files (`AI_RULES.md`, `MANIFEST.json`, `skills/`, `templates/`) into target projects under the `.agents/` folder.
- **Idempotency and Safeguards**: Both installers are fully idempotent, enforce Git repository detection, and prevent overwriting existing custom configs unless explicitly requested.
- **Framework Synchronizer**: Added `update.sh` to compare target versions and update changed skills/files without deleting user-created content.
- **Framework Uninstaller**: Added `uninstall.sh` to perform clean removals of only framework-managed files.
- **Package Manifest**: Updated `MANIFEST.json` to schema `1.3.0` containing repository URLs, supported OS list, and file structure rules.
- **New Folders**: Added placeholder `templates/` and `examples/` folders.

---

## [1.2.0] - 2026-07-03

### Added
- **New Skill: `create-adr`**: Added a dedicated skill under `skills/create-adr/SKILL.md` to generate Architecture Decision Records (ADRs) under `docs/adr/ADR-XXX_*.md`.
- **FEAT-XXX Padded Feature IDs**: Pinned Feature IDs to the unified `FEAT-001`, `FEAT-002`, `FEAT-003` prefix standard.
- **ADR Assessment & Validation Gates**:
  - `plan-to-blueprint` now assesses and recommends ADR requirements (it does not write ADR files).
  - `blueprint-to-implementation` now blocks execution and requests `/create-adr` if a blueprint requires an ADR that does not exist or is not Accepted.
  - `software-development-workflow` now detects pending ADR creation steps.

### Changed
- **Release Tracking**: Refactored `implementation-to-release` to document releases directly into `CHANGELOG.md` instead of creating release files.
- **Clean Documentation Folders**: Kept only the 4 core folders (`docs/brainstorming/`, `docs/plans/`, `docs/designs/`, and `docs/adr/`).
- **All Skills Refactored**: Refactored all 13 existing skills and framework files (README, SKILLS, INSTALL, AGENTS, MANIFEST) to conform to the `FEAT-XXX` format and simplified folders.

### Removed
- Removed legacy folders `docs/releases/` and `docs/archive/`.

---

## [1.1.0] - 2026-07-03

### Added
- **Feature-Centric Documentation Structure**: Added `docs/brainstorming/` (for discovery requirements), `docs/designs/` (for blueprints), `docs/releases/` (for release notes), `docs/adr/` (for Architectural Decision Records), and `docs/archive/` (for deprecated features).
- **Feature ID Traceability**: Introduced unified Feature IDs (e.g. `001`, `002`) to link all artifacts generated during a feature's lifecycle (Discovery -> Plan -> Blueprint -> Release).
- **ID Allocation Algorithm**: Standardized the Feature ID calculation to read only from `docs/brainstorming/`.

### Changed
- **Orchestrator Refactoring**: Updated `software-development-workflow` to track status based on Feature IDs and detect active phase files using the new directory structure.
- **Requirement Discovery Upgrade**: Updated `brainstorming` to write master requirements files under `docs/brainstorming/` formatted as `NNN_<feature_name>.md`. Tweak to include Traceability headers.
- **Planning Prompt to Plan Refactoring**: Updated `brainstorming-to-plan` to read from `docs/brainstorming/` and output plans to `docs/plans/` using Feature IDs.
- **Plan to Blueprint Refactoring**: Updated `plan-to-blueprint` to read plans from `docs/plans/` and output blueprints to `docs/designs/` using Feature IDs.
- **Blueprint Execution Refactoring**: Updated `blueprint-to-implementation` to use technical designs in `docs/designs/`.
- **Git Release Refactoring**: Updated `implementation-to-release` to output release logs to `docs/releases/` using Feature IDs.
- **Repository Metadata Sync**: Updated `MANIFEST.json` (bumped to 1.1.0), `README.md`, `SKILLS.md`, `INSTALL.md`, and `AGENTS.md` to document the new feature-centric layout and rules.

---

## [1.0.0] - 2026-07-03

### Added
- **AI Skill Library**: Initial collection of 13 modular AI Agent skills for managing the Software Development Life Cycle (SDLC).
- **Environment Bootstrapping & Diagnostics**: Added `environment-bootstrap` and `environment-health` skills for automated workspace provisioning and health checks.
- **Project Memory Management**: Added `project-memory-bootstrap` and `project-memory-update` for maintaining a persistent, memory-first workspace metadata layer.
- **RAG & Search capabilities**: Added `project-rag-search` for lightning-fast semantic context retrieval.
- **Planning & Design Engine**: Added `brainstorming-to-plan` and `plan-to-blueprint` to build implementation plans and blueprints from structured requirements.
- **Code implementation**: Added `blueprint-to-implementation` and `implementation-to-release` to generate code and release software in a standardized, controlled fashion.
- **Frontend Design Thinking**: Added `frontend-design` containing core styling guidelines and accessibility rules.
- **OKR Reporting**: Added `okr-report-generator` for processing objective matrices.
- **Workflow Orchestration**: Added `software-development-workflow` to supervise the current phase of development.
- **Package Manifest**: Added `MANIFEST.json` containing machine-readable definitions for the skill library.
- **Documentation**: Added `README.md`, `INSTALL.md`, `SKILLS.md`, `LICENSE`, and this `CHANGELOG.md`.

### Changed
- **Interactive Requirement Discovery**: Refactored the `brainstorming` skill to use a 10-phase interactive workshop model. Calculates a Readiness Score and prompts clarifications when below 85 before producing a planning prompt.
