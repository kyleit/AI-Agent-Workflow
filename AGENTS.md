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

## Product-Oriented Public Export Changelog Rule
- **Product-Oriented Public Export Changelog Rule**: Upon completing source code publication via `make export` (or equivalent export commands to the `public_export` directory), the Agent **MUST** create or update a dedicated `CHANGELOG.md` file specifically for the public repository located at `public_export/CHANGELOG.md`. The content of this public changelog must be written entirely from a product-oriented perspective instead of containing low-level technical git details, making it easy to comprehend for end-users, and it **MUST ONLY** document changes that are actually present in the public export codebase.

## IDE Planning Mode Override Rules (IDE Planning Mode Override Rules)
- Whenever the user (Ba) requests code modifications, new source code additions, UI design changes, or creating/editing files, technical documents, or scripts in the project directory (including files in `extensions/` or `skills/` like `workflow-coordinator`, `brainstorming`, etc.), the Agent **MUST NOT** use the IDE's built-in Planning Mode (e.g., creating `implementation_plan.md` directly) to execute or bypass the workflow.
- The Agent **MUST** refuse direct implementation and instruct the user (Ba) to trigger the formal orchestration process by running the command of the corresponding skill (such as `quick-feature`, `quick-fix`, `workflow-coordinator`, `brainstorming`, etc.) to initialize a Work Item, write a Mini Spec, write a Technical Design Blueprint, or create standard architectural design documents.

GitHub Repository: https://github.com/kyleit/AI-Agent-Workflow
<!-- AIWF:RULES:END -->
