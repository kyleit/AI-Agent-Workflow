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
- Backend-only changes with no user-facing interface/design impact do not require `frontend-design`.

## Continuous Pre-Approval Review & Final Stop Rules
- For `quick-feature`, `quick-fix`, and the standard roadmap/discovery -> plan -> blueprint path, the Agent **MUST NOT stop for user approval** after session start, roadmap/discovery, Mini Spec, or Implementation Plan when the workflow can continue without new user information.
- Before moving from one pre-approval artifact to the next, the Agent **MUST self-review the current artifact** against the user request, active Skill, `AI_RULES.md`, traceability, relative-path rules, and `document-compliance-assessment` requirements.
- If any review FAILS, the Agent **MUST state the exact failed points**, revise only those failed points, and repeat review/revision until PASS. The Agent must not drift into unrelated changes while fixing a failed review.
- The Agent may stop before Blueprint only for real blockers: ambiguous workflow selection, missing required user information, readiness below threshold, or conflicting user requirements.
- After the Technical Design Blueprint passes internal review, the Agent **MUST stop absolutely for user approval before implementation**. At this final approval gate, the Agent MUST end the turn and MUST NOT call tools, mark the Blueprint approved, inspect more files, run git, run tests, or implement code until Ba explicitly approves.

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
- Whenever the user (Ba) requests code modifications, new source code additions, UI design changes, or creating/editing files, technical documents, or scripts in the project directory (including files in `extensions/` or `skills/` like `workflow-coordinator`, `brainstorming`, etc.), the Agent **MUST NOT** use the IDE's built-in Planning Mode (e.g., creating `implementation_plan.md` directly) to execute or bypass the workflow.
- The Agent **MUST** refuse direct implementation and instruct the user (Ba) to trigger the formal orchestration process by running the command of the corresponding skill (such as `quick-feature`, `quick-fix`, `workflow-coordinator`, `brainstorming`, etc.) to initialize a Work Item, write a Mini Spec, write a Technical Design Blueprint, or create standard architectural design documents.

GitHub Repository: https://github.com/kyleit/AI-Agent-Workflow
<!-- AIWF:RULES:END -->
