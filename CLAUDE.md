# CLAUDE.md

Guidelines for running and utilizing the AI Workflow Skills framework in this repository.

## Core Workflow Paradigm
The AI Workflow Framework heavily relies on the **Workflow Coordinator First Policy**.

1. **Mandatory Entry Gate**: Every user request, task, or bug fix **MUST** start by invoking the `workflow-coordinator` skill (`aiwf coordinator`). This skill evaluates intent, loads contextual state, and dispatches the correct sub-workflow (`quick-feature`, `quick-fix`, `brainstorming`, etc.).
2. **IDE Planning Mode Override**: You **MUST NOT** use your built-in IDE planning mode (e.g. creating `implementation_plan.md` directly) to execute workflows. You must route the natural language request through `workflow-coordinator` automatically.
3. **Continuous Pre-Approval Loop**: Once a workflow (like `quick-feature`) starts, do NOT stop for user approval until the **Technical Design Blueprint** is fully generated and has passed all internal compliance reviews (`document-compliance-assessment`).

## Skill Command Map
Many operations are managed via the `aiwf` CLI wrapper:

| Component/Phase | Command | Description |
| :--- | :--- | :--- |
| **Coordinator** | `aiwf coordinator` | **(START HERE)** Run workflow coordinator tick to dispatch tasks |
| **State** | `aiwf state` | Read or update workflow session state |
| **Memory** | `aiwf memory` | Query project memory index |
| **Search (RAG)** | `aiwf search` | Query RAG vector knowledge base |
| **Execution** | `aiwf execution` | Manage agent subprocess executions |
| **Doctor** | `aiwf doctor` | Run workspace/framework diagnostic checks |
| **Release** | `aiwf release` | Manage AIWF release lifecycle |

## Execution Protocol & Rules for Agents
1. **Memory-First**: Before performing any research or editing code, query the Project Memory using `aiwf memory` or the `project-rag-search` skill.
2. **Three-Stage Workflow (Quick Feature/Fix)**:
   - **Spec Phase**: Generate Mini Spec -> Internal Review.
   - **Blueprint Phase**: Generate Technical Blueprint -> Internal Review -> **Wait for Ba's approval (Blueprint Approval Gate)**.
   - **Implementation Phase**: Implement changes -> Debug & Verify -> Release.
3. **No Absolute Paths**: All links, files, and outputs must use relative paths. Absolute paths trigger immediate QA failure.
4. **Language Rule**: Maintain all technical designs, blueprints, and plans in **English**. Maintain reports and communication in **Vietnamese** (always addressing the user as **Ba**).

## Quality Gates & Verification
Before marking a skill or phase as complete, evaluate the output using the **100-Point Quality Scale** and ensure zero violations of the **15 Mandatory FAIL (NO-GO) Conditions** (documented in `skills/debug-to-verify/SKILL.md`).

## How AI Agents (Claude) Should Use Skills
This repository contains a massive framework of specialized AI Skills located in the `.agents/skills/` directory. As an AI Agent, you MUST utilize them:

1. **Skill Discovery**: Whenever you start a task, consider which specialized skills apply. You have access to dozens of skills (e.g., `frontend-design`, `quick-feature`, `project-rag-search`, `architecture-review`).
2. **Reading Skills**: If a skill seems relevant to your current task, you **MUST** read the `SKILL.md` file inside that skill's folder (e.g., `.agents/skills/frontend-design/SKILL.md`) **BEFORE** making decisions or writing code.
3. **Execution**: Once you have read the `SKILL.md` file, follow its instructions **exactly as documented**. Treat the skill's instructions as absolute constraints for your current task.
4. **Helper Scripts**: Many skills provide helper scripts (e.g., in `.agents/skills/<skill_name>/scripts/`). Use your terminal/command execution tools to run these scripts as instructed by the skill.
5. **Mandatory Skill Rules**:
   - `workflow-coordinator`: Must be used to route all incoming natural language requests.
   - `frontend-design`: Must be consulted for **ANY** task involving UI/UX, styling, or frontend components.
   - `document-compliance-assessment`: Must be used as a checklist to review generated pre-approval documents.
   - `vir-*` (Visual Intelligence Runtime): Must be used to visually verify UI implementations.
