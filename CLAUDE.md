# CLAUDE.md

Guidelines for running and utilizing the AI Workflow Skills framework in this repository.

## Skill Command Map
Every phase or skill is run via the workflow runtime CLI:
`python skills/workflow-runtime/scripts/workflow_runtime.py <command> [options]`

| Skill/Phase | Command | Description |
| :--- | :--- | :--- |
| **Initialize** | `init` | Initialize runtime session and configure permissions |
| **Brainstorming** | `brainstorm` | Run brainstorming for requirement discovery |
| **Planning** | `plan` | Generate implementation plan from brainstorming |
| **Blueprint** | `blueprint` | Generate Technical Design Blueprint from plan |
| **Implementation**| `implement` | Apply changes based on approved blueprint |
| **Debug / Verify**| `verify` | Execute tests and run quality checks on the implementation |
| **Release** | `release` | Package releases, update memory, and push to GitLab/GitHub |
| **Memory Sync** | `memory update` | Synchronize project memory state |

## Execution Protocol & Rules for Agents
1. **Memory-First**: Before performing any research or editing code, query the Project Memory using the `project-rag-search` skill (`./.agents/skills/project-rag-search`).
2. **Three-Stage Workflow (Quick Feature/Fix)**:
   - Generate Mini Spec (`/plan`) -> Wait for Ba's approval.
   - Generate Technical Blueprint (`/blueprint`) -> Wait for Ba's approval.
   - Implement changes (`/implement`) -> Debug & Verify -> Release.
3. **No Absolute Paths**: All links, files, and outputs must use relative paths. Absolute paths trigger immediate QA failure.
4. **Language Rule**: Maintain all technical designs, blueprints, and plans in **English**. Maintain reports and communication in **Vietnamese** (always addressing the user as **Ba**).

## Quality Gates & Verification
Before marking a skill or phase as complete, evaluate the output using the **100-Point Quality Scale** and ensure zero violations of the **15 Mandatory FAIL (NO-GO) Conditions** (documented in `skills/debug-to-verify/SKILL.md`).
