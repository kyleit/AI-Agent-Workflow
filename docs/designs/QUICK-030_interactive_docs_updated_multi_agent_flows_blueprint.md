<!-- File path: docs/designs/QUICK-030_interactive_docs_updated_multi_agent_flows_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-030
workflow: quick-feature
status: draft
---
# Technical Design Blueprint - Interactive Docs Updated Multi-Agent Flows

## 1. Proposed Code Changes

### `interactive-docs/index.html`
- **Operation**: MODIFY
- **Responsibility**: Holds the static documentation content, sidebar navigation labels, workflow guide panels, overview copy, runtime guide copy, and existing Obsidian setup guide.
- **Changes**:
  - Update the `<title>` text to describe AIWF as an interactive guide for orchestrated SDLC, runtime, and multi-agent flows.
  - Update the overview welcome card to explain the current AIWF model:
    - Skill Suggestion Gate routes natural-language requests.
    - Blueprint approval is mandatory before code changes.
    - Split-state runtime stores workflow state under `.agents/state/`.
    - Knowledge Runtime is the single access layer for memory/RAG/provider knowledge.
    - Orchestrator coordinates workflow ownership and implementation scheduling.
    - Release is explicit and never automatic.
  - Update the "Nguyen tac Vang" overview list to include:
    - No Blueprint, No Code.
    - Orchestrator-first for workflow execution.
    - Analysis agents are read-only.
    - Worker agents are allowed only during implementation with non-overlapping write sets and file locks.
    - Runtime API v1 and frozen architecture are not redesigned by docs workflows.
  - Update the workflow guide intro copy for existing flow panels:
    - `#flowStandard`: describe standard full SDLC as sequential discovery, planning, blueprint, implementation, debug, verify, and explicit release.
    - `#flowFeature`: describe quick-feature as Spec -> Blueprint -> Implementation with approval gates.
    - `#flowFix`: describe quick-fix as localized bug repair with the same blueprint gate.
    - `#flowOrchestrate`: rewrite the orchestrated workflow content to explain Orchestrator primacy, read-only analysis subagents, implementation-only worker agents, execution mode choice, file locks, and release gate.
  - Update command snippets that currently imply stale behavior:
    - Memory sync snippets should use `python runtime/scripts/project_memory/cli.py update` or `python skills/workflow-runtime/scripts/workflow_runtime.py memory update`.
    - Avoid absolute local paths in all visible examples.
  - Preserve existing tab ids, button `data-tab` attributes, flow panel ids, copy button calls, and static asset references.

### `interactive-docs/docs-assets/app.js`
- **Operation**: MODIFY
- **Responsibility**: Provides client-side routing, skills search/filter, copy helper, and the interactive simulator scenarios.
- **Changes**:
  - Keep existing public browser functions and DOM expectations:
    - `initRouter()`
    - `initSkillsCatalog()`
    - `copyToClipboard(text, btnElement)`
    - `initSimulator()`
    - `simStepsData`
  - Update `tabTitleMap` strings to reflect current docs naming:
    - Overview: "Tong quan AIWF Orchestrated SDLC"
    - Workflows: "Workflow, Orchestrator va Multi-Agent Flows"
    - Runtime: "Runtime, State va Knowledge Operations"
  - Replace stale simulator content inside `simStepsData.standard` with a current sequence:
    1. Initialize workflow in sandbox mode.
    2. Synchronize project memory.
    3. Skill Suggestion Gate classifies the request.
    4. Brainstorming creates/updates `docs/brainstorming/`.
    5. Planning creates `docs/plans/`.
    6. Blueprint creates and registers `docs/designs/`.
    7. Implementation runs only after approved blueprint.
    8. Debug runs validation.
    9. Verify creates final quality gate report.
    10. Release remains explicit and approval-gated.
  - Replace stale simulator content inside `simStepsData.feature` with:
    1. Validate checkpoint 2.
    2. Create QUICK spec.
    3. User approves spec.
    4. Create/register blueprint.
    5. User approves blueprint.
    6. Implement only listed docs-site files.
    7. Verify static docs.
  - Replace stale simulator content inside `simStepsData.fix` with:
    1. Local bug classification.
    2. FIX spec.
    3. FIX blueprint.
    4. Scoped implementation.
    5. Build/test/verify.
  - Replace stale simulator content inside `simStepsData.orchestrated` with:
    1. `/orchestrate` starts the owning workflow.
    2. Orchestrator classifies scope and reads memory/RAG.
    3. Analysis agents run read-only during discovery/planning/design.
    4. Blueprint defines read sets and write sets.
    5. User chooses execution mode only at implementation start.
    6. Worker agents acquire file locks and write only assigned files.
    7. Runtime aggregates results, debug/verify gates run sequentially.
    8. Release is explicit.
  - Remove or replace visible absolute local paths in terminal output examples.
  - Preserve workflow selector values: `standard`, `feature`, `fix`, `orchestrated`.

### `interactive-docs/docs-assets/skills-data.js`
- **Operation**: MODIFY
- **Responsibility**: Defines searchable skill card data used by `initSkillsCatalog()`.
- **Changes**:
  - Update existing entries to reflect current semantics:
    - `initialize-workflow`: lightweight initialization, split-state runtime, cached state, no heavy memory/RAG scan during init.
    - `project-memory-update`: script-first incremental memory update using Git diff and Knowledge Runtime/provider delegation.
    - `brainstorming`: discovery only, no implementation.
    - `brainstorming-to-plan`: stakeholder-facing plan, no code implementation detail.
    - `plan-to-blueprint`: complete file-by-file implementation contract.
    - `blueprint-to-implementation`: code changes only from approved blueprint.
    - `implementation-to-debug`: build/lint/test and scoped self-fix loop.
    - `debug-to-verify`: final compliance and Go/No-Go quality gate.
    - `implementation-to-release`: explicit release only, version/tag/push approval required.
    - `software-development-workflow`: workflow routing/status advisor.
    - `quick-feature`: three-phase quick feature workflow.
    - `quick-fix`: three-phase localized bug workflow.
    - `orchestrator`: workflow entrypoint, schedules analysis and implementation workers under policy constraints.
    - `knowledge-runtime`: unified knowledge provider access layer.
  - Add or update card copy for current multi-agent concepts:
    - `workflow-runtime`: split-state, checkpoint, lease, lock, execution mode, analysis-agent, and state commands.
    - `vir-runtime`, `vir-investigate`, `vir-verify`, and `vir-memory-update` if present or appropriate for the current docs catalog.
  - Keep each object schema unchanged: `name`, `command`, `category`, `checkpoint`, `purpose`, `input`, `output`, `pitfall`.
  - Avoid adding fields that `app.js` does not render.

### `interactive-docs/docs-assets/style.css`
- **Operation**: OPTIONAL MODIFY
- **Responsibility**: Existing visual styling and responsive layout for the static docs site.
- **Changes**:
  - Only adjust styles if refreshed copy causes overflow or mobile wrapping defects.
  - Allowed changes are limited to existing docs-site selectors:
    - `.flow-tabs-nav`
    - `.flow-tab-btn`
    - `.step-card-detail h3`
    - `.runtime-card`
    - `.skill-card`
  - No theme redesign, no new global layout model, and no asset replacement.

## 2. Target Folder Structure

```text
.
├── docs/
│   ├── quick/
│   │   └── QUICK-030_interactive_docs_updated_multi_agent_flows.md
│   └── designs/
│       └── QUICK-030_interactive_docs_updated_multi_agent_flows_blueprint.md
└── interactive-docs/
    ├── .nojekyll
    ├── index.html
    └── docs-assets/
        ├── app.js
        ├── skills-data.js
        ├── style.css
        ├── icon.png
        ├── icon.svg
        ├── infographic.jpg
        └── screenshots/
```

## 3. Interface & Data Contracts

- **API/CLI Contracts**: No new CLI/API contracts are introduced.
- **Static DOM Contracts**:
  - Sidebar buttons keep `data-tab`.
  - Workflow buttons keep `data-flow`.
  - Flow panels keep ids used by `app.js`.
  - Simulator controls keep ids:
    - `workflowSelect`
    - `simStepTitle`
    - `simAgentAction`
    - `simCliCommand`
    - `simProgress`
    - `btnRunCli`
    - `btnApprove`
    - `btnReset`
    - `terminalBody`
- **JavaScript Data Schema**:
  - `skillsData` remains an array of plain objects:
    ```js
    {
      name: "string",
      command: "string",
      category: "string",
      checkpoint: "string",
      purpose: "string",
      input: "string",
      output: "string",
      pitfall: "string"
    }
    ```
  - `simStepsData` remains an object keyed by workflow selector value. Each step remains:
    ```js
    {
      title: "string",
      cli: "string",
      agentAction: "string",
      gate: "proceed | approval | release | none",
      gateText: "optional string",
      terminal: [
        { type: "prompt | success | warn | error | output", text: "string" }
      ]
    }
    ```

## 4. Algorithms & Key Logic

1. Preserve the existing router algorithm:
   - On sidebar click, update active menu state.
   - Hide all `.tab-content`.
   - Show the target tab by id.
   - Update the header title from `tabTitleMap`.
2. Preserve the existing skills catalog algorithm:
   - Filter by `currentFilterCategory`.
   - Filter by search match against `name`, `command`, or `purpose`.
   - Render cards from `skillsData`.
3. Preserve the existing simulator algorithm:
   - Read selected workflow key from `workflowSelect`.
   - Display current step from `simStepsData`.
   - Print terminal lines on "Chay CLI".
   - If the step has an approval or release gate, print user input `Y` after approval click.
   - Move to the next step or reset at the end.
4. Content update logic:
   - Replace old claims with current AI_RULES-aligned statements.
   - Any mention of parallel workers must say implementation phase only.
   - Any mention of release must say explicit user approval only.
   - Any mention of code modification must mention approved blueprint first.

## 5. Validation Rules

- Changed project docs and static docs files must not contain absolute local filesystem paths.
- `interactive-docs/docs-assets/app.js` must remain valid JavaScript.
- `interactive-docs/docs-assets/skills-data.js` must remain valid JavaScript and define `skillsData`.
- `interactive-docs/index.html` must keep required script tags:
  - `docs-assets/skills-data.js`
  - `docs-assets/app.js`
- Existing static assets must continue to use relative paths.
- No runtime implementation files may be modified.

## 6. Implementation Checklist

- [ ] Update `interactive-docs/index.html` overview copy.
- [ ] Update `interactive-docs/index.html` workflow panel copy and command snippets.
- [ ] Update `interactive-docs/index.html` orchestrated workflow panel with current multi-agent/subagent constraints.
- [ ] Update `interactive-docs/docs-assets/app.js` header titles.
- [ ] Update `interactive-docs/docs-assets/app.js` simulator scenario data.
- [ ] Update `interactive-docs/docs-assets/skills-data.js` skill descriptions and pitfalls.
- [ ] Adjust `interactive-docs/docs-assets/style.css` only if visual overflow appears.
- [ ] Verify no absolute local paths in changed docs-site files.
- [ ] Verify static page interactions in a browser or with a lightweight static inspection.

## 7. Verification & Test Plan

- **Acceptance Assertions**:
  - *REQ-001*: Opening `interactive-docs/index.html` shows the updated overview and existing sidebar navigation still works.
  - *REQ-002*: Workflow tabs still switch between Standard, Quick Feature, Quick Fix, and Orchestrator panels.
  - *REQ-003*: Skills search can find `/orchestrate`, `/knowledge`, `/memory-sync`, `/implement`, and `/verify`.
  - *REQ-004*: Simulator can run one complete workflow path without JavaScript exceptions.
  - *REQ-005*: `Select-String` or equivalent search finds no absolute local filesystem paths in changed static docs files.
  - *REQ-006*: Git diff shows no changes under runtime implementation code, Visualizer extension code, or provider implementation code.
  - *REQ-007*: Content states that analysis agents are read-only outside implementation and worker agents are implementation-only with scoped write sets/file locks.
  - *REQ-008*: Content states that release, tag, push, and version bumps are explicit approval-gated operations.
