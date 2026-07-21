<!-- AIWF:RULES:BEGIN -->
# AI Engineering Workflow Agents

Every AI agent working inside this project **MUST** follow the AI Workflow Framework.

## Primary Workflow

Before executing any task:

1. Load and follow all policies defined in AI_RULES.md (the single source of truth).
2. Load the workflow resources from:

   * .agents/skills/
   * .agents/runtime/
   * .agents/templates/
3. Use the matching workflow Skill whenever one exists.
4. Respect runtime checkpoints and resume rules.
5. Never bypass approval gates or other framework policies.
6. Use `.agents/state/` sub-states and CLI `state` commands to inspect or restore system status.

## Global Policies

The following policies are defined in AI_RULES.md and apply to every task:

1. Approval Gate Policy
2. Git Workflow Policy
3. Memory First Policy
4. RAG Policy
5. Artifact Policy
6. Versioning Policy
7. Documentation Policy
8. Testing Policy
9. Release Policy
10. Workflow Phase Separation Policy
11. Absolute Path Prohibition Policy
12. Workflow First Enforcement Policy
13. Artifact Governance & Documentation Structure Policy

AI_RULES.md is the **single source of truth** for all shared framework behavior. If any instruction conflicts with another document, follow AI_RULES.md.

---

## Agent Catalog

The framework divides agents into **Core Phase Owners** and **Specialist Assistants**:

### 1. Core Phase Owners
- **Planner**: converts brainstorming to plans.
- **Architect**: converts plans to design blueprints.
- **Coder**: modifies codebase.
- **Reviewer**: audits code and test output.
- **Release Manager**: handles versioning and publish tasks.

### 2. Specialist Groups
- **Discovery**: Product Analyst, Business Analyst, Requirement Analyst, Research Agent, Memory Analyst, RAG Analyst.
- **Planning**: Dependency Analyst, Risk Analyst, Security Planner, Performance Planner, Test Planner.
- **Architecture**: Backend Architect, Frontend Architect, Database Architect, API Architect, Infrastructure Architect, Security Architect.
- **Implementation**: Backend Developer, Frontend Developer, Database Developer, Infrastructure Developer, DevOps Developer, Migration Developer, Documentation Writer, Test Developer.
- **Review**: Code Reviewer, QA Reviewer, Security Reviewer, Performance Reviewer, Accessibility Reviewer, Architecture Reviewer.
- **Release**: Version Manager, Release Validator, Package Builder, ChangeLog Manager, Publisher.

## Mandatory Frontend Design Skill Rule
- Any task or artifact that touches frontend design, UI/UX flow, frontend components, layout, spacing, typography, color, visual hierarchy, icons, animation, aesthetic styling, or design-system decisions **MUST** use the `frontend-design` Skill before making design or implementation decisions.
- This rule applies during brainstorming, roadmap/spec writing, planning, blueprinting, implementation, and review.
- `frontend-design` is the design authority for decisions and acceptance criteria, but it is not visual proof by itself. Any implemented UI change **MUST** pass a separate `frontend-visual-debug` evidence gate before the Agent may claim the UI is correct.
- Backend-only changes with no user-facing interface/design impact do not require `frontend-design`.

## Continuous Pre-Approval Review & Final Stop Rules
- For `quick-feature`, `quick-fix`, and the standard roadmap/discovery -> plan -> blueprint path, the Agent **MUST NOT stop for user approval** after session start, roadmap/discovery, Mini Spec, or Implementation Plan when the workflow can continue without new user information.
- Before moving from one pre-approval artifact to the next, the Agent **MUST self-review the current artifact** against the user request, active Skill, `AI_RULES.md`, traceability, relative-path rules, and `document-compliance-assessment` requirements.
- If any review FAILS, the Agent **MUST state the exact failed points**, revise only those failed points, and repeat review/revision until PASS. The Agent must not drift into unrelated changes while fixing a failed review.
- Each generated pre-approval artifact **MUST contain an `Internal Review Evidence` section** with reviewer roles, source artifacts, checklist PASS/FAIL rows, exact failed points, revision scope, re-review count, document-compliance score, and relative-path scan result. Missing evidence is an automatic FAIL and the Agent must revise the artifact before moving forward.
- The Agent may stop before Blueprint only for real blockers: ambiguous workflow selection, missing required user information, readiness below threshold, or conflicting user requirements.
- After the Technical Design Blueprint passes internal review, the Agent **MUST request Blueprint Approval through** `aiwf prompt select --question "Approve this Technical Design Blueprint for implementation?" --options "Continue|Cancel" --default "Cancel"`, then stop absolutely before implementation. A plain chat approval question is not valid unless the runtime prompt bridge is unavailable and that unavailability is explicitly reported.
- At the final Blueprint Approval gate, the Agent MUST end the turn and MUST NOT mark the Blueprint approved, inspect more files, run git, run tests, or implement code until explicit approval evidence exists.
- Blueprint Approval evidence MUST be scoped to the exact work item. The approval record, Blueprint path/filename, and Blueprint frontmatter work item id must match; stale approvals, approvals from another work item, full-access authorization, or autonomous delivery authorization MUST NOT unlock implementation.

## Semantic Feature Documentation Folder Rule
- Every new FEAT/FIX/QUICK artifact must be created under a semantic feature family folder, for example `docs/features/visualizer/blueprints/FEAT-407_visualizer_automated_test_runner_blueprint.md`.
- The feature family folder name must describe the real product/domain capability after reading the artifact content. It must not be copied from the work item ID (`FEAT-*`, `FIX-*`, `QUICK-*`) or created as one folder per ticket.
- Agents must classify the feature family using evidence from the filename, YAML frontmatter, title, first headings, summary/problem statement, and linked source artifacts. Low-confidence classification must be reported before moving files.
- Every feature family must maintain `docs/features/<feature-family>/README.md` as the cross-artifact index linking specs, plans, blueprints, debug reports, verification reports, final reports, screenshots, ADRs, and release notes.
- Do not create new flat workflow files directly under `docs/brainstorming/`, `docs/plans/`, `docs/blueprints/`, `docs/issues/`, `docs/quick/`, `docs/debug/`, `docs/verification/`, or `docs/reports/`. Existing flat files and former `docs/work-items/` folders are legacy inputs only and may be migrated by an explicit semantic documentation migration task.
- For multi-phase work, keep all phase folders inside the same semantic feature family and stage folder using `master/` and `phase-NN-<phase-slug>/`.

## Post-Implementation Automated Quality Loop
- After implementation starts from an approved Blueprint, the Agent **MUST continue automatically** through code review, targeted validation, debug/test, real runtime case testing, and final verification before reporting completion.
- Code review must use `code-standard-review` and compare every changed file against the approved Blueprint, project rules, architecture boundaries, security expectations, and scope limits.
- Validation and tests must be targeted to the changed components. `pytest` must use `pytest -v -s <related_test_file_or_directory> 2>&1 | tee .agents/runtime/tests.log`.
- A mock-only or fake-data-only result is not enough. The Agent must exercise a real runtime/user path through the affected CLI/API/IPC/database/service/browser surface, clean up any test data, and report the evidence.
- If the change affects frontend UI or browser interaction, the Agent must verify it in a real browser and capture screenshots. If IDE browser tools are unavailable, use a browser reachable through a Chrome DevTools Protocol (CDP) debug port or equivalent real browser automation.
- Opening a browser or taking a screenshot once is not enough. The Agent must compare the implemented UI against the Blueprint and `frontend-design` acceptance criteria, inspect layout/DOM, console, network, responsive breakpoints, and affected interactions, then document concrete evidence.
- A frontend review **MUST FAIL** when screenshots are missing, only static/source inspection was performed, known visual issues remain unfixed, console/network errors block the UI, text overlaps/clips, responsive layout breaks, or the implementation conflicts with explicit user/design requirements. The Agent must fix in-scope failures and rerun the visual check until PASS or a real blocker is reported.
- The final result must be written to a Markdown report under `docs/reports/`. Screenshots must be stored under `docs/reports/assets/<work-item-id>/` and linked from the report with relative paths.

## Product-Oriented Public Export Changelog Rule
- **Product-Oriented Public Export Changelog Rule**: Upon completing source code publication via `make export` (or equivalent export commands to the `public_export` directory), the Agent **MUST** create or update a dedicated `CHANGELOG.md` file specifically for the public repository located at `public_export/CHANGELOG.md`. The content of this public changelog must be written entirely from a product-oriented perspective instead of containing low-level technical git details, making it easy to comprehend for end-users, and it **MUST ONLY** document changes that are actually present in the public export codebase.

## Git Commit & Export Staging Rules
- Whenever creating a Git commit, or before pushing code, the Agent **MUST** check whether `.agents/memory/memory-state.json` or any file under `.agents/memory/` has changes. If changes exist, the Agent **MUST** run `git add` for those memory files before creating the commit so the project memory state is stored together with the source code.
- Whenever publishing or releasing, the Agent **MUST** run `git add public_export` to update the public export commit pointer in the parent repository before the release commit is finalized.
- The Agent **MUST NEVER** write local machine paths, such as `file:///absolute/path/`, `file:///e:/...`, `/Users/...`, or `/Volumes/...`, into any `CHANGELOG.md` file. This prevents leaking a developer's local filesystem structure.

## Testing & Logging Rules
- Every `pytest` run in this project **MUST** write the full test log to `.agents/runtime/tests.log` for progress tracking and debugging evidence.
- **Targeted Testing Rule**: When implementing or fixing a specific task, the Agent **MUST** run only the test files or test directories directly related to the modified components. Running the entire project test suite is forbidden unless explicitly requested or genuinely required.
- When running `pytest`, the Agent **MUST** use tee-style output so test names are visible in real time and the same output is saved to the project log:
  `pytest -v -s <related_test_file_or_directory> 2>&1 | tee .agents/runtime/tests.log`

## Environment Capability Discovery Rules
- The Agent **MUST NEVER** manually run tool or system version commands such as `python --version`, `go version`, `node --version`, `git --version`, `docker --version`, or similar commands.
- Environment and technology stack discovery **MUST** be performed by invoking and analyzing the JSON output from `skills/workflow-runtime/scripts/workspace_doctor.py`.

## IDE Planning Mode Override Rules (IDE Planning Mode Override Rules)
- Whenever the user requests code modifications, new source code additions, UI design changes, or creating/editing files, technical documents, or scripts in the project directory (including files in `extensions/` or `skills/` like `workflow-coordinator`, `brainstorming`, etc.), the Agent **MUST NOT** use the IDE's built-in Planning Mode (e.g., creating `implementation_plan.md` directly) to execute or bypass the workflow.
- The Agent **MUST** route the natural language request through `workflow-coordinator` automatically. If the workflow selection is clear, the Agent must dispatch the matching Skill (`quick-feature`, `quick-fix`, `brainstorming`, etc.) without asking the user to type that Skill command manually.
- The Agent may ask the user to choose a workflow only when the request is genuinely ambiguous or required information is missing. Once a workflow is selected, the Agent must continue through the required pre-approval review loops until the reviewed Technical Design Blueprint is ready.
- The Agent **MUST** use the runtime prompt bridge at the final Technical Design Blueprint Approval gate and wait for explicit user approval before implementation. This final approval gate must never be bypassed or replaced by an ad-hoc chat `Y/N` question.

GitHub Repository: https://github.com/kyleit/AI-Agent-Workflow
<!-- AIWF:RULES:END -->
