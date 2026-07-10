<!-- docs/brainstorming/FEAT-014_interactive_choice_protocol.md -->

---
feature_id: FEAT-014
feature_name: Interactive Choice Protocol for AIWF
status: draft
stage: brainstorming
created_at: 2026-07-07
updated_at: 2026-07-07
previous_artifact: None
next_artifact: ../plans/FEAT-014_interactive_choice_protocol_plan.md
---

# Master Requirement Document – Interactive Choice Protocol for AIWF

## 1. Feature ID & Name
- **Feature ID**: FEAT-014
- **Feature Name**: Interactive Choice Protocol for AIWF

## 2. Original Idea
Refactor the AI Workflow Framework so that whenever a workflow requires the user to make a decision, the AI no longer asks the user to type responses in chat (Y/N, 1/2/3, A/B/C, etc.).
Instead, the AI should emit a structured Interactive Choice object that can be consumed by external IDE integrations such as the AIWF Visualizer Extension.
This feature must be IDE-independent and must work in VSCode (Codex), Antigravity IDE, Claude Code, Cursor, and future integrations.

## 3. Business Problem
- **Problem**: In graphic-oriented IDEs, typing numeric options (1, 2, 3) or confirmation commands (Y/N) in the chat is inefficient. The AI needs a way to request selections natively through the user interface.
- **Why it matters**: A graphical choice protocol (buttons, dropdowns) reduces keyboard interactions, eliminates typos, prevents invalid inputs, and improves workflow speed.
- **Who is affected**: All users interacting with the AI Engineering Workflow in supported IDEs.
- **Expected outcome**: Smooth interactive flow where the IDE renders buttons based on a pending choice JSON file, and resumes execution immediately after the user clicks a button.

## 4. Requirement Discovery
- **Functional Requirements**:
  - **FR-01 (Runtime choice files)**: Maintain choice data under `.agents/runtime/pending-choice.json` and user responses under `.agents/runtime/choice-response.json`.
  - **FR-02 (CLI Command suite)**: Extend CLI `workflow_runtime.py` with commands:
    - `choice create`: Creates `pending-choice.json`.
    - `choice wait`: Polling loop that blocks until `choice-response.json` is created or timeout occurs.
    - `choice read`: Reads the selected option ID from `choice-response.json`.
    - `choice clear`: Clears choice JSON files after consumption.
  - **FR-03 (Skill Refactoring)**: Refactor all skills to replace interactive console input prompts with the runtime choice CLI commands.
  - **FR-04 (Fallback Capability)**: Automatically fall back to text interaction in console if no IDE response is received within timeout or if UI response is not supported.
  - **FR-05 (UI Capability Detection)**: Detect if a compatible UI is available.
    - Check `.agents/runtime/ui-capabilities.json` first (e.g., `{"interactive_choice": true, "provider": "aiwf-visualizer"}`).
    - Check environment variables or IDE API integration next.
    - If no UI capability is detected, immediately use **Text Fallback Mode** (do not write pending file or wait).
  - **FR-06 (Timeout Protection)**: If interactive mode is enabled but no response is written within the configured timeout (default: 60 seconds), automatically fall back to Text Fallback Mode to prevent AI from getting stuck.
  - **FR-07 (Extension Independence)**: Choice Protocol must be an optional enhancement; the system must run cleanly in plain VSCode, CLI, Codex, Antigravity IDE, Cursor, or Claude Code.
- **Non-functional Requirements**:
  - **NFR-01 (IDE Independence)**: Must communicate solely through local filesystem files (`pending-choice.json` and `choice-response.json`) in JSON format.
  - **NFR-02 (Stateless Cleanup)**: CLI must clean up choice files on completion or failure to avoid stale state.
- **Technical Constraints**:
  - **TC-01**: Must be implemented in Python for compatibility with the existing `workflow_runtime.py`.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Where should the choice files be written? | Under `.agents/runtime/pending-choice.json` and `.agents/runtime/choice-response.json` |
| How should the polling loop behave? | Poll every 0.5s for `choice-response.json`. If no response within timeout, ask the user via console input (stdin fallback) |
| Which skills need to be refactored? | All skills requiring decisions (brainstorming, git branch, plan, blueprint, release, etc.) |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: AIWF CLI is managed by `skills/workflow-runtime/scripts/workflow_runtime.py` and session tracking.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| CLI Runtime | [workflow_runtime.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) | Needs to be extended with the `choice` subcommand suite |
| Session Handler | [session.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/session.py) | Atomically reads/writes files |
| SDLC Skills | [skills/](file:///e:/AgentsProject/skills/) | All skills needing user choice will call the CLI subcommand |
| Visualizer Backend | [extension.ts](file:///e:/AgentsProject/extensions/visualizer/src/extension.ts) | Watch `pending-choice.json`, send update messages to Webview, write `choice-response.json` on choice selection |
| Visualizer Webview | [webviewHtml.ts](file:///e:/AgentsProject/extensions/visualizer/src/webviewHtml.ts) | Render "Workflow Actions" sidebar section, choices cards, approval actions, and brainstorm solutions |

## 9. Solution Options Evaluated

### Option A: Independent Choice Files with CLI Wait Polling (Selected)
- **Overview**: Emit `pending-choice.json`, block python execution in a polling loop watching for `choice-response.json`.
- **Architecture**: CLI runs in-process, polls filesystem, falls back to raw console input on timeout or interactive mode detection.
- **Advantages**:
  - IDE independent.
  - Avoids race conditions on `.session.json`.
  - Cleans up workspace files after use.
- **Disadvantages**: Polling takes minimal CPU cycles.
- **Complexity**: Low
- **Risk**: Low
- **Performance**: High
- **Maintainability**: High
- **Compatibility**: High
- **Future Scalability**: High

### Option B: Session-embedded Choice Communication
- **Overview**: Store choice state in `.session.json` variables directly.
- **Architecture**: Extension watches `.session.json` and modifies it to respond.
- **Advantages**: Fewer files created.
- **Disadvantages**: Multi-write race conditions between CLI and IDE Extensions.

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Low | Medium |
| Risk | Low | High |
| Performance | High | High |
| Maintainability | High | Medium |
| Compatibility | High | High |
| Future Scalability | High | Medium |
| Development Cost | Low | Medium |

## 11. Selected Solution
- **Choice**: Option A — Independent Choice Files with CLI Wait Polling
- **Why Selected**: Safer concurrency model, separates ephemeral choice data from long-term session state, directly matches requirements.
- **Trade-offs Accepted**: Polling loop in python.
- **Technical Debt**: None.
- **Risk Mitigation**: Default timeouts (e.g., 5 seconds for initial UI response detection, 120 seconds overall wait) to fall back to text console inputs.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Blocking execution indefinitely if IDE doesn't respond and fallback fails. → *Mitigation*: Fallback to standard input (`input()`) if no UI file is written within a quick check interval or if polling times out.
- **Assumptions**:
  - A-01: IDE integrations can watch and write to the `.agents/runtime/` folder.

## 13. Acceptance Criteria
- [ ] Runtime CLI supports `choice create`, `choice wait`, `choice read`, and `choice clear`.
- [ ] Standard choice files exist under `.agents/runtime/` with the exact JSON protocols.
- [ ] Fallback to CLI text interaction when no UI responses are found.
- [ ] All SDLC skills (Brainstorming, Git Branch, Plans, Blueprints, Release, etc.) are refactored.
- [ ] Visualizer VS Code Extension watches `pending-choice.json`, renders "Workflow Actions" sidebar section, choices cards (Git strategy, approvals, solutions), writes `choice-response.json`, and deletes `pending-choice.json`.
- [ ] Visualizer UI closes choices automatically if files are removed or workflow completes.
- [ ] Queue support implemented in the Extension to render the oldest choice card first if multiple exist.
- [ ] Automated tests cover all choice workflows, file watching, rendering, timeouts, and fallbacks.

---

## 14. Final Planning Prompt

### Purpose
Complete, self-contained prompt for the `brainstorming-to-plan` Skill.

### Problem Statement
Introduce the Interactive Choice Protocol to replace numeric/confirmation text chats with UI button selections on external IDE integrations, specifically integrating with the AIWF Visualizer Extension.

### Objectives & Selected Solution
Implement Solution Option A using `pending-choice.json` and `choice-response.json` managed via `workflow_runtime.py choice` commands, and update the VS Code extension webview layout to render Workflow Actions.

### Functional Requirements
1. Implement `choice` subcommand suite in `workflow_runtime.py`.
2. Refactor skills to call this CLI suite.
3. Build robust fallback to standard console input.
4. Implement VS Code Extension FS watcher for `pending-choice.json` and message passing to Webview panel to render choice actions and write responses.
5. Implement queueing mechanism and auto-close behaviors in the Webview panel.
6. Implement test suite for choice protocols, python CLI, and visualizer extension integrations.

### Verification Checklist
- [ ] docs/plans/FEAT-014_interactive_choice_protocol_plan.md generated and approved
- [ ] docs/designs/FEAT-014_interactive_choice_protocol_blueprint.md generated and approved
- [ ] All Acceptance Criteria mapped to implementation tasks

---

> ⚠ The next Skill is `brainstorming-to-plan`.
> It must be invoked **manually** by the user.
> This Skill does NOT invoke it automatically.
