# AI Rules & Global Policies

This document is the single source of truth for all shared behaviors, constraints, and policies across all AI Engineering Workflow Skills. All Skills must refer to these policies to prevent duplication and ensure consistency.

---

### AI-First Execution Contract

In autonomous workflow mode, every Skill and script MUST return one structured command envelope containing status, side effects, evidence, and next action. The Workflow Supervisor MUST execute automatic next actions until completion, failure, a cycle, a budget limit, or a strategic human gate. Internal CLI commands MUST NOT be presented as instructions for the user to type.

Local read, compile, lint, and test activities are runtime-owned safe capabilities. Network, destructive, production, and release activities remain explicit approval capabilities.

### 1. Approval Gate Policy

The framework is strictly **approval-driven**, but allows dual execution modes depending on project configurations:

- **Legacy Mode (`workflow_mode=legacy`)**: Every state-changing action (modifying files, commits, tags, branches) requires explicit human confirmation through native Agent/IDE `ask_question` first. `workflow_runtime.py prompt select` is only a fallback bridge when the host cannot call native `ask_question` directly.
- **Autonomous Mode (`workflow_mode=autonomous`)**: Workflow execution is managed by the **Workflow Supervisor**. State-changing actions during intermediate compilation, test runs, and static linting are automated. The supervisor strictly halts only at the following **3 Strategic Human Approval Gates**:
  1. **Gate 1 â€” Workflow Selection Approval**: Human selects the workflow path only when the request is ambiguous or multiple workflow options are valid.
  2. **Gate 2 â€” Blueprint Approval**: Human validates technical architecture and contracts after the Blueprint has passed all internal review loops.
  3. **Gate 3 â€” Release Approval**: Human validates production release risk.

*   **No Double Confirmation Policy**: Any action already approved or selected by the user through native Agent/IDE `ask_question`, or through `workflow_runtime.py prompt select` when used as a fallback bridge, MUST NOT be confirmed again in chat. The Agent must directly execute the selected action after receiving the structured prompt result, except selecting the dangerous `unrestricted` mode, which still requires an explicit high-impact confirmation.

*   **Pre-Approval Artifact Self-Review Policy**: From roadmap/discovery through Specification, Implementation Plan, and Technical Blueprint, the Agent MUST self-review every generated artifact before moving to the next artifact. The review MUST check the user request, the active Skill, this `AI_RULES.md`, traceability, artifact placement, relative-path rules, and `document-compliance-assessment` requirements. If the review FAILS, the Agent MUST state the exact failed points, revise only those failed points, and repeat the review/revision loop until PASS. The Agent MUST NOT request user approval for intermediate roadmap, brainstorming, specification, or plan artifacts in the continuous workflow unless required to resolve ambiguity, missing information, or workflow selection. The ONLY mandatory pre-implementation human approval stop is after the Technical Blueprint has passed internal review.

*   **Large Feature Roadmap-First Policy**: Any large, multi-phase, system-level, cross-module, or high-risk feature MUST create a reviewed Roadmap artifact before Implementation Plan or Blueprint generation. The Roadmap MUST live under the semantic feature documentation shape `docs/features/<feature-family>/roadmaps/<WORK_ITEM_ID>_<slug>_roadmap.md` and contain complete phase inventory, feature coverage matrix, requirement-to-phase mapping, dependency order, release slices, risks, and explicit "not missed" checks. Planning and Blueprint phases MUST read and preserve the Roadmap shape. If a large/multi-phase workflow has no reviewed Roadmap, the workflow is BLOCKED and must return to discovery.

*   **Pre-Approval Review Evidence Contract**: Every roadmap/discovery, Specification, Implementation Plan, and Technical Blueprint artifact MUST contain an `Internal Review Evidence` section before the Agent advances to the next phase. This section MUST list: reviewer roles used, source artifacts reviewed, checklist items, PASS/FAIL result, exact failed points when any exist, revision scope, re-review count, document-compliance score, and relative-path scan result. Missing review evidence is an automatic FAIL. A review result may be PASS only when all failed points are fixed, the document-compliance score is at least 95/100, and no no-go condition exists.

*   **Blueprint Engineering Quality Gate**: Every Blueprint that can lead to source-code changes, including `quick-fix`, `quick-feature`, and standard feature Blueprints, MUST fail review and MUST NOT be presented for approval unless `Internal Review Evidence` explicitly proves all of the following: canonical `CODE_BLOCK_GATE: PASS`; every touched source file has a projected line budget under 500 physical lines; any split caused by the 500-line rule uses one family-name folder plus one facade/barrel/aggregate entry file; every affected language is mapped to an active strict language profile; and the exact build/lint/typecheck/test commands for those languages are listed. `CODE_BLOCK_GATE: NOT_APPLICABLE` is valid only for docs/config-only Blueprints with no implementation-ready code blocks and no source-code write surface. Missing, `PENDING`, `NOTE`, `N/A`, or failed evidence for any item is an automatic `FAIL`.

*   **Strict Reviewer Accountability & No Rubber-Stamp Policy**: Every reviewer, architecture reviewer, QC reviewer, or coordinator acting as a gatekeeper is personally responsible for blocking weak, incomplete, inconsistent, or non-compliant artifacts. Reviewers MUST NOT approve artifacts merely because the owning agent claims completion, because a checklist says PASS, or because the workflow is expected to continue. Reviewers MUST inspect the actual artifact content, referenced source artifacts, phase coverage, traceability, path hygiene, and evidence. A review PASS is legal only when the reviewer can cite concrete artifact sections, tables, paths, or report entries proving every required criterion. If any requirement is missing, thin, vague, contradictory, stale, misplaced, out of phase order, or unsupported by evidence, the reviewer MUST return `FAIL`.

*   **Reviewer Failed-Point Repair Contract**: When a review FAILS, the reviewer MUST report only the exact failed points that need correction, with enough location detail for the owning phase agent to repair them without reinterpreting the whole artifact. Each failed point MUST include: artifact path, section/table/field, violated rule or requirement, why it fails, and the minimum correction required. The owning phase agent MUST revise only those failed points, preserve valid content, and return the artifact for re-review. The coordinator MUST NOT advance to the next phase, request user approval, start implementation, or broaden the scope while any failed point remains unresolved. A second review MUST verify the changed sections directly and record whether each failed point is fixed, still failing, or newly regressed.
*   **Pre-Approval Self-Correction Loop**: If an artifact review FAILS, the Agent MUST NOT proceed to the next phase, request user approval, or create downstream artifacts. The owning phase agent MUST revise only the explicitly failed points, preserve all already-valid content, and rerun the same review checklist. The loop repeats until PASS. The FAIL report MUST be specific enough for a different agent to fix the same points without reinterpreting the whole artifact.

*   **Blueprint Approval Structured Prompt Requirement**: After the reviewed Technical Blueprint reaches PASS, the Agent MUST request final Blueprint Approval through the native Agent/IDE `ask_question` tool first. `aiwf prompt select` is only the fallback bridge for hosts that intercept its `<interactive_prompt type="ask_question">` payload or can provide stdin to the subprocess. A plain chat message such as "approve?", "Y/N", "duyet?", or "please confirm" is NOT a valid primary Blueprint Approval gate. If `aiwf prompt select` returns `PROMPT_UNAVAILABLE`, this means no prompt was shown and no user selection was received; it MUST NOT be treated as `Cancel`. When native `ask_question` is available, the Agent MUST use it immediately. If neither native `ask_question` nor prompt-select rendering is available, the Agent MUST explicitly state that structured prompting is unavailable, keep the workflow stopped at Blueprint Approval, and treat any chat response only as fallback evidence. The Agent MUST NOT mark the Blueprint approved or implement code before explicit approval evidence exists.

*   **Blueprint Approval Scope Binding**: Blueprint Approval evidence MUST be bound to the exact `work_item_id` and Blueprint path it approves. An approval record is valid only when the approval work item, Blueprint filename/path, and Blueprint frontmatter (`feature_id`, `issue_id`, `quick_id`, or `work_item_id`) all resolve to the same work item. Approval from a different work item, stale active workflow, global state, full-access authorization, or autonomous delivery authorization MUST NOT unlock implementation. Full-access mode may continue internal pre-approval phases, but it MUST NEVER auto-approve the final Blueprint Approval gate.

*   **Frontend Design Skill Binding Policy**: Any request, artifact, Blueprint, implementation, or review that creates, changes, or specifies frontend design MUST use the `frontend-design` Skill before making design decisions. This includes UI/UX flows, frontend components, page layout, spacing, typography, color, visual hierarchy, icons, animation, aesthetic styling, and design-system choices. If the work only changes backend logic with no user-facing interface/design impact, this binding is not required. `frontend-design` produces design decisions and acceptance criteria; it is not visual proof by itself. Implemented UI changes MUST pass the `frontend-visual-debug` evidence gate before the Agent may claim the UI is correct.
    *   **Mandatory Mobile-First Hierarchy (`Mobile -> Desktop -> Tablet`)**: Every frontend architecture, component layout, and design system MUST be conceived and developed with strict **Mobile First** priority: **Mobile (`375px - 480px`) -> Desktop (`1024px - 1440px+`) -> Tablet (`768px - 1024px`)**. Designing desktop-first and shrinking down is strictly prohibited. The mobile layout establishes the essential content hierarchy, touch targets (minimum 44x44px), compact navigation, and responsive typography, which are then progressively enhanced for desktop and tablet viewports.

---

## 1A. Workflow Supervisor Execution Policy

- **Lifecycle Ownership**: The Workflow Supervisor owns the thread execution loop, event routing, and checkpoint resume. Worker agents execute assigned micro-tasks only and cannot spawn other workers or edit workflow states directly.
- **Retry & Fail-safe**: Failed agent compilations automatically trigger retries up to 3 times. If failures persist, the supervisor halts execution, escalates to the Debug Agent, and notifies the user.
- **Suggestion Gate Bypass**: When tasks are triggered autonomously by the Supervisor loop, typical suggestion confirmation alerts are bypassed.

---

## 1B. Permission Model Separation

- **Workflow Permission**: Grants the supervisor authorization to read/write state checkpoints and run local verification test scripts.
- **Release Permission**: Controls packaging, version tagging, and git pushes. Release permission is NEVER automated and strictly requires user confirmation.

---

## 2. Git Workflow Policy

All Git actions must be performed with explicit visibility and approval.

*   **Branch Strategy**:
    *   All work should occur on a dedicated feature/fix/quick branch.
    *   **Feature Branches**: Named `feature/FEAT-XXX-slug` (from `docs/brainstorming/`).
    *   **Fix Branches**: Named `fix/FIX-XXX-slug` (from `docs/issues/`).
    *   **Quick Feature Branches**: Named `quick/QUICK-XXX-slug` (from `docs/quick/`).
*   **Branch Management**:
    *   Never create, switch, check out, or delete branches automatically.
    *   Before coding, run `git branch --show-current` and `git status --short`. Recommend branch names and wait for explicit choice.
*   **Dirty Tree Handling**:
    *   If the working tree is dirty or has uncommitted changes, warn the user.
*   **Commit, Tag, and Push**:
    *   Never perform `git commit`, `git tag`, or `git push` automatically. Always prompt the user for approval first.
    *   Tags must use the format `vX.Y.Z`.
*   **Non-Git Projects**:
    *   If no `.git` directory is detected, skip Git branch/merge/commit/push steps entirely, but still execute build, test, and summary actions.

---

## 3. Memory First Policy

To prevent context overload and improve accuracy, all operations must prioritize the Project Memory over directory scans.

*   **Sequence**:
    1.  **Project Memory**: Consult `<memory_root>/project-summary.md` and module configuration first to identify structure, API patterns, and code boundaries.
    2.  **RAG Search**: Query the RAG vector store or memory indexes for specific files or APIs.
    3.  **Targeted Source Inspection**: Inspect ONLY the files directly relevant to the feature or issue.
    4.  **User Questions**: Ask the user clarifying questions only when memory and targeted inspection do not resolve ambiguity.
*   **Constraints**:
    *   Never scan the entire repository (e.g., wild recursive greps) as a first step.
    *   Always consult Project Memory before asking the user for design guidance.

---

## 4. RAG Policy

Retrieval-Augmented Generation searches must follow a strict priority ordering.

*   **Retrieval Hierarchy**:
    *   **Level 1**: Project Memory (`project-summary.md`, area and module documents under `memory_root`).
    *   **Level 2**: Roadmaps, Discovery & Specifications (`docs/roadmaps/`, `docs/brainstorming/`, `docs/issues/`, `docs/quick/`).
    *   **Level 3**: Implementation Plans (`docs/plans/`).
    *   **Level 4**: Technical Blueprints (`docs/blueprints/`).
    *   **Level 5**: Architectural Decision Records (`docs/adr/`).
    *   **Level 6**: Targeted source code inspection (only for files identified in Levels 1â€“5).
*   **Chunk Selection & Fallback**:
    *   Rank results by similarity score.
    *   Fallback to adjacent modules or documentation if direct matches are not found.
    *   Never run full repository scans or generic searches if RAG results are available.

---

## 5. Artifact Policy

The documentation architecture enforces strict separation of concerns.

*   **Directory Structure**:
    | Directory | Purpose | Naming Format |
    | :--- | :--- | :--- |
    | `docs/features/` | Semantic feature families | `<feature-family>/README.md` |
    | `docs/features/<feature-family>/roadmaps/` | Large Feature Roadmaps | `<WORK_ITEM_ID>_<slug>_roadmap.md` |
    | `docs/features/<feature-family>/brainstorming/` | Requirements Discovery (Standard Features) | `<WORK_ITEM_ID>_<slug>.md` |
    | `docs/features/<feature-family>/plans/` | Implementation Plans | `<WORK_ITEM_ID>_<slug>_plan.md` |
    | `docs/features/<feature-family>/blueprints/` | Technical Blueprints | `<WORK_ITEM_ID>_<slug>_blueprint.md` |
    | `docs/features/<feature-family>/issues/` | Bug Fix Specifications (Quick-Fix) | `<WORK_ITEM_ID>_<slug>.md` |
    | `docs/features/<feature-family>/quick/` | Quick Feature Specifications | `<WORK_ITEM_ID>_<slug>.md` |
    | `docs/adr/` | Architectural Decision Records | `ADR-XXX_slug.md` |
    | `docs/features/<feature-family>/debug/` | Debug and Build Diagnostics | `<WORK_ITEM_ID>_<slug>_debug.md` |
    | `docs/features/<feature-family>/verification/` | Final Quality Gate Reports | `<WORK_ITEM_ID>_<slug>_verify.md` |
    | `docs/features/<feature-family>/reports/` | Post-implementation evidence reports | `<WORK_ITEM_ID>_<slug>_post_implementation_report.md` |
    | `docs/releases/` | Release Notes & Change Logs | `RELEASE-XXX_slug.md` |
    | `docs/archive/` | Historical/Retired Artifacts | As needed |
*   **Semantic Feature Documentation Contract**:
    *   Every new FEAT/FIX/QUICK artifact MUST be stored under `docs/features/<feature-family>/<stage>/...`.
    *   `<feature-family>` is a semantic product/domain family, not a work item ID. Examples: `visualizer`, `telegram`, `workflow-runtime`, `interactive-docs`, `project-memory`, `vir`, `cloud-platform`, `release-public-export`, `agent-orchestration`.
    *   Agents MUST classify the feature family by reading the artifact content, not by copying the `FEAT-*`, `FIX-*`, or `QUICK-*` identifier. Required evidence includes filename, YAML frontmatter, title, first headings, summary/problem statement, and linked source artifacts.
    *   Every feature family MUST maintain `docs/features/<feature-family>/README.md` as the cross-artifact index. The index MUST link all roadmaps, brainstorming/specs, plans, blueprints, debug reports, verification reports, final reports, screenshots, ADRs, and release artifacts that belong to the feature family.
    *   New flat workflow artifacts directly under `docs/brainstorming/`, `docs/plans/`, `docs/blueprints/`, `docs/issues/`, `docs/quick/`, `docs/debug/`, `docs/verification/`, or `docs/reports/` are forbidden, except `.gitkeep` and legacy files awaiting semantic migration.
    *   Existing flat files and former work-item folders are legacy read-only inputs. Agents may read them, migrate them, or link them from a migration report, but MUST NOT create new flat files or new `docs/work-items/<WORK_ITEM_ID>_<slug>/` folders.
    *   Multi-phase features use the same semantic feature family folder, then stage-specific `master/` and `phase-NN-<phase-slug>/` folders when needed.
*   **Relative Paths**: All links inside documents must use relative file paths/links. Absolute paths (e.g., `file:///Users/...`) are strictly prohibited in project artifacts.
*   **Metadata**: Every document must begin with YAML frontmatter specifying its `artifact_type`, `feature_id`/`issue_id`, `workflow`, `status`, and tracking links.
*   **Plan Synchronization**: Any IDE-level execution plan (`implementation_plan.md`) approved by the user MUST be copied into the canonical semantic feature folder before Blueprint or implementation work begins, for example `docs/features/<feature-family>/plans/FEAT-XXX_slug_plan.md`, `docs/features/<feature-family>/issues/FIX-XXX_slug.md`, or `docs/features/<feature-family>/quick/QUICK-XXX_slug.md`. Keeping an approved plan only in an IDE brain/temp directory is a serious workflow violation.

---

## 6. Versioning Policy

We strictly adhere to Semantic Versioning (SemVer).

*   **Format**: `vX.Y.Z` (e.g., `v1.9.0`)
*   **Bumping Rules**:
    *   **Patch (`Z`)**: Bug fixes and backward-compatible security updates.
    *   **Minor (`Y`)**: Backward-compatible new features, specs, or skills.
    *   **Major (`X`)**: Backward-incompatible architectural changes.
*   **Tagging**: Git tags must match the exact version prefix: `vX.Y.Z`.

---

## 7. Documentation Policy

Documentation must remain clean, professional, and easy to parse.

*   **Markdown Standards**:
    *   Use GitHub Flavored Markdown (GFM).
    *   Always use Markdown tables instead of Unicode box art drawings for reports, metrics, and logs to avoid rendering issues.
    *   Include clear, clean headers and checklists.
*   **Metadata**:
    *   Keep YAML blocks simple, clean, and placed at the absolute start of files.
    *   **Strict Constraint**: Never place author information inside prompt bodies. Never append signatures, names, emails, or personal comments to generated planning, blueprint, or implementation documents. Author metadata must belong only to `SKILL.md` frontmatter, `MANIFEST.json`, and `README.md`.
*   **Prompt Boundary XML Tagging (Claude Optimization)**:
    *   To prevent context leakage and confusion when mixing instructions and codebase files, use standard XML tags (e.g. `<instructions>`, `<context>`, `<file_content>`) to encapsulate structural payload boundaries.
    *   Example: Wrap codebase contents in `<file_content filepath="path/to/file">...</file_content>` tags to help Claude distinguish instruction sets from project code.

---

## 8. Testing Policy

Reliability is enforced through automated builds, testing, and runtime validation.

*   **Verification Gates**:
    *   Before any code change is finalized, you must verify compilation, run the test suite, execute the Runtime Validation Pipeline, and perform DDD/Clean Architecture Validation.
    *   **Runtime Validation Requirement**: A feature is considered complete ONLY when all the following runtime validation steps pass successfully:
        1. **Build/Compile**: PASS (Command used: `go build` / `npm run build` / etc.)
        2. **Static Analysis & Lint**: PASS (Command used: `go vet` / `ruff` / etc.)
        3. **Unit Tests**: PASS (Command used: `go test` / `pytest` / etc.)
        4. **Runtime Startup**: PASS (Process starts without immediate crashes, panic, traceback, or exit errors)
        5. **Readiness Detection**: PASS (Process binds to TCP ports or passes HTTP /health /ready HTTP status 200 checks within 15 seconds)
        6. **Runtime Smoke Tests**: PASS (Simulated request/response loop, WebSocket, worker task, or database read/write executes successfully)
        7. **Health Checks**: PASS (Resources and telemetry data reporting are healthy)
        8. **Graceful Shutdown**: PASS (Process terminates cleanly via SIGTERM / exit code = 0, releasing all bound ports and resources without leaks)
        9. **DDD / Clean Architecture Validation**: PASS (Architecture Compliance Score >= 95/100, no Critical Architecture Violations)
    *   **Strict Rule**: Passing unit tests alone MUST NEVER mark a feature as completed.
    *   **Debug & Verify Quality Gates**: All standard feature cycles must pass through `implementation-to-debug` (compilation, linter, tests, and runtime pipeline validation) followed by `debug-to-verify` (blueprint compliance, runtime checks, architecture verification, and Go/No-Go decision).
    *   **Post-Implementation Automated Quality Loop**: After implementation, the workflow MUST continue automatically through the following gates before reporting completion to the user or recommending release. These post-implementation commands do not require a new Blueprint. If the implementation started from an approved Blueprint, use that Blueprint as the primary review baseline. If the changes are maintenance/release-only work without an active Blueprint, use the explicit user request, reviewed Git diff, project rules, and changed-file evidence as the review baseline.
        1. **Code Review Gate**: Use `code-standard-review` to review every changed file against the approved Blueprint when one exists, otherwise against the explicit user request and release diff, plus project rules, coding standards, architecture boundaries, security expectations, and scope limits.
        2. **Code Validation Gate**: Run targeted build, lint, typecheck, dependency-direction checks, schema/config validation, and any project-specific validators directly related to the changed files.
        3. **Debug/Test Gate**: Run targeted tests for the modified components. For `pytest`, use `pytest -v -s <related_test_file_or_directory> 2>&1 | tee .agents/runtime/tests.log`.
        4. **Real Runtime Case Gate**: Exercise at least one real user/runtime path without mocks, fake test doubles, or fabricated data. Use the real CLI/API/IPC/database/service/browser surface that the feature affects. Seed data is allowed only when it is created through real application interfaces and cleaned up afterward.
        5. **Frontend Browser Evidence Gate & E2E Visual Automation Loop**: If the change affects UI, frontend behavior, layout, visual state, navigation, or user interaction, verify it via automated end-to-end browser execution and capture screenshots across all viewports. Prefer IDE browser tools when available; otherwise use a browser reachable via Chrome DevTools Protocol (CDP) or real browser automation (Playwright/Puppeteer). Designing or implementing without visual verification is strictly prohibited.
            *   **Mandatory Closed-Loop Cycle (`Automation -> Screenshot -> Validate -> Fix -> Repeat`)**:
                1. **Automation**: Launch the development server, navigate to the target route/view, and automatically execute real user interaction flows (clicks, inputs, submissions, navigation).
                2. **Screenshot**: Capture high-resolution visual evidence at all 3 required breakpoints: **Mobile (`375px/390px`)**, **Desktop (`1440px/1920px`)**, and **Tablet (`768px/820px`)**, plus dynamic visual states (modals, dropdowns, error toasts).
                3. **Validate**: Inspect visual DOM, layout integrity, touch targets (>= 44x44px), text clipping/wrapping, contrast, network calls, and browser console logs.
                4. **Fix & Retry Loop**: If ANY visual defect, layout breakage, text overlap, overflow, responsive failure, or console error is detected, the Agent MUST immediately fix the source code and rerun the cycle (Automation -> Screenshot -> Validate).
                5. **Completion Gate**: The task MUST NOT be marked complete or PASS until zero visual errors remain and all 3 viewports render flawlessly. Simply opening a browser or taking a single screenshot without multi-breakpoint verification is an automatic FAIL.
                6. **AI/IDE Execution Contract**: The Agent or IDE supervisor MUST invoke the structured `visual e2e` runner automatically after implementation, consume its JSON result, apply `next_action=fix_source_and_rerun` when blocked, and rerun the complete ordered matrix. The user is not required to type internal commands or manually coordinate the loop.
        6. **Final Evidence Report Gate**: Generate a Markdown report under `docs/reports/` summarizing code review, validation, debug/tests, real runtime case, browser/CDP evidence, screenshots across Mobile/Desktop/Tablet, cleanup, remaining risks, and final PASS/FAIL. Screenshots MUST be stored under `docs/reports/assets/<work-item-id>/` and linked with relative Markdown paths.
    *   **No Mock-Only Completion Rule**: Unit tests, mocked tests, reflection tests, or fake-data-only checks MUST NOT mark implementation complete when the changed behavior has a real runtime surface. Real runtime evidence is mandatory unless the report explains why no runtime surface exists.
*   **Failure Behavior**:
    *   If building or compiling fails, or if any test fails, or if runtime validation fails: print stdout/stderr/crash logs.
    *   **STOP** immediately. Set status to `Failed verification` and do not proceed with commit, verify, or release activities. Apply self-healing rules (up to 3 retries) within task scope if applicable.
*   **Background Test Progress Notification**:
    *   CÃ¡c tiáº¿n trÃ¬nh test cháº¡y ngáº§m (background tests) báº¯t buá»™c pháº£i theo dÃµi tiáº¿n trÃ¬nh vÃ  cá»© má»—i 5% tiáº¿n Ä‘á»™ hoÃ n thÃ nh pháº£i gá»­i thÃ´ng bÃ¡o cáº­p nháº­t lÃªn giao diá»‡n/há»‡ thá»‘ng hoáº·c logs má»™t láº§n Ä‘á»ƒ ngÆ°á»i dÃ¹ng dá»… dÃ ng theo dÃµi trá»±c quan.
    *   For any background or asynchronous test execution processes, the agent or test coordinator must track execution progress and output a progress notification or log update exactly every 5% of completed tests.

---

## 9. Explicit Release Policy

Release is NEVER automatic. Completion of implementation, compilation, or verification (passing all tests and quality gates) does NOT grant permission to perform release activities.

The AI must NEVER update version numbers, modify `CHANGELOG.md`, create git commits, tags, merges, pushes, or invoke the `implementation-to-release` skill unless the user has explicitly requested a Release (e.g. via keywords like `/release`, `release`, `create release`, `publish release`, `bump version`, `commit and push`, or `tag this version`). 

If no explicit release request is given by the user, the workflow MUST STOP after the Verification phase, recommend running Release, and wait for input.

*   **Release Sequence**:
    1.  **Determine Release Context**: If an active workflow/work item exists, this is a Workflow Release and must use that workflow's verification evidence. If no active workflow exists but the current user turn explicitly requests release, this is an Explicit Maintenance Release and must use reviewed Git diff plus targeted validation evidence instead of requiring a Blueprint.
    2.  **Verify Status Check**: For Workflow Release, check `docs/features/<feature-family>/verification/<WORK_ITEM_ID>_<slug>_verify.md` and ensure the verification status is `PASS`. If `FAIL` or missing, STOP the workflow and return to the debug phase. For Explicit Maintenance Release, do not require a Blueprint or workflow verification artifact; instead list the release diff, exclude unrelated files, and run targeted validation for the files being released.
    3.  **Build & Test**: Compile the affected components and run targeted tests/validators directly related to the changed files. Run the full test suite only when the user requests it or the release affects broad shared behavior.
    4.  **Detect Version**: Determine the current project version.
    5.  **Update Version**: Update the version strings across project config files (requires approval).
    6.  **Update CHANGELOG**: Write release notes into `CHANGELOG.md` under a new version heading (requires approval).
    7.  **Merge (if applicable)**: Run the Release Gate; if on a non-main branch, ask whether to merge and await approval.
    8.  **Approval Gate**: Explain the final Git commit, tag, and push actions, listing all modified files and branch, then request final release approval.
    9.  **Commit**: Commit version files and `CHANGELOG.md`.
    10. **Git Tag**: Tag the release commit as `vX.Y.Z`.
    11. **Push Branch**: Push the release branch to the remote repository.
    12. **Push Tag**: Push the tag to the remote repository.

---

## 10. Workflow Phase Separation Policy

To eliminate duplicated information, reduce token usage, and maintain clear separation of concerns, the **Planning** and **Blueprint** phases have distinct, non-overlapping responsibilities:

*   **Project Planning Phase (`docs/plans/`)**:
    *   Focusses entirely on project management, scope, deliverables, and risk mitigation.
    *   **Strict Constraints**: Planning documents must **NEVER** describe code implementations, define classes, define functions or interfaces, define database tables/schemas/SQL, define directory or folder layouts, or generate pseudo-code.
    *   The document must remain understandable by both technical and non-technical stakeholders.
*   **Technical Design Blueprint Phase (`docs/blueprints/`)**:
    *   Acts as the **single source of technical truth** and the **Implementation Contract** for code changes.
    *   **Strict Quality Constraints**: The Design Blueprint must contain complete technical decisions and specs. It is strictly forbidden to use placeholders (`...`, `etc.`, `TBD`, `to be decided`, `future work`) or generic instructions (`modify related files`, `update existing logic`). Every single affected file, API contract, and algorithm must be explicitly defined and documented.
    *   Owns all technical specifications, including: architecture layouts, sequence and interaction flows (e.g., Mermaid diagrams), class and method signatures (with types), database schemas and migration scripts, folder structures, error handling, security validations, and test strategies.
    *   It references the Project Plan for high-level guidance but does not duplicate its sections.

---

## 11. Shared Validation Engine Policy

All code-generating workflows (`blueprint-to-implementation`, `quick-fix`, `quick-feature`) must run an automated validation pipeline before reporting status.

*   **Command Auto-Detection**:
    *   Automatically scan the workspace for files indicating the project technology stack:
        *   `package.json`: `npm run build`, `npm run lint`, `npm test` or `npm run test`, `npm run typecheck`.
        *   `Makefile`: `make`, `make build`, `make test`.
        *   `go.mod`: `go build ./...`, `go test ./...`.
        *   `pyproject.toml` / `pytest.ini` / `requirements.txt` / `setup.py`: `pytest`, `python -m pytest`, `pylint`, `black --check`.
        *   `Cargo.toml`: `cargo build`, `cargo test`.
        *   `tsconfig.json`: `tsc --noEmit`.
    *   If a category has no config file, mark it as `Not Configured`.
*   **Execution & Self-Fix Loop**:
    1.  Run the validation command.
    2.  If the command fails:
        *   Analyze the log files to locate errors (compilation, linter, tests).
        *   **Scope Protection Rule**: Automatically fix issues ONLY if they are inside the scope of files modified by the current active task. Never refactor or edit unrelated modules/code.
        *   Re-run validation.
        *   Allow up to a maximum of **3 retries**.
    3.  If validation still fails after retries, or if the fix is unsafe/out of scope:
        *   **STOP** immediately. Set status to `FAILED`.
        *   Never claim implementation complete.
        *   Do not perform git commit, tag, or push.
        *   Recommend running `/debug`.
*   **Completion Criteria**:
    *   Status is `PASS` only when:
        *   Build: `PASS` or `Not Configured`
        *   Lint: `PASS` or `Not Configured`
        *   Typecheck: `PASS` or `Not Configured`
        *   Tests: `PASS` or `Not Configured`
        *   Self Review: `PASS` (code is clean, well-logged, free of dead code)

---

## 12. Session State Tracking Policy

To keep the VS Code Visualizer Dashboard synchronized in real-time with minimum I/O overhead, the active workflow state, step logging, and token count must be updated progressively during execution using a split-state engine under `.agents/state/`.

*   **Split State Files**:
    *   State is split into 8 specialized JSON files inside `.agents/state/`: `context.json`, `workflow.json`, `runtime.json`, `approvals.json`, `usage.json`, `agents.json`, `rules.json`, `recovery.json`.
    *   The monolithic `.agents/.session.json` is a derivative compatibility view generated by aggregate sync.
*   **Atomic Writing**:
    *   To prevent file corruption and partial reads, all updates to individual state files inside `.agents/state/` and `.agents/.session.json` MUST be performed atomically.
    *   First, write the complete JSON content to a temporary file: `<filename>.tmp`.
    *   Then, rename/replace the temporary file to the final destination.
*   **Bi-directional Synchronization**:
    *   Any writes to sub-state files automatically rebuild `.session.json` (Aggregate).
    *   Any external writes to `.session.json` are automatically parsed back to sub-state files (Deconstruct) upon CLI invocation to prevent drift.
*   **Progressive Updates**:
    *   Every Skill must update the session state files progressively during execution, specifically at:
        1. **Skill start**: Immediately set status to `in_progress`, current_skill, current_command, and start logging in `runtime.json`.
        2. **Each major step/checkpoint transition**: Update current_step and append log lines to current_logs in `runtime.json`.
        3. **Before running long-running/async commands**: Set step/logs indicating the command is launching.
        4. **After command results**: Append output highlights, status, or errors to the logs.
        5. **On failure**: Set status to `failed` and append error logs.
        6. **On completion**: Set status to `completed` and update suggested next skill/command in `workflow.json` / `runtime.json`.
*   **Preserving & Detecting Conversation ID**:
    *   On every initialize/resume workflow entry, the runtime MUST detect the active conversation ID first. If the active conversation ID differs from `context.json` (or `.agents/.session.json`), update it before calculating context usage. Preserve workflow state, but refresh active context usage using the new transcript.
*   **Required Session Fields**:
    *   Every update must preserve existing fields and update only changed fields.
    *   The following live tracking fields MUST be updated:
        ```json
        {
          "conversation_id": "string (GUID)",
          "checkpoint": "integer (1-10)",
          "status": "in_progress | completed | failed",
          "current_skill": "string",
          "current_command": "string",
          "current_step": "string (current active subtask description)",
          "current_logs": ["array of string log lines showing progressive progress"],
          "suggested_next_skill": "string | null",
          "suggested_next_command": "string | null",
          "updated_at": "string (ISO-8601 Timestamp)"
        }
        ```
*   **Context Usage Token Estimation**:
    *   Locate the main `transcript.jsonl` using the preserved `"conversation_id"` at `<appDataDir>/brain/<conversation_id>/.system_generated/logs/transcript.jsonl`.
    *   Estimate `total_tokens` as `fileSize / 3`.
    *   Update the `"context_usage"` object in `.agents/.session.json`.

---

## 13. Blueprint Mandatory Implementation Policy

This is a mandatory global policy. The following rules are absolute and cannot be bypassed:

*   **Rule 1: No Implementation Without Blueprint**: No Skill may start product/source-code implementation for a feature or bug fix unless there is a Technical Design Blueprint document. Triaging or implementing feature/fix behavior directly from brainstorming, planning, feature specifications, fix specifications, quick specifications, or user conversation text is strictly forbidden. The Technical Design Blueprint is the ONLY legal input for starting implementation.
*   **Rule 1A: Post-Implementation Command Exemption**: Post-implementation commands do not require a new Blueprint. This includes `implementation-to-debug`, `code-standard-review`, `debug-to-verify`, `implementation-to-release`, targeted test runs, validation, packaging, version bumping, changelog updates, public export, commit, tag, and push. These commands must not introduce new product behavior unless they route back through the normal Blueprint approval gate. They must validate against the approved Blueprint when one exists; otherwise they must validate against the explicit user request, reviewed Git diff, project rules, and concrete test evidence.
*   **Rule 2: Valid Blueprint Path**: A Blueprint must exist under the `docs/blueprints/` directory. Valid file paths match one of:
    - Canonical semantic feature shape: `docs/features/<feature-family>/blueprints/<WORK_ITEM_ID>_<slug>_blueprint.md` (+ `.json` when generated).
    - Canonical multi-phase folder shape: `docs/features/<feature-family>/blueprints/master/<WORK_ITEM_ID>_<slug>_master_blueprint.md` + `docs/features/<feature-family>/blueprints/phase-NN-<phase-slug>/phase-blueprint.md` (each optionally split into companion files per that phase's own indexing rules).
    - Legacy flat shape: `docs/blueprints/FEAT-XXX_slug_blueprint.md`, `docs/blueprints/FIX-XXX_slug_blueprint.md`, or `docs/blueprints/QUICK-XXX_slug_blueprint.md` may be read for backward compatibility only. New Blueprints MUST NOT use the flat shape.
*   **Rule 3: Explicit User Approval**: The Blueprint must be explicitly approved by the user through a structured selection surface. Primary path: native Agent/IDE `ask_question` with `Continue|Cancel`. Fallback path: `aiwf prompt select --question "Approve this Technical Design Blueprint for implementation?" --options "Continue|Cancel" --default "Cancel"` only when the host can render its XML bridge or pipe stdin. `PROMPT_UNAVAILABLE` means no selection happened and MUST NOT be treated as `Cancel`. Manual approval keywords such as `Y`, `Yes`, `Proceed`, or `Continue` are accepted only as fallback evidence when both native `ask_question` and runtime prompt bridge are unavailable and the Agent explicitly reports that unavailability. The AI must never assume blueprint approval.
*   **Rule 4: Stop Condition**: If a task is about starting implementation and no approved Blueprint exists, the AI must IMMEDIATELY STOP, explain the requirement, recommend generating or approving the Blueprint, and wait for input. Do not apply this stop condition to post-implementation review, debug, verification, or explicit release commands.
*   **Rule 5: Override Priority**: This policy overrides all implementation-start capable Skills. No exceptions.
*   **Rule 6: Mandatory SDLC Skill Binding**: Má»i hoáº¡t Ä‘á»™ng chá»‰nh sá»­a, thÃªm, xÃ³a tá»‡p mÃ£ nguá»“n dá»± Ã¡n báº¯t buá»™c pháº£i Ä‘Æ°á»£c thá»±c hiá»‡n trong pháº¡m vi hoáº¡t Ä‘á»™ng cá»§a má»™t SDLC Skill tÆ°Æ¡ng á»©ng (nhÆ° `quick-fix` cho sá»­a lá»—i nhanh, `quick-feature` cho tÃ­nh nÄƒng nhanh). NghiÃªm cáº¥m AI Agent tá»± Ã½ thay Ä‘á»•i file mÃ£ nguá»“n trá»±c tiáº¿p bÃªn ngoÃ i ranh giá»›i cá»§a cÃ¡c Skill nÃ y, ngay cáº£ khi tÃ i liá»‡u láº­p káº¿ hoáº¡ch `implementation_plan.md` á»Ÿ táº§ng IDE Ä‘Ã£ Ä‘Æ°á»£c duyá»‡t.
*   **Rule 7: Blueprint Quality Gate**: Before a Blueprint is approved, it must be verified that it contains a complete file-by-file analysis table (mapping absolute/relative paths, operations, and responsibilities) and a verifiable implementation checklist. Any Blueprint containing placeholders or generic instructions must be rejected and returned to the draft phase.
*   **Rule 8: Blueprint Review Evidence Gate**: Before a Blueprint is presented for approval, the Blueprint artifact itself MUST contain `Internal Review Evidence` with reviewer roles, source artifacts, checklist PASS/FAIL rows, failed-point repair history, document-compliance score, and relative-path scan result. A Blueprint without this section is not review-passed and cannot be sent to the user for approval.

---

## 14. Workflow Coordinator Auto-Routing Policy

When the user provides a natural language request without explicitly invoking a Skill (such as `/workflow`, `/brainstorm`, `/quick-fix`, `/quick-feature`, `/blueprint`, `/implement`, or `/release`), the AI must route the request through `workflow-coordinator` first instead of asking the user to run a Skill command manually.

The AI must classify the request first using the following classification rules:
- **Bug, error, regression, wrong output, broken behavior**: Route to `quick-fix` (if localized/low-risk) or `brainstorming` (if complex/broad).
- **Small feature, simple UI block, validation, filter, button, config option**: Route to `quick-feature`.
- **Large feature, new module, architecture change, multi-component work**: Route to `brainstorming`.
- **Existing approved blueprint**: Route to `blueprint-to-implementation`.
- **Debug/build/test failure after implementation**: Route to `implementation-to-debug`.
- **Verification / Final Quality Gate check**: Route to `debug-to-verify`.
- **Release, tagging, push, version bump, changelog update**: Route to `implementation-to-release` ONLY if the user explicitly requested release.

### Auto-Dispatch Behavior

When classification is clear, the AI MUST:
1. Invoke or follow `workflow-coordinator` for the current tick.
2. Persist the routing decision in workflow runtime state when runtime commands are available.
3. Immediately dispatch to the selected Skill and execute that Skill's pre-approval workflow.
4. Continue through internal review/revision loops until the Technical Design Blueprint passes review.
5. Stop absolutely at the final Blueprint Approval gate and wait for explicit user approval before implementation.

The AI MUST NOT stop merely to recommend a clear Skill, ask the user to type `/quick-feature`, `/quick-fix`, `/brainstorming`, or ask for confirmation before starting the selected workflow. A confirmation gate is allowed only when workflow selection is genuinely ambiguous or required information is missing.

When multiple workflow options are genuinely possible, output this format and STOP:
```text
I found multiple possible workflows:

Option 1:
Skill: quick-fix
Use when: this is a localized bug or small issue.
Result: creates FIX spec, then Blueprint, then waits for approval.

Option 2:
Skill: quick-feature
Use when: this is a small new feature.
Result: creates QUICK spec, then Blueprint, then waits for approval.

Option 3:
Skill: brainstorming
Use when: this may affect architecture, modules, or multiple components.
Result: starts full discovery workflow.

Please choose:
1, 2, or 3
```

The AI may use an interactive question/choice tool only for ambiguous workflow selection or missing required user information. If the tool is not supported by the client/IDE, fall back to the text format. The AI must never modify implementation code until the selected workflow reaches an approved Technical Design Blueprint.

---

## 15. Workspace Permission Mode Policy

The framework supports three workspace permission modes:
- **sandbox** (Default): Under sandbox mode, the AI must explicitly prompt for approval before any state-changing action, including writing or modifying files, modifying source code, running build/test/lint commands, updating project memory/RAG, and publishing releases.
- **full_access**: Under full_access mode, the AI is granted permission to perform normal workflow actions automatically without repeated prompts. This includes writing/updating specs, design blueprints, source code files, local database files, running builds/tests, and updating project memory/RAG.
- **unrestricted**: Under unrestricted mode, the AI is granted permission to perform ALL actions automatically (including git push, tags, release, and credentials/secrets modifications) without any prompts. 

**Two-Factor Confirmation Gate**: When selecting `unrestricted` mode during workspace initialization, the CLI must output a high-impact warning and require the user to explicitly type `CONFIRM_UNRESTRICTED` to proceed. If the confirmation fails, it must fallback to `sandbox` mode.

**Hard-Gated Operations**: Even in `full_access` mode, the AI MUST explicitly prompt for approval before executing any of the following actions (they are bypassable ONLY in `unrestricted` mode):
1. Version bump and editing CHANGELOG release sections.
2. Git commits, tags, and pushing/merging branches.
3. Destructive deletion of large files/directories.
4. Shell commands targeting directories outside the workspace.
5. Editing credential, config, or security secret settings.
6. Changing the permission mode itself.

If the permission mode is missing, invalid, or corrupted, the system must automatically fallback to `sandbox` mode.

---

## 16. Interactive CLI Prompts Bridge Policy

To streamline runtime interactions and eliminate manual keyboard input in the chat interface:
1. **Native Ask Question First**: Any workflow selection, approval, or confirmation gate MUST use the native IDE `ask_question` tool first when it is available, with explicit options such as `Continue|Cancel`, `Approve|Reject`, or the concrete workflow choices. The Agent must not author ad-hoc chat prompts like `Confirm? Y/N`, `duyet?`, or `approve?`.
2. **Prompt Select Fallback & XML Interception**: Only when native `ask_question` is unavailable or unsupported may the Agent run `workflow_runtime.py prompt select` / `aiwf prompt select`. `prompt select` emits an ask-question-first `<interactive_prompt type="ask_question">...</interactive_prompt>` XML block followed by a backward-compatible `<interactive_prompt type="select">...</interactive_prompt>` fallback. The host/Agent must parse the ask-question payload first and render it through the native Agent/IDE question UI whenever that tool exists.
3. **Tool Invocation JSON Hygiene**: The Agent must call `ask_question` through the native structured tool-call object only. It MUST NOT hand-author raw JSON strings, manually escape Unicode, paste serialized JSON into the tool input, or include unvalidated escape sequences. If a native `ask_question` call fails with `InputValidationError`, invalid JSON, truncated payload, unescaped backslash, unescaped control character, or malformed `\uXXXX` escape, the Agent MUST immediately retry through `aiwf prompt select --options "Continue|Cancel"` or the concrete option set instead of asking for a chat approval token.
4. **Piped Response**: Upon receiving the user's selection, the Agent must pipe the selected option string (or option index) directly back into the subprocess stdin.
5. **Graceful Fallback**: If `aiwf prompt select` returns `PROMPT_UNAVAILABLE`, the Agent MUST treat that as "no prompt was shown". If native `ask_question` is available, invoke it immediately. If native `ask_question`, prompt-select XML interception, and direct stdin piping are all unavailable or unsupported in the current client, the Agent may print the question as text in the chat, wait for the user to type the selection, and then pipe that input back to the subprocess stdin.

---

## 17. Environment Tools Checking and Caching Policy

To optimize execution speed, minimize token utilization, and prevent redundant shell executions, the following rules apply when verifying tools in the environment during initialization:
1. **Caching Requirement**: The AI Agent must store verified environment tool states in `.agents/runtime/env_cache.json` along with a `cached_at` ISO-8601 timestamp and the list of checked tools and their status.
2. **Cache Validation**: When verifying tools during workspace initialization (`initialize-workflow`), the AI Agent must check if `.agents/runtime/env_cache.json` exists. If it exists and the `cached_at` timestamp is within the last 24 hours, the Agent MUST skip executing shell verification commands (such as `which`, `git --version`, `docker ps`, etc.) and load the tool status directly from the cache.
3. **Cache Invalidation & Recheck**: The cache is bypassed and tools are rechecked ONLY when:
   - The cache file does not exist or is corrupted.
   - The cache age exceeds 24 hours.
   - A force recheck is requested.
   - A tool marked as "available" in the cache fails to execute during workflow stages.

---

## 18. Option Selection and Decision Making Policy

To ensure structured interactions and prevent open-ended or ambiguous confirmations when presenting choices to the user:
1. **Mandatory Native Prompting**: Whenever the AI Agent presents multiple options, choices, approval gates, or alternative paths to the user (including brainstorming directions, design alternatives, architecture options, resolving ambiguous requirements, Blueprint Approval, release approval, commit approval, tag approval, and push approval), the Agent **MUST** use native `ask_question` first when available, then `workflow_runtime.py prompt select` / `aiwf prompt select` only as a fallback so the decision remains structured and runtime-visible.
2. **Constraint on Text List**: The Agent must not simply list options in the chat text and wait for the user to type their choice while native `ask_question` or the runtime bridge is available. A structured prompt selection is mandatory.
3. **Approval Options**: Approval prompts must use explicit options, normally `Continue|Cancel` or `Approve|Reject`, with a safe default such as `Cancel` or `Reject`.
4. **Graceful Fallback**: If native `ask_question`, `prompt select`, or the IDE/client XML bridge cannot render the prompt, the Agent may fall back to presenting the options as a numbered list in the chat text, but must still treat that as fallback evidence rather than the normal path.

---

## 19. Multi-Agent Orchestration Policy

To ensure centralized decision making, task isolation, and secure parallel execution across the workspace:
1. **Orchestrator Command Primacy**: The Orchestrator is the single entry point. Every workflow execution must begin inside the Orchestrator via the `/orchestrate` command.
2. **Worker Skill Constraints**: Other workflow Skills (such as brainstorming, planning, blueprinting, implementing, etc.) act strictly as workers. Workers cannot invoke other workers, schedule parallel tasks, merge files, or own the global workflow session state.
3. **Execution Scope Isolation**: Every task scheduled by the Orchestrator must define a distinct `read_set` and a non-overlapping `write_set` in `execution-plan.json`. Workers are strictly prohibited from modifying files outside of their assigned `write_set`.
4. **File Locking Registry**: Before modifying any file, the Agent must acquire a file lock in `.agents/runtime/file-locks.json` using the `lock acquire` command. Workers must respect locks held by other tasks.
5. **No Self-Dispatch**: Agents executing worker tasks must never spawn or dispatch other agents. Only the Orchestrator owns multi-agent planning and coordination.
6. **Task Execution State**: All changes to the runtime session and parallel task statuses must be synchronized through the `workflow-runtime` CLI commands.
7. **Implementation-Only Parallel Execution**: Parallel execution is allowed ONLY during the implementation/execution phase (after an approved blueprint exists, or spec approved, and entering implementation/execution). All other workflow phases (discovery, brainstorming, planning, blueprint generation, ADR creation, memory bootstrap, memory update, RAG search, project discovery, workflow initialization, approval gates, and release) MUST remain strictly sequential.
8. **User Execution Mode Choice Timing**: The Orchestrator may never automatically choose parallel mode. The user is prompted to choose the execution mode ONLY when implementation is ready to begin. No prompts for Parallel or Sequential choice are allowed during discovery, brainstorming, planning, or blueprinting.
9. **Allowed Execution Modes**: Supported implementation modes are Parallel and Sequential. If Parallel is chosen, the Orchestrator runs concurrent workers for task groups with non-overlapping write sets. If Sequential is chosen, tasks are run one-by-one according to topological order.
10. **Choice Gate Stop**: If the user does not select a mode when prompted at the implementation start (1. Parallel, 2. Sequential, 3. Re-split, 4. Cancel), execution must stop immediately without modifying any workspace files.

---

## 20. Multi-Agent Analysis Policy

To support deep engineering research, architecture reviews, and validation while keeping workspace mutations safe:
1. **Multi-Agent Analysis Availability**: Every workflow phase (discovery, brainstorming, planning, blueprint generation, design, verification, and release) may dispatch temporary analysis agents or sub-agents for research, validation, auditing, and review purposes.
2. **Analysis-Only Scope (Read-Only)**: Analysis agents are strictly read-only. They are permitted to inspect project memory, vector RAG database, blueprints, plans, source files, configuration, logs, and git status.
3. **No Code Modification**: Analysis agents must never modify any source code files, update session or runtime state, create git commits/tags, perform releases, or edit final canonical workflow documents.
4. **Structured Recommendations**: Analysis agents return only structured recommendations and summaries. Only the owning phase agent (e.g., the planner during planning, the architect during blueprinting) is authorized to compile and output the final canonical workflow artifact (e.g., the plan, the design blueprint, the verification report).
5. **Lifespan Boundaries**: All analysis agents are temporary. Their metadata, status, and recommendations are tracked in `analysis-agents.json` and synchronized with the visualizer, and they must be automatically cleaned up upon phase completion.

---

## 21. Script-First Execution Policy

To minimize token consumption, eliminate LLM logic errors, and ensure repeatable, verifiable execution of procedural tasks:
1. **Deterministic Tasks**: All deterministic, repeatable, file-based, validation-based, and state-management actions MUST be executed by Python CLI scripts instead of natural language prompt instructions.
2. **Hybrid Tasks Separation**: For hybrid tasks (brainstorming, quick-fix, quick-feature, brainstorming-to-plan, plan-to-blueprint, ADR creation, blueprint-to-implementation), the LLM is restricted to reasoning, design, code generation, and rationale writing. The CLI script commands must handle ID allocation, path generation, YAML/markdown validation, checkpoint/session state persistence, and command execution.
3. **Structured JSON Output**: Every script-first CLI command must return structured JSON formatting on standard output.

---

## 22. Absolute Path Prohibition Policy

To prevent the leakage of user directory structures, usernames, and system details when project files and changes are pushed to remote Git repositories:
1. **No Absolute Paths**: All AI agents and CLI scripts are strictly prohibited from generating, writing, or placing absolute file paths (e.g., `/Users/username/...`, `C:\Users\username\...`, or `file:///path/to/user/...`) in any project files, documents, configuration files, prompt responses, source code, or tests.
2. **Mandatory Relative Paths**: All references to files, folders, and resources must use project-relative paths (e.g., `./skills/...`, `docs/plans/...`, or `.agents/workflow.config.json`).

3. **Canonical Public Source URL Preservation**: The intentional public AIWF
   source repository is `https://github.com/kyleit/AI-Agent-Workflow.git`.
   AI agents MUST NOT replace it with a placeholder, redact it, delete it,
   drop it from a contract, or silently substitute another repository. This
   public URL is configuration, not personal data or a policy violation.
3. **Markdown Links**: Táº¥t cáº£ cÃ¡c liÃªn káº¿t tÃ i liá»‡u Markdown trá» tá»›i tá»‡p tin hoáº·c thÆ° má»¥c Báº®T BUá»˜C pháº£i luÃ´n luÃ´n sá»­ dá»¥ng Ä‘Æ°á»ng dáº«n tÆ°Æ¡ng Ä‘á»‘i (relative paths) báº¯t Ä‘áº§u tá»« thÆ° má»¥c gá»‘c cá»§a dá»± Ã¡n (vÃ­ dá»¥: `[session.py](skills/workflow-runtime/scripts/session.py)`). Tuyá»‡t Ä‘á»‘i nghiÃªm cáº¥m viá»‡c sá»­ dá»¥ng Ä‘Æ°á»ng dáº«n tuyá»‡t Ä‘á»‘i hoáº·c Ä‘á»‹nh dáº¡ng giao thá»©c tuyá»‡t Ä‘á»‘i cá»¥c bá»™ nhÆ° `file:///e:/...` hay `file:///C:/...` trong cÃ¡c tÃ i liá»‡u.
4. **Scope of Application**: This rule applies universally to all Skills, docs, issues, plans, designs, code comments, tests, and CLI outputs.

---

## 23. Mandatory Skill Skeleton Policy

Whenever a Blueprint introduces a new AIWF Skill, it MUST generate the complete Skill skeleton including SKILL.md and all required supporting artifacts.

*   **Structure**:
    The generated Skill folder `skills/<skill-name>/` must contain at least:
    *   `SKILL.md` (containing Purpose, Public APIs, Workflow Integration, Configuration, Runtime Commands, Provider Strategy, Backward Compatibility, Usage Examples, Extension Points, Limitations).
    *   `scripts/` (containing Python CLI script or helpers).
    *   `tests/` (containing unit/integration tests for the CLI script).
*   **Validation Gate**:
    Any Blueprint that adds a new skill path under `skills/` but does not define `SKILL.md` or required directories in its write set is invalid and must fail validation.

---

## 24. Unified Knowledge Layer Policy

No AIWF Skill may access knowledge providers (such as Markdown files, SQLite databases, Qdrant vector databases, or Obsidian local REST APIs) directly. All knowledge operations (including search, read, write, and index updates) must go through the Knowledge Runtime API unless explicitly approved as a compatibility adapter.

*   **Machine-Level Global Provider Manager**:
    *   Cáº¥u hÃ¬nh thÃ´ng sá»‘ káº¿t ná»‘i vÃ  mÃ£ khÃ³a bÃ­ máº­t (`api_key`) toÃ n cá»¥c Ä‘Æ°á»£c lÆ°u trá»¯ táº¡i `~/.aiwf/providers.json` (macOS/Linux) hoáº·c `%USERPROFILE%\.aiwf\providers.json` (Windows).
    *   Cáº¥m tuyá»‡t Ä‘á»‘i lÆ°u trá»¯ hoáº·c commit mÃ£ khÃ³a báº£o máº­t (`api_key`) vÃ o tá»‡p cá»¥c bá»™ cá»§a dá»± Ã¡n. Cáº¥u hÃ¬nh dá»± Ã¡n chá»‰ chá»©a cÃ¡c thuá»™c tÃ­nh override cá»¥c bá»™ (vÃ­ dá»¥: táº¯t/báº­t provider hoáº·c thay Ä‘á»•i vault_path).
    *   Giao tiáº¿p dÃ²ng lá»‡nh CLI cá»§a `provider` Ä‘Æ°á»£c tÃ­ch há»£p qua lá»‡nh `aiwf provider` (`list`, `add`, `enable`, `disable`, `test`, `doctor`).

---

## 25. Backend Architectural & Code Quality Policy

Äá»ƒ Ä‘áº£m báº£o dá»± Ã¡n phÃ¡t triá»ƒn bá»n vá»¯ng vÃ  cháº¥t lÆ°á»£ng QA/QC Ä‘Æ°á»£c kiá»ƒm soÃ¡t cháº·t cháº½ á»Ÿ má»©c sáº£n pháº©m tháº­t (production-ready):

1. **Domain-Driven Design (DDD) & Clean Architecture**:
   * Táº¥t cáº£ mÃ£ nguá»“n backend pháº£i tuÃ¢n thá»§ nghiÃªm ngáº·t mÃ´ hÃ¬nh Clean Architecture vÃ  DDD.
   * **Domain Layer**: Chá»©a Entities, Value Objects, Domain Events vÃ  Interface. Lá»›p nÃ y khÃ´ng Ä‘Æ°á»£c phá»¥ thuá»™c vÃ o báº¥t ká»³ thÆ° viá»‡n hay framework bÃªn ngoÃ i nÃ o (nhÆ° HTTP, Web frameworks, ORMs, Database drivers, Message brokers, Cloud SDKs).
   * **Application Layer**: Chá»©a Use Cases vÃ  Ports. Logic nghiá»‡p vá»¥ á»Ÿ Ä‘Ã¢y chá»‰ phá»‘i há»£p luá»“ng hoáº¡t Ä‘á»™ng cá»§a Domain vÃ  chá»‰ phá»¥ thuá»™c vÃ o Domain abstractions.
   * **Infrastructure Layer**: Chứa Database adapters, HTTP/gRPC handlers, Wails bindings, file storage adapters.
   * Logic nghiá»‡p vá»¥ cá»‘t lÃµi khÃ´ng Ä‘Æ°á»£c phÃ©p viáº¿t trá»±c tiáº¿p trong tá»‡p giao tiáº¿p (Wails controller hoáº·c FastAPI routes).
   * **Dependency Direction Enforcement**: Chiá»u phá»¥ thuá»™c báº¯t buá»™c lÃ  Delivery -> Application -> Domain, Infrastructure -> Application/Domain Interfaces.

2. **Automated Architecture Fitness Validation**:
   * Há»‡ thá»‘ng tá»± Ä‘á»™ng quÃ©t AST (Abstract Syntax Tree) Ä‘á»ƒ phÃ¢n tÃ­ch cÃ¡c imports cá»§a Go vÃ  Python.
   * **Architecture Compliance Score**: Má»—i Work Item pháº£i cÃ³ Ä‘iá»ƒm sá»‘ kiáº¿n trÃºc tá»‘i thiá»ƒu Ä‘áº¡t **95/100**.
   * **Cáº¥m tuyá»‡t Ä‘á»‘i Critical Architecture Violations** (báº¥t ká»ƒ tá»•ng Ä‘iá»ƒm):
     * Domain phá»¥ thuá»™c vÃ o Infrastructure hoáº·c Delivery.
     * Application phá»¥ thuá»™c trá»±c tiáº¿p vÃ o concrete Infrastructure adapters.
     * Lá»›p Delivery bá» qua (bypass) Use Cases Ä‘á»ƒ thao tÃ¡c trá»±c tiáº¿p vá»›i Database/Repository.
     * CÃ³ liÃªn káº¿t phá»¥ thuá»™c vÃ²ng (circular dependency) giá»¯a cÃ¡c lá»›p lÃµi.
   * Architecture quality analysis results MUST be recorded at `docs/features/<feature-family>/verification/<WORK_ITEM>_architecture_verify.md`.

3. **Code Lines Limit**:
   * **Giá»›i háº¡n sá»‘ dÃ²ng tá»‘i Ä‘a trÃªn má»—i tá»‡p**: Má»—i tá»‡p tin mÃ£ nguá»“n backend (Go `.go`, Python `.py`) **KHÃ”NG ÄÆ¯á»¢C VÆ¯á»¢T QUÃ 500 dÃ²ng code**.
   * Náº¿u tá»‡p tin vÆ°á»£t quÃ¡ 500 dÃ²ng, báº¯t buá»™c pháº£i thá»±c hiá»‡n tÃ¡i cáº¥u trÃºc (refactoring), tÃ¡ch nhá» thÃ nh cÃ¡c module hoáº·c tá»‡p tin con riÃªng biá»‡t cÃ³ trÃ¡ch nhiá»‡m Ä‘Æ¡n nháº¥t (Single Responsibility Principle).
   * **Family-folder split rule**: When a large file is split only to satisfy the 500-line limit, the extracted sibling files MUST be grouped under one shared family-name directory and exposed through one facade/barrel/aggregate entry file. External modules MUST import/use that aggregate entry point instead of importing scattered internal split files. Splitting into many flat files directly in the parent directory is a policy violation.

4. **QA/QC Embedded Asset Guard**:
   * **Cáº¥m tuyá»‡t Ä‘á»‘i Dummy Assets khi Build**: Cáº¥m sá»­ dá»¥ng cÃ¡c tá»‡p tin giáº£ láº­p (dummy), tá»‡p tin rá»—ng (nhÆ° index.html trá»‘ng) hoáº·c tÃ i nguyÃªn thiáº¿u (missing JS/CSS) Ä‘á»ƒ vÆ°á»£t qua bÆ°á»›c biÃªn dá»‹ch.
   * **XÃ¡c thá»±c tá»± Ä‘á»™ng**: Validation pipeline pháº£i thá»±c hiá»‡n quÃ©t phÃ¢n tÃ­ch cÃ¡c thÆ° má»¥c tÃ i nguyÃªn nhÃºng (nhÆ° `frontend/dist`). Náº¿u phÃ¡t hiá»‡n chá»©a tá»‡p dummy hoáº·c kÃ­ch thÆ°á»›c quÃ¡ nhá» (< 1KB), pipeline pháº£i Ä‘Ã¡nh dáº¥u tháº¥t báº¡i ngay láº­p tá»©c (FAIL) vÃ  yÃªu cáº§u build Ä‘áº§y Ä‘á»§ frontend.
   * **Graceful Runtime Check**: Äáº£m báº£o á»©ng dá»¥ng sau khi khá»Ÿi cháº¡y pháº£i load Ä‘Æ°á»£c tÃ i nguyÃªn giao diá»‡n tháº­t thÃ´ng qua smoke tests kiá»ƒm tra ná»™i dung tráº£ vá», thay vÃ¬ chá»‰ kiá»ƒm tra cá»•ng port má»Ÿ.

---

## 26. Workspace Session Runtime Policy

*   **Session Runtime as Default**: Session Runtime is the default execution model for all workspace operations. It uses lightweight in-memory and file-based state checks via the Workflow Supervisor, without requiring long-running daemons.
*   **Resident Daemon is Optional**: The Resident Daemon (Resident Orchestrator / Runtime Manager) is optional and must never be started automatically during project initialization (`aiwf init`). It can only be started explicitly via command line (e.g., `aiwf orchestrator start --mode resident`).
*   **Forbid Manual Environment Checks**: AI agents MUST NOT manually run verification commands such as `python --version`, `go version`, `node --version`, `git --version`, `docker --version`, or similar tool validation commands.
*   **Mandatory Doctor Consumption**: All environment, capability, and stack checking operations must strictly consume the structured JSON payload returned by executing `workspace_doctor.py`.

---

## 27. Workflow First Enforcement Policy

To enforce standard software engineering processes and prevent bypasses, all operations must adhere to the Workflow First Enforcement rules:

1. **Mandatory Workflow Entry Gate**:
   Engineering requests MUST NOT be executed directly by the LLM. The first execution step MUST be `workflow_runtime.py workflow submit`.
   Skills are runtime execution units, not documentation. The AI must never ask users to manually trigger workflow skills.
   Every engineering request (including new features, bug fixes, refactoring, architecture changes, migrations, and code modifications) MUST be submitted through `workflow_runtime.py workflow submit`. Direct implementation outside Workflow Runtime is forbidden. AI must perform Intent Detection and routing first. Direct implementation is strictly prohibited.
   *Flow:* User Request -> Workflow Entry Gateway -> Intent Detection -> Workflow Supervisor -> Skill Router -> Skill Execution -> Agent Execution -> Artifacts + Evidence.

2. **Prevention of Direct Coding**:
   The AI MUST NOT directly edit source code, create implementation files, modify configurations, run build commands, or run tests before the required workflow phases are completed. Code modifications are only allowed after the design phase is approved.

3. **Mandatory Skill Lifecycle Mapping**:
   Every workflow phase must map to a registered skill:
   - Discovery -> `brainstorming`
   - Planning -> `brainstorming-to-plan`
   - Architecture -> `architecture-review`
   - Design -> `plan-to-blueprint` / `quick-feature` / `quick-fix`
   - Implementation -> `blueprint-to-implementation`
   - Debug -> `implementation-to-debug`
   - Verification -> `debug-to-verify`
   - Certification -> `vir-verify`
   - Final Review -> `final-review`
   - Release Preparation -> `release-preparation`
   - Release -> `implementation-to-release`

4. **Artifact Enforcement**:
   Every skill must generate its required artifacts under the approved semantic feature docs directories:
   - Roadmap (large/multi-phase features): `docs/features/<feature-family>/roadmaps/FEAT-xxx_slug_roadmap.md`
   - Discovery/Brainstorming: `docs/features/<feature-family>/brainstorming/FEAT-xxx_slug.md`
   - Planning: `docs/features/<feature-family>/plans/FEAT-xxx_slug_plan.md`
   - Design/Blueprint: `docs/features/<feature-family>/blueprints/FEAT-xxx_slug_blueprint.md`
   - Technical Reports: `docs/features/<feature-family>/reports/FEAT-xxx_slug_report.md`
   Creating workflow artifacts in project root is strictly forbidden. If a required artifact is missing or stored in an invalid location, the workflow status is set to `BLOCKED`.

5. **State Separation (Workspace vs. Workflow)**:
   Workspace state is decoupled from feature workflow state. Workspace state being `READY` does not mean the feature workflow is completed or released. Release decisions must depend on verified evidence.

6. **Human Approval Gates**:
   Human approval is strictly required at three strategic gates:
   - Gate 1: Workflow Selection Approval, only when workflow routing is ambiguous or multiple valid paths exist
   - Gate 2: Blueprint Approval, only after roadmap/discovery, plan/spec, and blueprint artifacts have passed internal review
   - Gate 3: Release Approval
    - Roadmap/discovery, specification, and implementation plan artifacts are reviewed internally and do not create human approval stops unless information is missing or contradictory.
    - All post-approval intermediate phases (Implementation, Debug, Verification, Certification, Final Review, Release Preparation, Post Release Validation, Monitoring, Governance) must execute autonomously when evidence passes.

7. **Session Auto-Initialization & Bootstrap Guard**:
   All workflow requests must pass through Session Bootstrap Guard. If the current session is not initialized:
   - execute initialize-workspace automatically.
   - persist initialization state.
   - continue the original request.
   Initialization must never stop workflow execution.

8. **AI Response Behavior**:
   When receiving an engineering request, the AI must first output a detection summary, then immediately continue into the selected workflow when routing is clear:
   ```text
   AIWF Workflow Detection
   Intent: [Feature Request | Bug Fix | Refactoring | Migration]
   Workflow: [feature-development | bug-fix | refactoring | migration]
   Starting Skill: [skill-name]
   ```
   Do not stop after detection for a clear request. Do not merely recommend that the user invoke a Skill. Dispatch to the selected Skill in the same turn, create and internally review the required pre-approval artifacts, and stop only at a valid strategic gate.
   Do not modify source code immediately. Pre-approval workflow artifacts may be created before Blueprint Approval when required by the selected Skill. Source code changes remain forbidden until the reviewed Blueprint has explicit approval evidence.
   User-facing output MUST use project-relative paths only and MUST NOT emit local absolute paths, drive-letter paths, or `file:///` links.

8. **Workflow Trace Requirement**:
   Every engineering request must create trace events:
   - `workflow.request.received`
   - `workflow.started`
   - `skill.selected`
   - `skill.started`
   - `artifact.created`
   - `phase.completed`
   - `workflow.completed`
   These events must be appended to `.agents/state/events/events.jsonl` (or `.agents/state/events.jsonl`).

9. **Legacy Resident Orchestrator Migration**:
   The Resident Orchestrator is deprecated. The default model is Session Runtime + Workflow Supervisor. Resident daemon mode only runs when explicitly commanded by the user.


---

## Section 28: Artifact Governance & Documentation Structure Policy

1. **Approved Documentation Storage**:
   All AIWF generated artifacts MUST be stored under approved documentation directories. Creating workflow artifacts in project root is forbidden.
   
   Approved mappings:
   - **Brainstorming**: `docs/brainstorming/`
   - **Planning**: `docs/plans/`
   - **Architecture**: `docs/architecture-reviews/`
   - **Blueprints**: `docs/blueprints/`
   - **Implementation**: `docs/implementation/`
   - **Verification**: `docs/verification/`
   - **Release**: `docs/release/`
   - **Reports**: `docs/reports/`
   - **Operations**: `docs/operations/`

   All FEAT/FIX/QUICK artifacts MUST use the semantic feature documentation contract:
   `docs/features/<feature-family>/<stage>/...`. Root-level stage files and former work-item
   folders are legacy-only and must not be created for new work.

2. **Creation Lifecycle**:
   Before creating any artifact:
   - Identify artifact type.
   - Select approved stage directory under `docs/features/<feature-family>/`.
   - Classify or create the semantic `<feature-family>` by reading artifact content and recording evidence.
   - Create or update `docs/features/<feature-family>/README.md`.
   - Validate path.
   - Create document.

3. **Supervisor Blocking**:
   Workflow Supervisor must verify artifact paths and naming before phase transitions. Any violation will set status to `BLOCKED` with reason `Artifact governance violation`.

---

## Section 29: Telegram Continuous Listener Policy

1. **Runtime-Supervised Listener**:
   Telegram runs as a worker supervised by the runtime daemon. `initialize-workflow` MUST NOT start a standalone Telegram daemon. If Telegram integration is needed and the runtime daemon is not running, start or restart the runtime daemon and let it supervise the Telegram worker.

2. **Non-blocking Execution**:
   The listener worker MUST run asynchronously inside the runtime supervisor to avoid stalling the initialization CLI or workflow sequence.

3. **Message Integration**:
   Messages received via Telegram (logged to `.agents/inbox/inbox.json`) must be processed within the active session by the running Agent, preventing duplicate parallel CLI session invocations.

4. **Project Inbox Read Allowance**:
   Agents may read `.agents/inbox/inbox.json` and non-sensitive files under `.agents/inbox/` without asking for additional workflow confirmation. This allowance is read-only, project-local, and exists only for Telegram inbox messages and user-provided input artifacts routed into the registered workspace. It does not grant permission to read credentials, secrets, `.env` files, private keys, tokens, or any file outside the registered project workspace. Host IDE or sandbox filesystem prompts still take precedence and cannot be bypassed by this policy.

5. **Bidirectional Command Execution & Messaging**:
   Báº¥t ká»³ khi nÃ o báº¯t Ä‘áº§u má»™t lÆ°á»£t lÃ m viá»‡c (Turn), Agent Báº®T BUá»˜C pháº£i kiá»ƒm tra tá»‡p tin `.agents/inbox/inbox.json`. Náº¿u cÃ³ lá»‡nh/tin nháº¯n tá»« ngÆ°á»i dÃ¹ng gá»­i Ä‘áº¿n, Agent pháº£i xá»­ lÃ½ nÃ³ nhÆ° má»™t yÃªu cáº§u hÆ°á»›ng dáº«n trá»±c tiáº¿p tá»« ngÆ°á»i dÃ¹ng. Sau khi thá»±c thi xong hoáº·c khi cháº¡m Ä‘áº¿n cÃ¡c chá»‘t phÃª duyá»‡t cáº§n dá»«ng láº¡i há»i ngÆ°á»i dÃ¹ng, Agent Báº®T BUá»˜C pháº£i gá»­i tÃ³m táº¯t hoáº¡t Ä‘á»™ng vÃ  ná»™i dung cÃ¢u há»i vá» Telegram cá»§a ngÆ°á»i dÃ¹ng qua sendMessage API (sá»­ dá»¥ng máº«u vÃ  cÃ¡c helper script trong ká»¹ nÄƒng `notify-telegram`), sau Ä‘Ã³ Ä‘áº£m báº£o runtime daemon váº«n Ä‘ang cháº¡y Ä‘á»ƒ supervisor duy trÃ¬ Telegram worker. Agent MUST NOT start a standalone Telegram daemon for this purpose.

---

## Section 30: AIWF CLI Usage & Runbook Rule

1. **Mandatory Runbook Lookup**:
   Whenever an Agent needs to use the `aiwf` CLI (or its subcommands), the Agent **MUST** first read and consult the CLI Runbook located at `.agents/runtime/aiwf-cli-runbook.md` to ensure correct syntax and available flags.

2. **No Hallucination**:
   Agents **MUST NOT** guess, invent, or hallucinate `aiwf` CLI commands. If a command or argument is not present in the runbook, it cannot be used.



---

## Section 31: Global Runtime Daemon Command Bus & Non-Blocking Schedule Waiting Policy

1. **Universal Applicability**:
   This policy applies across **ALL Skills** and **ALL Agents** without exception whenever background tasks, git operations (`git.add`, `git.commit`, `git.diff`), builds (`export.build`), test runs (`test.run`), framework updates (`framework.update`), or releases (`release.publish`) are executed.

2. **Prohibition of Direct CLI Triggers**:
   When an Agent writes a command request to `.agents/runtime/commands/runtime.request.json`, the Agent **MUST NOT** run interactive shell commands (such as `workflow_runtime runtime process` or `python -m workflow_runtime...`) via `run_command` to trigger execution. The background Runtime Daemon automatically inspects and processes requests every 1-2 seconds.

3. **Mandatory Non-Blocking Schedule Waiting Protocol**:
   - **Step 1**: Write `.agents/runtime/commands/runtime.request.json` with the target command and payload.
   - **Step 2**: Immediately invoke the `schedule` tool with a 3-second timer (`DurationSeconds="3"`, `Prompt="Check .agents/runtime/commands/runtime.response.json for completion"`).
   - **Step 3**: Remain silent and do not issue additional tool calls until the timer fires.
   - **Step 4**: Upon timer notification, inspect `.agents/runtime/commands/runtime.response.json` using `view_file` (read-only file tool, zero shell execution).

4. **Mandatory Content Payload Generation**:
   The Runtime Daemon is a dumb executor. It DOES NOT auto-generate content such as commit messages, changelogs, version numbers, or documentation. When sending any daemon command that requires content (e.g., `git.commit`), the Agent **MUST** compute the complete content (e.g., write `CHANGELOG.md` via IDE tools) and **MUST** pass the explicit content (e.g., the commit message) inside the `"args"` object of the JSON request payload.

---

## Section 32: Global Multi-Language Strict Engineering Policy

1. **3-Layer Policy Architecture**:
   All managed source files (`*.py`, `*.go`, `*.js`, `*.jsx`, `*.ts`, `*.tsx`) must adhere to a mandatory 3-Layer Policy Model:
   - **Level 1 (Core Policy)**: `.agents/policies/strict-engineering.md` â€” Enforces DDD, Clean Architecture, DIP/DI, Fail-Fast, 500-Line Limit (physical lines), and No Validator Bypass.
   - **Level 2 (Language Profiles)**: `.agents/profiles/{python,golang,typescript,javascript}.yaml` â€” Enforces toolchain gates (Pyright STRICT, `golangci-lint`, `tsc` strict, ESLint, `Import Linter`, `depguard`) and forbidden bypasses.
   - **Level 3 (Project Architecture Contract)**: `.agents/contracts/engineering-quality-gates.yaml` â€” Defines project-specific bounded contexts, layer boundaries, and dependency directions.

2. **Phase Binding**:
   - **Blueprint**: Must identify affected languages, load active language profiles, calculate file line budgets (<500 lines split strategy), define any family-folder split plan plus aggregate/facade entry file, and bind policy hashes.
   - **Implementation**: Must enforce pre-write line budgets, family-folder split shape, aggregate/facade imports, Fail-Fast dependencies, and produce zero bypasses.
   - **Debug**: Must enforce Root-Cause Debugging (no suppressing diagnostics with `# type: ignore` or `@ts-ignore`) and raise Blueprint Drift if architecture boundaries change.
   - **Verify**: Must independently enforce all active Language Profile static validators. ALL active profiles MUST PASS (no cross-language compensation).

---

## Section 33: Physical Repository Write Policy & Disk Mutation Verification Gate

1. **Working Tree as Sole Source of Truth**:
   The physical project working tree on disk (`disk = truth`) is the ONLY authoritative state of implementation. Chat output code blocks, IDE previews, proposed diffs, virtual patches, or temporary scratch buffers DO NOT count as implementation.

2. **Mandatory Write-Read-Back Loop**:
   Every source file modification must execute the 4-step sequence: `WRITE` (persist canonical project file to disk) $\rightarrow$ `READ BACK` (re-read file from disk) $\rightarrow$ `COMPARE INTENT` (verify file content matches intent) $\rightarrow$ `WORKING TREE VERIFICATION` (`git status` / `git diff`).

3. **Canonical File Ownership**:
   All writes must mutate canonical project files directly. Creating duplicate shadow files (`foo_v2.py`, `foo_copy.py`) or writing to `scratch/` or `/tmp` instead of the canonical file is STRICTLY FORBIDDEN.

4. **Independent Verification Gate**:
   The `verify` phase MUST NOT trust implementation status claims. `verify` MUST independently inspect physical files on disk and verify repository working tree state. Any discrepancy between claimed changes and disk state results in an immediate `VERIFY FAIL`.

