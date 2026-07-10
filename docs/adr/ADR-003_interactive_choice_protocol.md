<!-- File path: docs/adr/ADR-003_interactive_choice_protocol.md -->

# ADR-003: Interactive Choice Protocol and Fallback Strategy

## Status
Accepted

## Related Feature
FEAT-014

## Context
Various checkpoints in the AI Engineering Workflow require developers to select options (e.g. Git branches, solution options, approval gates). Presenting these decisions via numeric or text prompts in the chat window is inefficient for graphical environments like VS Code (via the AIWF Visualizer Extension). The extension needs a standard protocol to detect pending decisions, render corresponding buttons or radio selectors natively, write responses back, and signal the AI to resume. Additionally, the workflow must remain compatible with text-only IDE environments (like Claude Code, Cursor, or plain CLI).

## Decision
We choose **Option A: File-Based Ephemeral Exchange with Polling and Timeout Watchdog**.
1. **Interactive Choice Files**:
   - AI outputs decision specifications to `.agents/runtime/pending-choice.json`.
   - The IDE reads this file, renders interactive elements, and writes the choice result to `.agents/runtime/choice-response.json`, deleting `pending-choice.json`.
   - The CLI blocks execution in a polling loop (every 0.5 seconds) checking for `choice-response.json`.
2. **UI Capability Detection**:
   - Check `.agents/runtime/ui-capabilities.json` for `{"interactive_choice": true}`. If false or missing, immediately fall back to text interaction without writing files.
3. **Timeout Protection**:
   - If interactive mode is enabled but no response arrives within 60 seconds, print a warning and transition to Text Fallback Mode.

## Alternatives Considered
- **Option B: Storing Choice State in `.session.json`**:
  - *Description*: Embed choices within session data blocks.
  - *Reason for Rejection*: Creating, reading, and updating the central `.session.json` from both CLI runtime and extension side concurrently introduces file-locking and write race conditions.

## Trade-offs
- **Pros**:
  - **Clean Decoupling**: Ephemeral choice variables are fully isolated from long-term session/state logs.
  - **IDE Independence**: Any external tool (scripts, CLI, VSCode) can watch and write to these two standard JSON files.
  - **Race-Condition Free**: CLI only writes the pending file and reads the response; IDE only reads the pending file and writes the response.
- **Cons**:
  - Introduces two temporary JSON files.
  - Requires a polling loop in CLI.

## Consequences
- Developers in supported graphical IDEs can interact with the workflow simply by clicking buttons on the Visualizer sidebar.
- Vanilla console environments continue to prompt users with traditional text prompts.
- All Skills templates call the central runtime choice suite uniformly.

## Risks
- **Visualizer crash / UI hang**: If the webview gets stuck, the AI might block indefinitely.
  - *Mitigation*: The 60-second CLI timeout watchdog guarantees a fallback to console standard input (`input()`).

## References
- Requirement: [FEAT-014 Requirements Specification](file:///e:/AgentsProject/docs/brainstorming/FEAT-014_interactive_choice_protocol.md)
- Plan: [FEAT-014 Scoping and Planning Plan](file:///e:/AgentsProject/docs/plans/FEAT-014_interactive_choice_protocol_plan.md)
- Design: [FEAT-014 Technical Design Blueprint](file:///e:/AgentsProject/docs/designs/FEAT-014_interactive_choice_protocol_blueprint.md)
