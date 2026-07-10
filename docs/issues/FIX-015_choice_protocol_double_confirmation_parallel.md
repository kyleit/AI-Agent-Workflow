---
artifact_type: fix-spec
issue_id: FIX-015
workflow: quick-fix
status: pending
---

# Fix Specification – Choice Protocol, Double Confirmation, and Parallel Execution

## 1. Issue Description
Ba reported three issues regarding the workflow:
1. When submitting raw prompts without calling a skill explicitly, the suggestion gate does not work as expected or fails to automatically route to/execute the correct skill.
2. In the Sandbox or Full Access permission modes, once the user has approved/selected an option in an interactive choice dialog, the Agent prompts them again in the chat text for confirmation, leading to duplicate confirmation loops.
3. The Orchestrator has not been seen running in parallel. Clear documentation and execution state registration are needed for parallel worker executions.

Investigation shows that:
- The `choice` subcommand is missing from `workflow_runtime.py` in the workspace, causing the `software-development-workflow` interactive suggestions prompt to fail.
- Redundant confirmation prompts occur because the Agent's global policy demands explicit confirmation for all state-changing actions even after the user has just clicked "Yes" or made a selection in the Visualizer/interactive modal.
- Parallel worker execution needs to be registered via `workflow_runtime.py task` commands during the Implementation phase to display properly on the visualizer dashboard.

## 2. Scope
- **In Scope**:
  - Implement `do_choice` with subactions `create`, `wait`, `read`, and `clear` in `workflow_runtime.py` (both root and `.agents` copies).
  - Register `choice` subcommand and arguments in `main()`.
  - Add the **No Double Confirmation Policy** to `AI_RULES.md` (both root and `.agents` copies).
  - Update SDLC skills (`quick-fix`, `quick-feature`, `blueprint-to-implementation`, `orchestrator`, `implementation-to-release`) to skip redundant chat confirmations when utilizing the choice protocol or `ask_question`.
  - Run the `test_choice.py` unit test suite to verify implementation.
- **Out of Scope**:
  - Rewriting the entire visualizer extension or modifying other subcommands of the CLI runtime.
  - Adding new GUI components to the extension sidebar.
