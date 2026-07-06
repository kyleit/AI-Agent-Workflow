# AI Rules & Global Policies

This document is the single source of truth for all shared behaviors, constraints, and policies across all AI Engineering Workflow Skills. All Skills must refer to these policies to prevent duplication and ensure consistency.

---

## 1. Approval Gate Policy

The framework is strictly **approval-driven**. Before executing any state-changing action, every Skill must seek explicit confirmation.

*   **State-changing actions include**:
    *   Modifying source code or tests.
    *   Creating, deleting, or overwriting files (except Phase 1 spec/fix generation).
    *   Creating, switching, or checking out Git branches.
    *   Git merging, rebasing, committing, tagging, or pushing.
    *   Performing version bumps or modifying `CHANGELOG.md`.
*   **Procedure**:
    1.  Explain the proposed action clearly.
    2.  List all affected files (created, modified, or deleted).
    3.  List the current Git branch (if in a Git project).
    4.  Prompt the user for confirmation and **STOP**.
*   **Accepted Approval Keywords**: `Y`, `Yes`, `Proceed`, `Continue` (case-insensitive).
*   **Halt Condition**: Any other input is treated as a **STOP**. The Skill must immediately halt execution. Never assume approval.

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
    *   **Level 2**: Discovery & Specifications (`docs/brainstorming/`, `docs/issues/`, `docs/quick/`).
    *   **Level 3**: Implementation Plans (`docs/plans/`).
    *   **Level 4**: Technical Blueprints (`docs/designs/`).
    *   **Level 5**: Architectural Decision Records (`docs/adr/`).
    *   **Level 6**: Targeted source code inspection (only for files identified in Levels 1–5).
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
    | `docs/brainstorming/` | Requirements Discovery (Standard Features) | `FEAT-XXX_slug.md` |
    | `docs/plans/` | Implementation Plans | `FEAT-XXX_slug_plan.md` |
    | `docs/designs/` | Technical Blueprints | `FEAT-XXX_slug_blueprint.md` |
    | `docs/issues/` | Bug Fix Specifications (Quick-Fix) | `FIX-XXX_slug.md` |
    | `docs/quick/` | Quick Feature Specifications | `QUICK-XXX_slug.md` |
    | `docs/adr/` | Architectural Decision Records | `ADR-XXX_slug.md` |
    | `docs/debug/` | Debug and Build Diagnostics | `FEAT-XXX_debug.md` |
    | `docs/verification/` | Final Quality Gate Reports | `FEAT-XXX_verify.md` |
    | `docs/releases/` | Release Notes & Change Logs | `RELEASE-XXX_slug.md` |
    | `docs/archive/` | Historical/Retired Artifacts | As needed |
*   **Relative Paths**: All links inside documents must use relative file paths/links. Absolute paths (e.g., `file:///Users/...`) are strictly prohibited in project artifacts.
*   **Metadata**: Every document must begin with YAML frontmatter specifying its `artifact_type`, `feature_id`/`issue_id`, `workflow`, `status`, and tracking links.

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

Reliability is enforced through automated builds and testing.

*   **Verification Gates**:
    *   Before any code change is finalized, you must verify compilation and run the test suite.
    *   Always execute build commands (e.g., `npm run build`, `go build`) followed by unit/integration tests.
    *   **Debug & Verify Quality Gates**: All standard feature cycles must pass through `implementation-to-debug` (compilation, linter, tests, and error checks) followed by `debug-to-verify` (blueprint compliance, checklist verification, and Go/No-Go decision).
*   **Failure Behavior**:
    *   If building or compiling fails, or if any test fails: print stdout/stderr.
    *   **STOP** immediately. Set status to `Failed verification` and do not proceed with commit, verify, or release activities.

---

## 9. Explicit Release Policy

Release is NEVER automatic. Completion of implementation, compilation, or verification (passing all tests and quality gates) does NOT grant permission to perform release activities.

The AI must NEVER update version numbers, modify `CHANGELOG.md`, create git commits, tags, merges, pushes, or invoke the `implementation-to-release` skill unless the user has explicitly requested a Release (e.g. via keywords like `/release`, `release`, `create release`, `publish release`, `bump version`, `commit and push`, or `tag this version`). 

If no explicit release request is given by the user, the workflow MUST STOP after the Verification phase, recommend running Release, and wait for input.

*   **Release Sequence**:
    1.  **Verify Status Check**: Check `docs/verification/FEAT-XXX_verify.md` and ensure the verification status is `PASS`. If `FAIL` or missing, STOP the workflow and return to the debug phase.
    2.  **Build & Test**: Compile the codebase and run test suites to ensure 100% pass rate.
    3.  **Detect Version**: Determine the current project version.
    4.  **Update Version**: Update the version strings across project config files (requires approval).
    5.  **Update CHANGELOG**: Write release notes into `CHANGELOG.md` under a new version heading (requires approval).
    6.  **Merge (if applicable)**: Run the Release Gate; if on a non-main branch, ask whether to merge and await approval.
    7.  **Approval Gate**: Explain the final Git commit, tag, and push actions, listing all modified files and branch, then request final release approval.
    8.  **Commit**: Commit version files and `CHANGELOG.md`.
    9.  **Git Tag**: Tag the release commit as `vX.Y.Z`.
    10. **Push Branch**: Push the release branch to the remote repository.
    11. **Push Tag**: Push the tag to the remote repository.

---

## 10. Workflow Phase Separation Policy

To eliminate duplicated information, reduce token usage, and maintain clear separation of concerns, the **Planning** and **Blueprint** phases have distinct, non-overlapping responsibilities:

*   **Project Planning Phase (`docs/plans/`)**:
    *   Focusses entirely on project management, scope, deliverables, and risk mitigation.
    *   **Strict Constraints**: Planning documents must **NEVER** describe code implementations, define classes, define functions or interfaces, define database tables/schemas/SQL, define directory or folder layouts, or generate pseudo-code.
    *   The document must remain understandable by both technical and non-technical stakeholders.
*   **Technical Design Blueprint Phase (`docs/designs/`)**:
    *   Acts as the **single source of technical truth** for code changes.
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

To keep the VS Code Visualizer Dashboard synchronized in real-time, the active workflow state, step logging, and token count must be updated progressively during execution.

*   **Atomic Writing**:
    *   To prevent the VS Code extension watch engine from reading a partially-written file, all updates to `.agents/.session.json` MUST be performed atomically.
    *   First, write the complete JSON content to a temporary file: `.agents/.session.json.tmp`.
    *   Then, rename or move `.agents/.session.json.tmp` to replace `.agents/.session.json`.
*   **Progressive Updates**:
    *   Every Skill must update the session state file progressively during execution, specifically at:
        1. **Skill start**: Immediately set status to `in_progress`, current_skill, current_command, and start logging.
        2. **Each major step/checkpoint transition**: Update current_step and append log lines to current_logs.
        3. **Before running long-running/async commands** (e.g. build, test, docker): Set step/logs indicating the command is launching.
        4. **After command results**: Append output highlights, status, or errors to the logs.
        5. **On failure**: Set status to `failed` and append error logs.
        6. **On completion**: Set status to `completed` and update suggested next skill/command.
*   **Preserving Conversation ID**:
    *   The `conversation_id` MUST be created once per workflow session and saved. Do NOT regenerate or clear it on subsequent Skill calls. Always preserve the original ID.
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

## 13. Blueprint Mandatory Execution Policy

This is a mandatory global policy. The following rules are absolute and cannot be bypassed:

*   **Rule 1: No Code Modification Without Blueprint**: No Skill may create, delete, or modify source code unless there is a Technical Design Blueprint document. Triaging or implementing changes directly from brainstorming, planning, feature specifications, fix specifications, quick specifications, or user conversation text is strictly forbidden. The Technical Design Blueprint is the ONLY legal input for code generation and modification.
*   **Rule 2: Valid Blueprint Path**: A Blueprint must exist under the `docs/designs/` directory. Valid file paths must match:
    - `docs/designs/FEAT-XXX_slug_blueprint.md`
    - `docs/designs/FIX-XXX_slug_blueprint.md`
    - `docs/designs/QUICK-XXX_slug_blueprint.md`
*   **Rule 3: Explicit User Approval**: The Blueprint must be explicitly approved by the user. Accepted approval keywords are: `Y`, `Yes`, `Proceed`, `Continue` (case-insensitive). The AI must never assume blueprint approval.
*   **Rule 4: Stop Condition**: If no approved Blueprint exists, the AI must IMMEDIATELY STOP, explain the requirement, recommend generating or approving the Blueprint, and wait for input.
*   **Rule 5: Override Priority**: This policy overrides all implementation-capable Skills. No exceptions.

---

## 14. Skill Suggestion Gate Policy

When the user provides a natural language request without explicitly invoking a Skill (such as `/workflow`, `/brainstorm`, `/quick-fix`, `/quick-feature`, `/blueprint`, `/implement`, or `/release`), the AI must NOT start work immediately.

The AI must classify the request first using the following classification rules:
- **Bug, error, regression, wrong output, broken behavior**: Recommend `quick-fix` (if localized/low-risk) or `brainstorming` (if complex/broad).
- **Small feature, simple UI block, validation, filter, button, config option**: Recommend `quick-feature`.
- **Large feature, new module, architecture change, multi-component work**: Recommend `brainstorming`.
- **Existing approved blueprint**: Recommend `blueprint-to-implementation`.
- **Debug/build/test failure after implementation**: Recommend `implementation-to-debug`.
- **Verification / Final Quality Gate check**: Recommend `debug-to-verify`.
- **Release, tagging, push, version bump, changelog update**: Recommend `implementation-to-release` ONLY if the user explicitly requested release.

### Suggestion Format:

When classification is clear, output this format and STOP:
```text
I detected this as: [classification]

Recommended Skill:
[skill-name] / [command]

Reason:
[short reason]

This workflow will:
- [step 1]
- [step 2]
- [step 3]

Confirm to continue?
Y / N
```

When multiple options are possible, output this format and STOP:
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

The AI must NEVER execute the recommended Skill or modify files until the user explicitly confirms (with `Y`, `Yes`, `Proceed`, `Continue`, or the option number).



