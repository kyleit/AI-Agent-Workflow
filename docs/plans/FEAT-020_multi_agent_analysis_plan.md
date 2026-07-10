# Implementation Plan – Multi-Agent Analysis Across All Phases (FEAT-020)

This plan outlines the steps required to implement Multi-Agent Analysis across all phases of the AI Engineering Workflow Framework while maintaining strict sequential execution constraints for code modifications.

## 1. User Review Required
- **AI_RULES.md Section 17**: Adding the `Multi-Agent Analysis Policy`.
- **workflow_runtime.py Subcommand**: Adding `analysis-agent` command.
- **Visualizer Layout**: Displaying distinct sections for Analysis Agents and Implementation Agents in the webview.

## 2. Proposed Changes

### Central Policies
- [MODIFY] [AI_RULES.md](file:///Volumes/Kyle/AgentsProject/AI_RULES.md)
  - Add Section 17 (Multi-Agent Analysis Policy).

### CLI Runtime
- [MODIFY] [workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
  - Add parser, subcommand, logic for `analysis-agent` subcommand.
  - Automatically clean up `analysis-agents.json` inside `do_complete`.
  - Sync analysis agents state into `.session.json`.

### Visualizer Dashboard
- [MODIFY] [webviewHtml.ts](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/src/webviewHtml.ts)
  - Style and render Analysis Agents list.
  - Display current phase, running/completed analysis agents, active implementation agents, and execution mode.

### Interactive Docs & Simulator
- [MODIFY] [index.html](file:///Volumes/Kyle/AgentsProject/interactive-docs/index.html)
- [MODIFY] [app.js](file:///Volumes/Kyle/AgentsProject/interactive-docs/docs-assets/app.js)
  - Update simulator to support showing Analysis Agents in early steps.

### Workflow Skills
- [MODIFY] skills/brainstorming/SKILL.md
- [MODIFY] skills/brainstorming-to-plan/SKILL.md
- [MODIFY] skills/plan-to-blueprint/SKILL.md
- [MODIFY] skills/project-discovery/SKILL.md
- [MODIFY] skills/project-memory-update/SKILL.md
- [MODIFY] skills/project-memory-bootstrap/SKILL.md
- [MODIFY] skills/project-rag-search/SKILL.md
- [MODIFY] skills/implementation-to-debug/SKILL.md
- [MODIFY] skills/debug-to-verify/SKILL.md
- [MODIFY] skills/implementation-to-release/SKILL.md
  - Update instructions to mention requesting analysis agents via Orchestrator.

### Test Suite
- [MODIFY] [test_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/tests/test_runtime.py)
  - Add tests for lifecycle of temporary analysis agents and parallel execution check.

## 3. Verification Plan

### Automated Tests
- `python3 -m unittest discover -s skills/workflow-runtime/tests`

### Manual Verification
- Verify stepper visualizer rendering in `interactive-docs/index.html`.
