<!-- File path: docs/plans/FEAT-014_interactive_choice_protocol_plan.md -->

---
feature_id: FEAT-014
feature_name: Interactive Choice Protocol for AIWF
status: reviewed
stage: planning
created_at: 2026-07-07
updated_at: 2026-07-07
previous_artifact: ../brainstorming/FEAT-014_interactive_choice_protocol.md
next_artifact: ../designs/FEAT-014_interactive_choice_protocol_blueprint.md
---

# FEAT-014: Interactive Choice Protocol for AIWF

## Objective
- Introduce a structured Interactive Choice Protocol to replace manual command-line typing of choices (Y/N, numbers, or options) with graphical options like buttons in the VS Code Visualizer Extension.
- Define a protocol that works natively and asynchronously, falling back safely to text-based command-line interactions if no graphical UI capability is detected or if an interactive choice times out.

## Scope

### Included
- **Runtime CLI CLI Extension**: Extend `workflow_runtime.py` with commands (`choice create`, `choice wait`, `choice read`, and `choice clear`).
- **UI Detection and Fallback**: Detect capabilities using `.agents/runtime/ui-capabilities.json`, environment variables, or fallback to console standard input.
- **Timeout Watchdog**: Switch automatically to Text Fallback Mode if no response is written within 60 seconds.
- **Skill Refactoring**: Update all interactive prompt decision steps inside all SDLC skills.
- **Visualizer Extension Integration**: Implement FS file watching on `pending-choice.json`, render a dedicated "Workflow Actions" UI section in the sidebar, write `choice-response.json` on click, and queue incoming choices.
- **Verification Tests**: Write automated integration tests covering the protocol, timeouts, fallbacks, and Visualizer.

### Excluded
- Custom modal popups, system notifications, or confirmation dialogs outside the Sidebar panel.
- Porting visual rendering to other extensions (e.g., Cursor, Codex) in this cycle.

## Project Impact
- **Workflow CLI (`skills/workflow-runtime/`)**: High impact (new subcommands, filesystem choice handling, fallback polling loop).
- **SDLC Skills (`skills/`)**: Medium impact (calls CLI for approvals and choice paths instead of custom stdin checks).
- **Visualizer Extension (`extensions/visualizer/`)**: High impact (new panel view section, FS watch loop, message passing, response writing).
- **Workspace Documentation**: Update README, USAGE, INSTALL, and CHANGELOG.

## Dependencies
- VS Code workspace filesystem access to create, read, and delete files inside `.agents/runtime/`.
- Local Python 3.x interpreter.

## Risks
- **Race conditions**: If the file watcher fires multiple events or both extension and CLI try to write files.
  - *Mitigation*: Ensure atomic operations (temporary file renaming) and clear file states immediately after reading responses.
- **Infinite Blocking**: If the IDE crashes, the AI stays stuck.
  - *Mitigation*: Enforce a hard 60-second polling timeout before resorting to standard terminal prompts.

## Acceptance Criteria
- CLI subcommand `choice` performs file CRUD and polling validation.
- Visualizer Extension watches changes, renders Git Branch strategy, Brainstorm Options, and Approval Gate cards natively in the sidebar.
- Fallback text input functions immediately if `.agents/runtime/ui-capabilities.json` is missing or disabled.
- Standard tests pass and cover 100% of branch options, timeouts, fallback, and queue processing.

## Deliverables
- Extended CLI subcommand suite in `workflow_runtime.py`.
- Refactored Skills code templates (`SKILL.md` files).
- Updated VS Code Visualizer Extension code.
- Verification test suite covering python commands and mock file structures.
- Updated user guides and release change log.

## Estimated Complexity
- **Medium**: Involves cross-language updates (Python CLI and TypeScript extension backend/JS frontend), state queueing, and testing of asynchronous filesystem watchers.

## Recommended Blueprint Focus
- Watcher performance optimization to prevent high disk-read overhead.
- Safe serialization schema for `pending-choice.json` and `choice-response.json` to prevent parsing failures on half-written files.
- Thread-safe timeout implementation in Python.

## Recommended Next Skill
/blueprint
